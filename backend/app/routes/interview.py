import logging
import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.interview import InterviewSession, InterviewTurn
from app.models.optimizer import AnalysisJob, AgentResult
from app.core.security import get_current_user_id
from app.graph.interview.graph import interview_graph
from app.graph.optimizer.state import CareerOSState, InterviewState

router = APIRouter(prefix="/interview", tags=["interview"])
logger = logging.getLogger("uvicorn")


class StartPayload(BaseModel):
    target_role: Optional[str] = None
    interview_mode: str = "Generic Interview"  # "Generic Interview" | "Resume-Based Interview" | "Resume + JD Interview"
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None


class AnswerPayload(BaseModel):
    answer: str


# In-memory LangGraph working state, keyed by session_id. The DB rows
# (InterviewSession/InterviewTurn) remain the durable record used for
# history and the dashboard; this dict just carries LangGraph's state
# between requests within a session's lifetime — same tradeoff v2 already
# made, now paired with DB persistence for parity with v1.
_graph_state: dict[str, dict] = {}


@router.get("/")
async def list_interviews(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    stmt = select(InterviewSession).where(InterviewSession.user_id == user_id).order_by(InterviewSession.id.desc())
    res = await db.execute(stmt)
    sessions = res.scalars().all()
    return [
        {
            "session_id": s.id,
            "domain": s.domain,
            "status": s.status,
            "overall_score": s.overall_score,
            "completed_at": s.completed_at,
        }
        for s in sessions
    ]


@router.post("/start")
async def start_interview(
    payload: StartPayload,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    resume_data = None
    resume_review = None
    ats_result = None
    jd_data = None
    jd_text = payload.jd_text
    interview_mode = payload.interview_mode

    # For Resume-Based and Resume+JD modes, load the latest optimizer job's agent results.
    if interview_mode in ("Resume-Based Interview", "Resume + JD Interview"):
        stmt = (
            select(AnalysisJob)
            .where(AnalysisJob.user_id == user_id, AnalysisJob.status == "completed")
            .order_by(AnalysisJob.completed_at.desc())
            .limit(1)
        )
        job_res = await db.execute(stmt)
        latest_job = job_res.scalars().first()

        if latest_job:
            # For Resume+JD mode, use the JD from the analysis job if not supplied by the caller.
            if not jd_text:
                jd_text = latest_job.jd_text

            stmt_agents = select(AgentResult).where(AgentResult.job_id == latest_job.id)
            agents_res = await db.execute(stmt_agents)
            agent_results = agents_res.scalars().all()

            for ar in agent_results:
                if ar.agent_name == "resume" and ar.result_json:
                    from app.graph.optimizer.state import ResumeData
                    res_json = ar.result_json
                    if isinstance(res_json, dict) and "resume_data" in res_json:
                        try:
                            resume_data = ResumeData.model_validate(res_json["resume_data"])
                        except Exception as e:
                            logger.error(f"Failed to validate resume_data: {e}")
                        resume_review = res_json.get("resume_review")
                    else:
                        try:
                            resume_data = ResumeData.model_validate(res_json)
                        except Exception as e:
                            logger.error(f"Failed to validate resume_data: {e}")
                elif ar.agent_name == "ats" and ar.result_json:
                    from app.graph.optimizer.state import ATSResult
                    try:
                        ats_result = ATSResult.model_validate(ar.result_json)
                    except Exception as e:
                        logger.error(f"Failed to validate ats_result: {e}")
                elif ar.agent_name == "jd" and ar.result_json:
                    from app.graph.optimizer.state import JDData
                    try:
                        jd_data = JDData.model_validate(ar.result_json)
                    except Exception as e:
                        logger.error(f"Failed to validate jd_data: {e}")

    initial_state = {
        "workflow_type": "interview",
        "user_goal": interview_mode,
        "target_role": payload.target_role,
        "user_id": user_id,
        "job_id": f"iv-{uuid.uuid4().hex[:8]}",
        "jd_text": jd_text,
        "resume_data": resume_data,
        "resume_review": resume_review,
        "ats_result": ats_result,
        "jd_data": jd_data,
        "interview": InterviewState(),
        "completed_agents": [],
        "errors": [],
        "status": "pending",
    }

    final_state = await asyncio.to_thread(lambda: interview_graph.invoke(initial_state))

    interview = final_state.get("interview", {})
    is_dict = isinstance(interview, dict)
    current_question = interview.get("current_question") if is_dict else interview.current_question
    transcript = interview.get("transcript", []) if is_dict else interview.transcript
    plan = interview.get("plan") if is_dict else interview.plan

    session_domain = payload.target_role or getattr(plan, "target_role", "General Software Engineering")
    session = InterviewSession(user_id=user_id, domain=session_domain, status="in_progress")
    db.add(session)
    await db.commit()
    await db.refresh(session)

    if transcript:
        db.add(InterviewTurn(session_id=session.id, turn_number=1, question=transcript[-1]["question"]))
        await db.commit()

    _graph_state[session.id] = final_state

    return {
        "session_id": session.id,
        "target_role": payload.target_role,
        "plan": plan.model_dump() if hasattr(plan, "model_dump") else plan,
        "turn_number": len(transcript),
        "question": current_question,
    }


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    payload: AnswerPayload,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    stmt = select(InterviewSession).where(
        InterviewSession.id == session_id, InterviewSession.user_id == user_id
    )
    session = (await db.execute(stmt)).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Interview is already '{session.status}'")

    prev_state = _graph_state.get(session_id)
    if not prev_state:
        raise HTTPException(status_code=410, detail="Session state expired — please start a new interview")

    interview = prev_state.get("interview", {})
    interview_dict = interview.model_dump() if isinstance(interview, InterviewState) else dict(interview)

    interview_dict["current_answer"] = payload.answer
    transcript = interview_dict.get("transcript", [])
    if transcript:
        transcript[-1] = dict(transcript[-1])
        transcript[-1]["answer"] = payload.answer
        interview_dict["transcript"] = transcript

    prev_completed = prev_state.get("completed_agents", [])
    repeating = {"interview_agent", "interview_evaluator"}
    cleaned_completed = [a for a in prev_completed if a not in repeating]

    updated_state = dict(prev_state)
    updated_state["interview"] = InterviewState(**interview_dict)
    updated_state["completed_agents"] = cleaned_completed
    updated_state["next_agent"] = None

    final_state = await asyncio.to_thread(lambda: interview_graph.invoke(updated_state))

    interview_out = final_state.get("interview", {})
    is_dict = isinstance(interview_out, dict)
    is_complete = interview_out.get("interview_complete", False) if is_dict else interview_out.interview_complete
    current_question = interview_out.get("current_question") if is_dict else interview_out.current_question
    transcript_out = interview_out.get("transcript", []) if is_dict else interview_out.transcript
    turn_number = interview_out.get("turn_number", 0) if is_dict else interview_out.turn_number

    # Persist the just-answered turn's scores.
    if transcript_out:
        last_answered = transcript_out[-1] if transcript_out[-1].get("answer") is not None else None
        if last_answered:
            turns_stmt = select(InterviewTurn).where(
                InterviewTurn.session_id == session_id,
                InterviewTurn.turn_number == last_answered["turn_number"],
            )
            db_turn = (await db.execute(turns_stmt)).scalars().first()
            if db_turn:
                db_turn.answer = last_answered.get("answer")
                db_turn.score = last_answered.get("technical_score")
                db_turn.feedback = f"Communication: {last_answered.get('communication_score')}/100"
                db_turn.answered_at = datetime.utcnow()
                await db.commit()

    _graph_state[session_id] = final_state

    report = final_state.get("report")
    if is_complete and report:
        report_data = report.model_dump() if hasattr(report, "model_dump") else report
        overall = report_data.get("interview_score") or report_data.get("overall_score") or 0

        session.status = "completed"
        session.overall_score = overall
        session.summary_json = report_data
        session.completed_at = datetime.utcnow()
        await db.commit()

        del _graph_state[session_id]

        return {"session_id": session_id, "status": "completed", "report": report_data}

    # A new question was posted — persist its open turn row if not already there.
    if current_question:
        exists_stmt = select(InterviewTurn).where(
            InterviewTurn.session_id == session_id, InterviewTurn.turn_number == turn_number
        )
        exists = (await db.execute(exists_stmt)).scalars().first()
        if not exists:
            db.add(InterviewTurn(session_id=session_id, turn_number=turn_number, question=current_question))
            await db.commit()

    return {
        "session_id": session_id,
        "status": "in_progress",
        "turn_number": turn_number,
        "question": current_question,
        "transcript": transcript_out,
    }


@router.get("/{session_id}")
async def get_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    stmt = select(InterviewSession).where(
        InterviewSession.id == session_id, InterviewSession.user_id == user_id
    )
    session = (await db.execute(stmt)).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    turns_stmt = select(InterviewTurn).where(InterviewTurn.session_id == session_id).order_by(InterviewTurn.turn_number)
    turns = (await db.execute(turns_stmt)).scalars().all()

    return {
        "session_id": session.id,
        "domain": session.domain,
        "status": session.status,
        "overall_score": session.overall_score,
        "summary": session.summary_json,
        "turns": [
            {"turn_number": t.turn_number, "question": t.question, "answer": t.answer, "score": t.score, "feedback": t.feedback}
            for t in turns
        ],
    }