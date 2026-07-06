"""LangGraph-powered interview routes (v2).

These endpoints drive the multi-agent interview workflow described in the
README:  PlannerAgent → InterviewerAgent → TechnicalEvaluator →
CommunicationAgent → DifficultyController → Orchestrator loop → CareerCoach.

The existing /interview/* endpoints (v1) use InterviewOrchestrator — a
simpler service-based loop that's already working and wired to the frontend.
These v2 endpoints sit alongside v1 under /interview/v2/* and demonstrate
the full LangGraph agent orchestration.
"""

import logging
import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user_id
from app.graph.interview_graph import interview_graph
from app.graph.state import CareerOSState, InterviewState

router = APIRouter(prefix="/interview/v2", tags=["interview-v2"])
logger = logging.getLogger("uvicorn")


class StartPayload(BaseModel):
    target_role: str
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None


class AnswerPayload(BaseModel):
    answer: str


# In-memory session store. For a production deploy you'd persist this in the
# DB or use LangGraph's built-in checkpointing, but for demonstrating the
# multi-agent flow this keeps things simple and dependency-free.
_sessions: dict[str, dict] = {}


@router.post("/start")
async def start_interview_v2(
    payload: StartPayload,
    user_id: str = Depends(get_current_user_id),
):
    """Kick off a LangGraph multi-agent interview.

    The graph runs the orchestrator which selects PlannerAgent first, then
    InterviewerAgent to generate the first question. The graph halts when
    a question is posed with no answer (the structural halt in
    route_from_interviewer). The response includes the first question.
    """
    session_id = str(uuid.uuid4())
    job_id = f"iv2-{session_id[:8]}"

    initial_state = CareerOSState(
        workflow_type="interview",
        user_goal=payload.target_role,
        user_id=user_id,
        job_id=job_id,
        jd_text=payload.jd_text,
        interview=InterviewState(),
    )

    # Run the graph — it will plan the interview, generate the first question,
    # then halt at route_from_interviewer because there's no answer yet.
    final_state = await asyncio.to_thread(
        lambda: interview_graph.invoke(initial_state)
    )

    interview = final_state.get("interview", {})
    if isinstance(interview, dict):
        current_question = interview.get("current_question")
        transcript = interview.get("transcript", [])
        plan = interview.get("plan")
    else:
        current_question = interview.current_question
        transcript = interview.transcript
        plan = interview.plan

    _sessions[session_id] = {
        "state": final_state,
        "user_id": user_id,
    }

    return {
        "session_id": session_id,
        "target_role": payload.target_role,
        "plan": plan.model_dump() if hasattr(plan, "model_dump") else plan,
        "turn_number": len(transcript),
        "question": current_question,
    }


@router.post("/{session_id}/answer")
async def submit_answer_v2(
    session_id: str,
    payload: AnswerPayload,
    user_id: str = Depends(get_current_user_id),
):
    """Submit an answer and continue the multi-agent loop.

    Injects the answer into the interview state, then re-invokes the graph.
    The orchestrator will select TechnicalEvaluator → CommunicationAgent →
    DifficultyController, then decide whether to ask another question or
    finish with the CareerCoach.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this session")

    prev_state = session["state"]

    # Get the interview state from the previous graph run
    interview = prev_state.get("interview", {})
    if isinstance(interview, InterviewState):
        interview_dict = interview.model_dump()
    elif isinstance(interview, dict):
        interview_dict = interview
    else:
        interview_dict = {}

    # Inject the candidate's answer into the state
    interview_dict["current_answer"] = payload.answer

    # Update the last transcript entry with the answer (it was None when
    # the interviewer posted the question).
    transcript = interview_dict.get("transcript", [])
    if transcript:
        transcript[-1] = dict(transcript[-1])
        transcript[-1]["answer"] = payload.answer
        interview_dict["transcript"] = transcript

    # Reset completed_agents for agents that legitimately repeat each turn
    # so the orchestrator can pick them again this round.
    prev_completed = prev_state.get("completed_agents", [])
    repeating = {"interviewer_agent", "technical_evaluator", "communication_agent", "difficulty_controller"}
    cleaned_completed = [a for a in prev_completed if a not in repeating]

    updated_state = dict(prev_state)
    updated_state["interview"] = InterviewState(**interview_dict)
    updated_state["completed_agents"] = cleaned_completed
    updated_state["next_agent"] = None

    # Re-invoke the graph — the orchestrator picks up where we left off.
    final_state = await asyncio.to_thread(
        lambda: interview_graph.invoke(updated_state)
    )

    interview_out = final_state.get("interview", {})
    if isinstance(interview_out, InterviewState):
        is_complete = interview_out.interview_complete
        current_question = interview_out.current_question
        transcript_out = interview_out.transcript
        turn_number = interview_out.turn_number
    elif isinstance(interview_out, dict):
        is_complete = interview_out.get("interview_complete", False)
        current_question = interview_out.get("current_question")
        transcript_out = interview_out.get("transcript", [])
        turn_number = interview_out.get("turn_number", 0)
    else:
        is_complete = False
        current_question = None
        transcript_out = []
        turn_number = 0

    # Persist state for the next turn
    _sessions[session_id]["state"] = final_state

    report = final_state.get("report")
    if is_complete and report:
        # Interview is done — clean up and return the career report.
        del _sessions[session_id]
        report_data = report.model_dump() if hasattr(report, "model_dump") else report
        return {
            "session_id": session_id,
            "status": "completed",
            "report": report_data,
        }

    return {
        "session_id": session_id,
        "status": "in_progress",
        "turn_number": turn_number,
        "question": current_question,
        "transcript": transcript_out,
    }


@router.get("/{session_id}")
async def get_interview_v2(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get the current state of a v2 interview session."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found or already completed")
    if session["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this session")

    interview = session["state"].get("interview", {})
    if isinstance(interview, InterviewState):
        return {
            "session_id": session_id,
            "status": "completed" if interview.interview_complete else "in_progress",
            "turn_number": interview.turn_number,
            "current_question": interview.current_question,
            "transcript": interview.transcript,
            "difficulty": interview.current_difficulty,
        }

    return {
        "session_id": session_id,
        "status": "in_progress",
        "interview": interview,
    }
