import logging
import traceback
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.models.job import AnalysisJob, AgentResult, FinalReport
from app.graph.graph import app as graph_app
from app.graph.state import CareerOSState
from app.config import settings

router = APIRouter(prefix="/jobs", tags=["jobs"])
security = HTTPBearer()

logger = logging.getLogger("uvicorn")
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"


class AnalyzePayload(BaseModel):
    filename: str
    jd_text: str
    github_repo_url: Optional[str] = None


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject claim")
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JWT decode failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired token: {type(e).__name__}")


async def run_and_save_analysis(
    job_id: str, user_id: str, resume_pdf_path: str, jd_text: str, github_repo_url: Optional[str]
):
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id).values(status="running")
            )
            await session.commit()

        initial_state = CareerOSState(
            job_id=job_id,
            user_id=user_id,
            resume_pdf_path=resume_pdf_path,
            jd_text=jd_text,
            github_repo_url=github_repo_url
        )

        async for state_update in graph_app.astream(initial_state):
            for node_name, fields in state_update.items():
                if not isinstance(fields, dict):
                    continue

                agent_name = None
                result_data = None

                if node_name == "resume_node" and "resume_data" in fields:
                    agent_name = "resume"
                    rd = fields["resume_data"]
                    result_data = rd.model_dump() if hasattr(rd, "model_dump") else (rd.dict() if hasattr(rd, "dict") else rd)
                elif node_name == "jd_node" and "jd_data" in fields:
                    agent_name = "jd"
                    jd = fields["jd_data"]
                    result_data = jd.model_dump() if hasattr(jd, "model_dump") else (jd.dict() if hasattr(jd, "dict") else jd)
                elif node_name == "github_node" and "github_data" in fields:
                    agent_name = "github"
                    gh = fields["github_data"]
                    result_data = gh.model_dump() if hasattr(gh, "model_dump") else (gh.dict() if hasattr(gh, "dict") else gh)
                elif node_name == "ats_node" and "ats_result" in fields:
                    agent_name = "ats"
                    ar = fields["ats_result"]
                    result_data = ar.model_dump() if hasattr(ar, "model_dump") else (ar.dict() if hasattr(ar, "dict") else ar)

                if agent_name and result_data is not None:
                    async with AsyncSessionLocal() as session:
                        stmt = select(AgentResult).where(
                            AgentResult.job_id == job_id,
                            AgentResult.agent_name == agent_name
                        )
                        res = await session.execute(stmt)
                        existing = res.scalars().first()
                        if existing:
                            existing.status = "completed"
                            existing.result_json = result_data
                            existing.completed_at = datetime.utcnow()
                        else:
                            session.add(AgentResult(
                                job_id=job_id,
                                agent_name=agent_name,
                                status="completed",
                                result_json=result_data,
                                completed_at=datetime.utcnow()
                            ))
                        await session.commit()

                if node_name == "aggregator_node" and "final_report" in fields:
                    fr = fields["final_report"]
                    report_data = fr.model_dump() if hasattr(fr, "model_dump") else (fr.dict() if hasattr(fr, "dict") else fr)
                    async with AsyncSessionLocal() as session:
                        session.add(FinalReport(
                            job_id=job_id,
                            resume_score=report_data.get("resume_score", 80),
                            ats_score=report_data.get("ats_score", 80),
                            github_score=report_data.get("github_score", 85),
                            report_json=report_data,
                        ))
                        await session.commit()

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id)
                .values(status="completed", completed_at=datetime.utcnow())
            )
            await session.commit()

    except Exception as e:
        logger.error(f"Error in analysis job {job_id}: {traceback.format_exc()}")
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id)
                .values(status="failed", completed_at=datetime.utcnow())
            )
            await session.commit()


@router.post("/analyze")
async def analyze(
    payload: AnalyzePayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    resume_path = f"uploads/{payload.filename}"
    job = AnalysisJob(
        user_id=user_id,
        status="pending",
        resume_path=resume_path,
        jd_text=payload.jd_text,
        github_input=payload.github_repo_url,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(
        run_and_save_analysis,
        job.id,
        user_id,
        resume_path,
        payload.jd_text,
        payload.github_repo_url
    )

    return {"job_id": job.id, "status": "pending"}


@router.get("/")
async def list_jobs(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    stmt = select(AnalysisJob).where(AnalysisJob.user_id == user_id).order_by(AnalysisJob.created_at.desc())
    res = await db.execute(stmt)
    jobs = res.scalars().all()
    return [
        {
            "job_id": j.id,
            "status": j.status,
            "resume_path": j.resume_path,
            "jd_text": (j.jd_text[:80] + "...") if j.jd_text and len(j.jd_text) > 80 else j.jd_text,
            "github_repo_url": j.github_input,
            "created_at": j.created_at,
            "completed_at": j.completed_at,
        }
        for j in jobs
    ]


@router.get("/{job_id}")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    stmt = select(AnalysisJob).where(AnalysisJob.id == job_id, AnalysisJob.user_id == user_id)
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    res_results = await db.execute(select(AgentResult).where(AgentResult.job_id == job_id))
    results = res_results.scalars().all()

    agents = {
        "resume": {"status": "pending", "data": None},
        "jd": {"status": "pending", "data": None},
        "ats": {"status": "pending", "data": None},
        "github": {"status": "pending", "data": None},
    }
    completed_agents = []
    for r in results:
        agents[r.agent_name] = {"status": r.status, "data": r.result_json, "error": r.error_msg}
        if r.status == "completed":
            completed_agents.append(r.agent_name)

    if job.status == "running":
        for a in agents:
            if agents[a]["status"] == "pending":
                agents[a]["status"] = "running"

    return {
        "job_id": job.id,
        "status": job.status,
        "completed_agents": completed_agents,
        "agents": agents,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }


@router.get("/{job_id}/report")
async def get_job_report(job_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    stmt_job = select(AnalysisJob).where(AnalysisJob.id == job_id, AnalysisJob.user_id == user_id)
    if not (await db.execute(stmt_job)).scalars().first():
        raise HTTPException(status_code=404, detail="Job not found")

    res = await db.execute(select(FinalReport).where(FinalReport.job_id == job_id))
    report = res.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not ready")
    return report.report_json


@router.delete("/{job_id}")
async def delete_job(job_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    stmt = select(AnalysisJob).where(AnalysisJob.id == job_id, AnalysisJob.user_id == user_id)
    res = await db.execute(stmt)
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    await db.commit()
    return {"message": "Job deleted successfully"}
