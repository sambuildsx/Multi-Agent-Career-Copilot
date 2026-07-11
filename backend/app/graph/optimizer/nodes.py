import asyncio
import logging

from app.graph.optimizer.state import CareerOSState, FinalReport, JDData
from app.agents.optimization.resume_agent import ResumeAgent
from app.agents.optimization.ats_agent import ATSAgent
from app.agents.optimization.career_coach import CareerCoachAgent

logger = logging.getLogger("uvicorn")




def ingestion_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: ingestion_node")
    res = {"status": "running"}
    logger.info("=" * 20 + f"\nOUTPUT FROM ingestion_node: \n{res}\n" + "=" * 20)
    return res


def error_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: error_node")
    res = {"status": "failed"}
    logger.info("=" * 20 + f"\nOUTPUT FROM error_node: \n{res}\n" + "=" * 20)
    return res


def fan_out_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: fan_out_node")
    res = {}
    logger.info("=" * 20 + f"\nOUTPUT FROM fan_out_node: \n{res}\n" + "=" * 20)
    return res


async def resume_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: resume_node")
    agent = ResumeAgent()
    try:
        res = await asyncio.to_thread(agent.run, state)
        logger.info("=" * 20 + f"\nOUTPUT FROM resume_node: \n{res}\n" + "=" * 20)
        return res
    except Exception as e:
        logger.error(f"[{state['job_id']}] ResumeAgent failed: {e}")
        res = {"errors": [f"ResumeAgent failed: {e}"], "completed_agents": ["resume"]}
        logger.info("=" * 20 + f"\nOUTPUT FROM resume_node: \n{res}\n" + "=" * 20)
        return res


async def jd_node(state: CareerOSState) -> dict:
    """Runs concurrently with resume_node (both fan out from fan_out_node).
    JD extraction logic lives inside ATSAgent, but is called directly here
    — not via ATSAgent.run() — so it executes in parallel with resume
    parsing instead of serially after it."""
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: jd_node")
    if not state.get("jd_text"):
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
            "no_jd": True,   # signal to routing: skip aggregator in no-JD mode
        }
    agent = ATSAgent()
    try:
        jd_data = await asyncio.to_thread(agent.extract_jd, state["jd_text"])
        res = {"jd_data": jd_data, "completed_agents": ["jd"]}
        logger.info("=" * 20 + f"\nOUTPUT FROM jd_node: \n{res}\n" + "=" * 20)
        return res
    except Exception as e:
        logger.error(f"[{state['job_id']}] JD extraction failed: {e}")
        res = {"errors": [f"JD extraction failed: {e}"], "completed_agents": ["jd"]}
        logger.info("=" * 20 + f"\nOUTPUT FROM jd_node: \n{res}\n" + "=" * 20)
        return res


async def ats_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: ats_node")
    agent = ATSAgent()
    try:
        res = await asyncio.to_thread(agent.run, state)
        logger.info("=" * 20 + f"\nOUTPUT FROM ats_node: \n{res}\n" + "=" * 20)
        return res
    except Exception as e:
        logger.error(f"[{state['job_id']}] ATSAgent failed: {e}")
        res = {"errors": [f"ATSAgent failed: {e}"], "completed_agents": ["ats"]}
        logger.info("=" * 20 + f"\nOUTPUT FROM ats_node: \n{res}\n" + "=" * 20)
        return res


def aggregator_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: aggregator_node")
    coach = CareerCoachAgent()
    ats_result = state.get("ats_result")
    has_ats = ats_result is not None

    try:
        report = coach.summarize_resume(
            resume_data=state.get("resume_data"),
            resume_review=state.get("resume_review"),
            jd_data=state.get("jd_data"),
            ats_result=ats_result,
        )

        if isinstance(report, dict):
            resume_score          = report.get("overall_score") or report.get("resume_score") or 0
            missing                = list(report.get("missing_skills") or [])
            recommendations        = list(report.get("recommendations") or [])
            markdown                = report.get("markdown") or ""
            recommendation_cards   = list(report.get("recommendation_cards") or [])
            strengths              = list(report.get("strengths") or [])
            weaknesses             = list(report.get("weaknesses") or [])
            learning_roadmap       = list(report.get("learning_roadmap") or [])
        else:
            resume_score          = getattr(report, "overall_score", None) or getattr(report, "resume_score", 0) or 0
            missing                = list(getattr(report, "missing_skills", []) or [])
            recommendations        = list(getattr(report, "recommendations", []) or [])
            markdown                = getattr(report, "markdown", "") or ""
            recommendation_cards   = list(getattr(report, "recommendation_cards", []) or [])
            strengths              = list(getattr(report, "strengths", []) or [])
            weaknesses             = list(getattr(report, "weaknesses", []) or [])
            learning_roadmap       = list(getattr(report, "learning_roadmap", []) or [])

        # Deterministic guardrail — do not trust the LLM's missing_skills output
        # in no-JD mode, regardless of what the prompt says. This is what
        # actually fixes the "Missing Requirements" section showing up in
        # Normal Optimization mode.
        if not has_ats:
            missing = []

        ats_score = ats_result.overall_score if has_ats else None
        matched_techs = list(getattr(ats_result, "matched_technologies", []) or []) if has_ats else []

        if has_ats and ats_result.missing_skills:
            existing_lower = {s.lower() for s in missing}
            for skill in ats_result.missing_skills:
                if skill.lower() not in existing_lower:
                    missing.append(skill)

    except Exception as e:
        logger.error(
            f"[{state['job_id']}] CareerCoach.summarize_resume failed: {e} — using fallback report",
            exc_info=True,
        )
        resume_score          = 0
        ats_score              = ats_result.overall_score if has_ats else None
        missing                = list(ats_result.missing_skills) if has_ats else []
        matched_techs          = list(getattr(ats_result, "matched_technologies", []) or []) if has_ats else []
        recommendations        = ["Re-run the analysis — the career coach encountered an error."]
        markdown                = "# Report\n\nThe career coach was unable to generate a full report for this analysis."
        recommendation_cards   = []
        strengths              = []
        weaknesses             = []
        learning_roadmap       = []

    final_report: FinalReport = {
        "resume_score":          resume_score,
        "ats_score":             ats_score,
        "has_jd_analysis":       has_ats,  # set by code, never by the LLM — can't drift
        "top_recommendations":   recommendations,
        "recommendations":       recommendations,   # alias the frontend reads
        "missing_skills":        missing,
        "matched_technologies":  matched_techs,
        "report_markdown":       markdown,
        "markdown":              markdown,           # alias the frontend reads
        "strengths":             strengths,
        "weaknesses":            weaknesses,
        "learning_roadmap":      learning_roadmap,
        "recommendation_cards": recommendation_cards,
    }

    res = {
        "final_report": final_report,
        "status": "completed",
    }
    logger.info("=" * 20 + f"\nOUTPUT FROM aggregator_node: \n{res}\n" + "=" * 20)
    return res