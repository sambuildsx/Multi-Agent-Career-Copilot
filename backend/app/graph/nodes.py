from app.graph.state import CareerOSState, FinalReport
from app.agents.resume_agent import ResumeAgent
from app.agents.jd_agent import JDAgent
from app.agents.github_agent import GitHubAgent
from app.agents.ats_agent import ATSAgent

def ingestion_node(state: CareerOSState) -> dict:
    # Validate inputs. Stub for now.
    return {"status": "running"}

def error_node(state: CareerOSState) -> dict:
    return {"status": "failed"}

def fan_out_node(state: CareerOSState) -> dict:
    # Dummy node to allow unconditional fan-out to parallel branches
    return {}

def resume_node(state: CareerOSState) -> dict:
    agent = ResumeAgent()
    return agent.run(state)

def jd_node(state: CareerOSState) -> dict:
    agent = JDAgent()
    return agent.run(state)

def github_node(state: CareerOSState) -> dict:
    agent = GitHubAgent()
    return agent.run(state)

def ats_node(state: CareerOSState) -> dict:
    agent = ATSAgent()
    return agent.run(state)

def aggregator_node(state: CareerOSState) -> dict:
    # Final step, combine everything. Stub for now.
    return {
        "final_report": FinalReport(
            resume_score=80,
            ats_score=80,
            github_score=85,
            top_recommendations=["Learn Docker"],
            missing_skills=["Docker"],
            report_markdown="# Final Report Stub"
        ),
        "status": "completed"
    }
