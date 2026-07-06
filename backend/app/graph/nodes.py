import asyncio
import logging

from app.graph.state import CareerOSState, FinalReport, JDData
from app.agents.resume_agent import ResumeAgent
from app.agents.jd_agent import JDAgent
from app.agents.ats_agent import ATSAgent
from app.agents.career_coach import CareerCoachAgent

logger = logging.getLogger("uvicorn")


def ingestion_node(state: CareerOSState) -> dict:
    return {"status": "running"}


def error_node(state: CareerOSState) -> dict:
    return {"status": "failed"}


def fan_out_node(state: CareerOSState) -> dict:
    return {}


async def resume_node(state: CareerOSState) -> dict:
    agent = ResumeAgent()
    # ResumeAgent does blocking file I/O + a blocking LLM call — run it off
    # the event loop so other requests aren't frozen for the duration.
    return await asyncio.to_thread(agent.run, state)


async def jd_node(state: CareerOSState) -> dict:
    if not state.jd_text:
        return {
            "jd_data": JDData(
                raw_text="",
                required_skills=[],
                preferred_skills=[],
                responsibilities=[],
                technologies=[],
                experience_level="",
                important_keywords=[],
            ),
            "completed_agents": ["jd"],
        }
    agent = JDAgent()
    return await asyncio.to_thread(agent.run, state)


async def ats_node(state: CareerOSState) -> dict:
    agent = ATSAgent()
    return await asyncio.to_thread(agent.run, state)


def aggregator_node(state: CareerOSState) -> dict:
    """Produces the final report for the resume optimization workflow.
    If we have resume data, the CareerCoach generates a real report instead of
    returning hardcoded placeholders. Falls back to a minimal report if
    something goes wrong so the pipeline never silently drops results."""

    coach = CareerCoachAgent()
    has_ats = state.ats_result is not None

    try:
        report = coach.summarize_resume(state.resume_data, state.ats_result)

        resume_score = report.overall_score or 0
        ats_score = state.ats_result.overall_score if has_ats else None
        missing = report.missing_skills or []
        recommendations = report.recommendations or []
        markdown = report.markdown or ""

        # Merge ATS missing skills into the report's list (the coach might
        # not have caught everything the deterministic ATS checker did).
        if has_ats and state.ats_result.missing_skills:
            existing_lower = {s.lower() for s in missing}
            for skill in state.ats_result.missing_skills:
                if skill.lower() not in existing_lower:
                    missing.append(skill)

    except Exception as e:
        logger.error(f"[{state.job_id}] CareerCoach.summarize_resume failed: {e} — using fallback report")
        resume_score = 0
        ats_score = state.ats_result.overall_score if has_ats else None
        missing = state.ats_result.missing_skills if has_ats else []
        recommendations = ["Re-run the analysis — the career coach encountered an error."]
        markdown = "# Report\n\nThe career coach was unable to generate a full report for this analysis."

    return {
        "final_report": FinalReport(
            resume_score=resume_score,
            ats_score=ats_score,
            top_recommendations=recommendations,
            missing_skills=missing,
            report_markdown=markdown,
        ),
        "status": "completed",
    }