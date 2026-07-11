import logging
import traceback
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.models.optimizer import AnalysisJob, AgentResult, FinalReport
from app.graph.optimizer.graph import app as graph_app
from app.graph.state import CareerOSState
from app.config import settings
from app.core.security import get_current_user_id

router = APIRouter(prefix="/optimizer", tags=["optimizer"])

logger = logging.getLogger("uvicorn")


class AnalyzePayload(BaseModel):
    filename: str
    jd_text: Optional[str] = None  # None = "normal optimization" (resume-only) mode



async def run_and_save_analysis(
    job_id: str, user_id: str, resume_pdf_path: str, jd_text: Optional[str]
):
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id).values(status="running")
            )
            await session.commit()

        initial_state = {
            "job_id": job_id,
            "user_id": user_id,
            "resume_pdf_path": resume_pdf_path,
            "jd_text": jd_text,
            "status": "pending",
            "completed_agents": [],
            "errors": [],
        }

        report_saved = False

        async for state_update in graph_app.astream(initial_state):
            for node_name, fields in state_update.items():
                if not isinstance(fields, dict):
                    continue

                agent_name = None
                result_data = None

                if node_name == "resume_node" and "resume_data" in fields:
                    agent_name = "resume"
                    rd = fields["resume_data"]
                    rr = fields.get("resume_review")
                    result_data = {
                        "resume_data": rd.model_dump() if hasattr(rd, "model_dump") else (rd.dict() if hasattr(rd, "dict") else rd),
                        "resume_review": rr.model_dump() if hasattr(rr, "model_dump") else (rr.dict() if hasattr(rr, "dict") else rr) if rr else None
                    }
                elif node_name == "jd_node" and "jd_data" in fields:
                    agent_name = "jd"
                    jd = fields["jd_data"]
                    result_data = jd.model_dump() if hasattr(jd, "model_dump") else (jd.dict() if hasattr(jd, "dict") else jd)
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

                # ats_node also emits jd_data (JD extraction now lives inside
                # ATSAgent) — persist it under the same "jd" slot the
                # frontend already polls, so nothing there needs to change.
                if node_name == "ats_node" and "jd_data" in fields:
                    jd = fields["jd_data"]
                    jd_result_data = jd.model_dump() if hasattr(jd, "model_dump") else (jd.dict() if hasattr(jd, "dict") else jd)
                    async with AsyncSessionLocal() as session:
                        stmt = select(AgentResult).where(
                            AgentResult.job_id == job_id,
                            AgentResult.agent_name == "jd"
                        )
                        res = await session.execute(stmt)
                        existing = res.scalars().first()
                        if existing:
                            existing.status = "completed"
                            existing.result_json = jd_result_data
                            existing.completed_at = datetime.utcnow()
                        else:
                            session.add(AgentResult(
                                job_id=job_id,
                                agent_name="jd",
                                status="completed",
                                result_json=jd_result_data,
                                completed_at=datetime.utcnow()
                            ))
                        await session.commit()
                if "final_report" in fields:
                    if report_saved:
                        # aggregator_node fired more than once for this job (e.g. both
                        # resume_node and jd_node resolved to it in resume-only mode) —
                        # skip the duplicate write instead of hitting the unique
                        # constraint on FinalReport.job_id.
                        logger.warning(f"[{job_id}] aggregator_node fired again after report was already saved — skipping duplicate")
                        continue

                    fr = fields["final_report"]
                    report_data = fr.model_dump() if hasattr(fr, "model_dump") else (fr.dict() if hasattr(fr, "dict") else fr)
                    async with AsyncSessionLocal() as session:
                        session.add(FinalReport(
                            job_id=job_id,
                            resume_score=report_data.get("resume_score", 80),
                            ats_score=report_data.get("ats_score"),
                            report_json=report_data,
                        ))
                        await session.commit()
                    report_saved = True

        final_status = "completed" if report_saved else "failed"
        if not report_saved:
            logger.error(f"[{job_id}] graph finished but no final_report field was ever emitted")

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id)
                .values(status=final_status, completed_at=datetime.utcnow())
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
            "created_at": j.created_at,
            "completed_at": j.completed_at,
        }
        for j in jobs
    ]


@router.get("/result/{job_id}")
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


@router.get("/report/{job_id}")
async def get_job_report(job_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    stmt_job = select(AnalysisJob).where(AnalysisJob.id == job_id, AnalysisJob.user_id == user_id)
    job = (await db.execute(stmt_job)).scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    res = await db.execute(select(FinalReport).where(FinalReport.job_id == job_id))
    report = res.scalars().first()

    if not report:
        if job.status in ("pending", "running"):
            raise HTTPException(status_code=404, detail="Report not ready yet")
        raise HTTPException(status_code=404, detail=f"Job is '{job.status}' but no report was generated")

    report_data = dict(report.report_json)
    report_data["has_jd_analysis"] = bool(job.jd_text)
    
    if "matched_technologies" not in report_data:
        ats_res = await db.execute(select(AgentResult).where(AgentResult.job_id == job_id, AgentResult.agent_name == "ats"))
        ats_agent_res = ats_res.scalars().first()
        if ats_agent_res and ats_agent_res.result_json:
            report_data["matched_technologies"] = ats_agent_res.result_json.get("matched_technologies", [])
        else:
            report_data["matched_technologies"] = []

    return report_data


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