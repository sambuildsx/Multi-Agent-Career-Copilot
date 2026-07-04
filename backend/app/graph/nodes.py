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


def resume_node(state: CareerOSState) -> dict:
    agent = ResumeAgent()
    return agent.run(state)


def jd_node(state: CareerOSState) -> dict:
    # Resume-only mode: nothing to parse, return an empty stub so the
    # rest of the state machine doesn't have to special-case "jd_node
    # never ran" vs "jd_node ran and found nothing."
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
    return agent.run(state)


def ats_node(state: CareerOSState) -> dict:
    agent = ATSAgent()
    return agent.run(state)


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