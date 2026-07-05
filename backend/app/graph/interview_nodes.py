from app.graph.state import CareerOSState
from app.agents.planner_agent import PlannerAgent
from app.agents.interviewer_agent import InterviewerAgent
from app.agents.technical_evaluator import TechnicalEvaluatorAgent
from app.agents.communication_agent import CommunicationAgent
from app.agents.career_coach import CareerCoachAgent


def planner_node(state: CareerOSState) -> dict:
    agent = PlannerAgent()
    resume_text = state.resume_data.raw_text if state.resume_data else None
    plan = agent.run(
        target_role=state.user_goal, resume_text=resume_text, jd_text=state.jd_text
    )
    new_interview = state.interview.model_copy(update={"plan": plan})
    return {"interview": new_interview, "completed_agents": ["planner_agent"]}


def interviewer_node(state: CareerOSState) -> dict:
    agent = InterviewerAgent()
    decision = agent.next_question(state.interview.plan, state.interview.transcript)

    new_turn = {
        "turn_number": state.interview.turn_number + 1,
        "topic": decision.topic,
        "difficulty": decision.difficulty,
        "is_followup": decision.is_followup,
        "question": decision.question,
        "answer": None,
        "technical_score": None,
        "communication_score": None,
    }
    new_interview = state.interview.model_copy(update={
        "transcript": state.interview.transcript + [new_turn],
        "turn_number": state.interview.turn_number + 1,
        "current_topic": decision.topic,
        "current_question": decision.question,
        "current_answer": None,
    })
    return {"interview": new_interview, "completed_agents": ["interviewer_agent"]}


def technical_evaluator_node(state: CareerOSState) -> dict:
    agent = TechnicalEvaluatorAgent()
    last_turn = dict(state.interview.transcript[-1])
    evaluation = agent.evaluate(last_turn["topic"], last_turn["question"], state.interview.current_answer)

    last_turn["answer"] = state.interview.current_answer
    last_turn["technical_score"] = evaluation.score

    updated_transcript = state.interview.transcript[:-1] + [last_turn]
    new_interview = state.interview.model_copy(update={
        "transcript": updated_transcript,
        "technical_scores": state.interview.technical_scores + [evaluation],
    })
    return {"interview": new_interview, "completed_agents": ["technical_evaluator"]}


def communication_agent_node(state: CareerOSState) -> dict:
    agent = CommunicationAgent()
    last_turn = dict(state.interview.transcript[-1])
    evaluation = agent.evaluate(last_turn["question"], last_turn["answer"])

    last_turn["communication_score"] = evaluation.confidence

    updated_transcript = state.interview.transcript[:-1] + [last_turn]
    new_interview = state.interview.model_copy(update={
        "transcript": updated_transcript,
        "communication_scores": state.interview.communication_scores + [evaluation],
    })
    return {"interview": new_interview, "completed_agents": ["communication_agent"]}


def career_coach_node(state: CareerOSState) -> dict:
    agent = CareerCoachAgent()
    report = agent.summarize_interview(state.interview.transcript)
    new_interview = state.interview.model_copy(update={"interview_complete": True})
    return {"interview": new_interview, "report": report, "completed_agents": ["career_coach"]}