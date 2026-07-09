from app.graph.optimizer.state import CareerOSState
from app.agents.interview.interviewer_agent import InterviewAgent
from app.agents.interview.interview_evaluator import InterviewEvaluatorAgent
from app.agents.optimization.career_coach import CareerCoachAgent


import logging
logger = logging.getLogger("uvicorn")

def interview_agent_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: interview_agent_node")
    agent = InterviewAgent()
    res = agent.run(state)
    logger.info("=" * 20 + f"\nOUTPUT FROM interview_agent_node: \n{res}\n" + "=" * 20)
    return res


def interview_evaluator_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: interview_evaluator_node")
    agent = InterviewEvaluatorAgent()
    res = agent.run(state)
    logger.info("=" * 20 + f"\nOUTPUT FROM interview_evaluator_node: \n{res}\n" + "=" * 20)
    return res


def career_coach_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: career_coach_node")
    agent = CareerCoachAgent()
    interview = state.get("interview")
    transcript = interview.get("transcript", []) if isinstance(interview, dict) else interview.transcript
    report = agent.summarize_interview(transcript)
    if isinstance(interview, dict):
        new_interview = {**interview, "interview_complete": True}
    else:
        new_interview = interview.model_copy(update={"interview_complete": True})
    res = {"interview": new_interview, "report": report, "completed_agents": ["career_coach"]}
    logger.info("=" * 20 + f"\nOUTPUT FROM career_coach_node: \n{res}\n" + "=" * 20)
    return res