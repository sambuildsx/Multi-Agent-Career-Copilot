import logging
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.interview import InterviewSession, InterviewTurn
from app.services.interview_service import InterviewOrchestrator, ALLOWED_DOMAINS
from app.core.security import get_current_user_id

router = APIRouter(prefix="/interview", tags=["interview"])
logger = logging.getLogger("uvicorn")


class StartInterviewPayload(BaseModel):
    domain: str


class SubmitAnswerPayload(BaseModel):
    answer: str


def _build_transcript(turns: list[InterviewTurn]) -> list[dict]:
    return [
        {"question": t.question, "answer": t.answer, "score": t.score, "feedback": t.feedback}
        for t in turns
        if t.answer is not None
    ]


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
    payload: StartInterviewPayload,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if payload.domain not in ALLOWED_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Domain must be one of: {ALLOWED_DOMAINS}")

    orchestrator = InterviewOrchestrator()
    question = await asyncio.to_thread(orchestrator.generate_first_question, payload.domain)

    session = InterviewSession(user_id=user_id, domain=payload.domain, status="in_progress")
    db.add(session)
    await db.commit()
    await db.refresh(session)

    turn = InterviewTurn(session_id=session.id, turn_number=1, question=question)
    db.add(turn)
    await db.commit()

    return {
        "session_id": session.id,
        "domain": session.domain,
        "turn_number": 1,
        "question": question,
    }


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: str,
    payload: SubmitAnswerPayload,
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

    turns_stmt = select(InterviewTurn).where(InterviewTurn.session_id == session_id).order_by(InterviewTurn.turn_number)
    turns = (await db.execute(turns_stmt)).scalars().all()

    current_turn = next((t for t in reversed(turns) if t.answer is None), None)
    if not current_turn:
        raise HTTPException(status_code=400, detail="No open question awaiting an answer for this session")

    orchestrator = InterviewOrchestrator()

    evaluation = await asyncio.to_thread(
        orchestrator.evaluate_answer, session.domain, current_turn.question, payload.answer
    )

    current_turn.answer = payload.answer
    current_turn.score = evaluation.score
    current_turn.feedback = evaluation.feedback
    current_turn.answered_at = datetime.utcnow()
    await db.commit()

    transcript = _build_transcript(turns) + [{
        "question": current_turn.question,
        "answer": payload.answer,
        "score": evaluation.score,
        "feedback": evaluation.feedback,
    }]

    decision = await asyncio.to_thread(orchestrator.decide_next_step, session.domain, transcript)

    if decision.action == "end":
        summary = await asyncio.to_thread(orchestrator.summarize, session.domain, transcript)
        session.status = "completed"
        session.overall_score = summary.overall_score
        session.summary_json = summary.model_dump()
        session.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "session_id": session.id,
            "status": "completed",
            "last_evaluation": evaluation.model_dump(),
            "summary": summary.model_dump(),
        }

    next_turn = InterviewTurn(
        session_id=session_id,
        turn_number=current_turn.turn_number + 1,
        question=decision.next_question,
    )
    db.add(next_turn)
    await db.commit()

    return {
        "session_id": session.id,
        "status": "in_progress",
        "last_evaluation": evaluation.model_dump(),
        "turn_number": next_turn.turn_number,
        "question": decision.next_question,
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
            {
                "turn_number": t.turn_number,
                "question": t.question,
                "answer": t.answer,
                "score": t.score,
                "feedback": t.feedback,
            }
            for t in turns
        ],
    }