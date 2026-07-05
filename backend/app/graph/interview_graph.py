from langgraph.graph import StateGraph, START, END
from app.graph.state import CareerOSState
from app.agents.orchestrator import orchestrator_node
from app.graph.interview_nodes import (
    planner_node, interviewer_node, technical_evaluator_node,
    communication_agent_node, career_coach_node,
)


def route_from_orchestrator(state: CareerOSState) -> str:
    return state.next_agent


def route_from_interviewer(state: CareerOSState) -> str:
    # Structural stopping rule, not a business decision: once a new question
    # is posted with no answer yet, control must return to the caller (a
    # fresh HTTP request will bring the answer) rather than looping back into
    # the orchestrator expecting input that hasn't arrived.
    if state.interview.current_question and state.interview.current_answer is None:
        return "halt"
    return "continue"


builder = StateGraph(CareerOSState)

builder.add_node("orchestrator_node", orchestrator_node)
builder.add_node("planner_agent", planner_node)
builder.add_node("interviewer_agent", interviewer_node)
builder.add_node("technical_evaluator", technical_evaluator_node)
builder.add_node("communication_agent", communication_agent_node)
builder.add_node("career_coach", career_coach_node)

builder.add_edge(START, "orchestrator_node")

builder.add_conditional_edges("orchestrator_node", route_from_orchestrator, {
    "planner_agent": "planner_agent",
    "interviewer_agent": "interviewer_agent",
    "technical_evaluator": "technical_evaluator",
    "communication_agent": "communication_agent",
    "career_coach": "career_coach",
    "DONE": END,
})

builder.add_conditional_edges("interviewer_agent", route_from_interviewer, {
    "halt": END,
    "continue": "orchestrator_node",
})

builder.add_edge("planner_agent", "orchestrator_node")
builder.add_edge("technical_evaluator", "orchestrator_node")
builder.add_edge("communication_agent", "orchestrator_node")
builder.add_edge("career_coach", "orchestrator_node")

app = builder.compile()