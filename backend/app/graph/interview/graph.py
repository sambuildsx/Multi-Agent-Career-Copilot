from langgraph.graph import StateGraph, START, END
from app.graph.optimizer.state import CareerOSState
from app.agents.orchestrator import orchestrator_node
from app.graph.interview.nodes import (
    interview_agent_node, interview_evaluator_node, career_coach_node,
)


def route_from_orchestrator(state: CareerOSState) -> str:
    return state.get("next_agent", "DONE")


def route_from_interview_agent(state: CareerOSState) -> str:
    # Structural stopping rule: once a fresh question is posted with no
    # answer yet, control must return to the caller (a new HTTP request
    # brings the answer) rather than looping back into the orchestrator
    # expecting input that hasn't arrived.
    interview = state.get("interview", {})
    current_q = interview.get("current_question") if isinstance(interview, dict) else interview.current_question
    current_a = interview.get("current_answer") if isinstance(interview, dict) else interview.current_answer
    if current_q and current_a is None:
        return "halt"
    return "continue"


builder = StateGraph(CareerOSState)

builder.add_node("orchestrator_node", orchestrator_node)
builder.add_node("interview_agent", interview_agent_node)
builder.add_node("interview_evaluator", interview_evaluator_node)
builder.add_node("career_coach", career_coach_node)

builder.add_edge(START, "orchestrator_node")

builder.add_conditional_edges("orchestrator_node", route_from_orchestrator, {
    "interview_agent": "interview_agent",
    "interview_evaluator": "interview_evaluator",
    "career_coach": "career_coach",
    "DONE": END,
})

builder.add_conditional_edges("interview_agent", route_from_interview_agent, {
    "halt": END,
    "continue": "orchestrator_node",
})

builder.add_edge("interview_evaluator", "orchestrator_node")
builder.add_edge("career_coach", "orchestrator_node")

interview_graph = builder.compile()