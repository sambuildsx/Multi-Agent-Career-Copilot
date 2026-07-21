import logging
from langgraph.graph import StateGraph, START, END
from app.graph.optimizer.state import CareerOSState
from app.graph.interview.nodes import (
    interview_agent_node, interview_evaluator_node, career_coach_node,
)

logger = logging.getLogger("uvicorn")


def route_from_interview_agent(state: CareerOSState) -> str:
    logger.info("Entering route_from_interview_agent")
    interview = state.get("interview", {})
    is_dict = isinstance(interview, dict)
    is_complete = interview.get("interview_complete", False) if is_dict else interview.interview_complete

    if is_complete:
        logger.info("Interview is marked complete. Routing to career_coach.")
        return "career_coach"

    transcript = interview.get("transcript", []) if is_dict else interview.transcript
    last_turn = transcript[-1] if transcript else None

    # If the last turn has an answer but no evaluation scores yet, route to evaluator.
    if last_turn and last_turn.get("answer") is not None and last_turn.get("technical_score") is None:
        logger.info("Last turn has unevaluated answer. Routing to interview_evaluator.")
        return "evaluate"

    # If the last turn has a question and no answer yet (or there are no turns),
    # the interview is waiting for user input — halt.
    current_q = interview.get("current_question") if is_dict else interview.current_question
    if current_q and (last_turn is None or last_turn.get("answer") is None):
        logger.info("Active question pending answer. Halting graph execution (routing to END).")
        return "halt"

    # Fallback — should not normally be reached.
    logger.warning("route_from_interview_agent: unrecognised state, halting as fallback.")
    return "halt"


builder = StateGraph(CareerOSState)

builder.add_node("interview_agent", interview_agent_node)
builder.add_node("interview_evaluator", interview_evaluator_node)
builder.add_node("career_coach", career_coach_node)

builder.add_edge(START, "interview_agent")

builder.add_conditional_edges("interview_agent", route_from_interview_agent, {
    "halt": END,
    "evaluate": "interview_evaluator",
    "career_coach": "career_coach",
})

builder.add_edge("interview_evaluator", "interview_agent")
builder.add_edge("career_coach", END)

interview_graph = builder.compile()