import asyncio
from app.graph.state import CareerOSState, FinalReport, JDData
from app.agents.resume_agent import ResumeAgent
from app.agents.jd_agent import JDAgent
from app.agents.ats_agent import ATSAgent


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
    has_ats = state.ats_result is not None
    return {
        "final_report": FinalReport(
            resume_score=80,  # TODO: pull from real resume_data once ResumeAgent scoring lands
            ats_score=(state.ats_result.overall_score if has_ats else None),
            top_recommendations=["Learn Docker"],
            missing_skills=["Docker"],
            report_markdown="# Final Report Stub",
        ),
        "status": "completed",
    }