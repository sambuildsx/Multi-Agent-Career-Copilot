from langgraph.graph import StateGraph, START, END
from app.graph.state import CareerOSState
from app.graph.nodes import (
    ingestion_node, error_node, fan_out_node, resume_node, jd_node,
    ats_node, aggregator_node
)
from app.graph.routing import route_ingestion, route_to_ats

builder = StateGraph(CareerOSState)

def wait_node(state: CareerOSState) -> dict:
    # A dummy node to stall a parallel branch until the other one finishes.
    return {}

builder.add_node("ingestion_node", ingestion_node)
builder.add_node("error_node", error_node)
builder.add_node("fan_out_node", fan_out_node)
builder.add_node("resume_node", resume_node)
builder.add_node("jd_node", jd_node)
builder.add_node("ats_node", ats_node)
builder.add_node("aggregator_node", aggregator_node)
builder.add_node("wait_node", wait_node)

builder.add_edge(START, "ingestion_node")

builder.add_conditional_edges("ingestion_node", route_ingestion, {
    "error_node": "error_node",
    "fanout": "fan_out_node"
})

builder.add_edge("fan_out_node", "resume_node")
builder.add_edge("fan_out_node", "jd_node")

builder.add_conditional_edges("resume_node", route_to_ats, {
    "ats_node": "ats_node",
    "aggregator_node": "aggregator_node",
    "wait_node": "wait_node",
    "__end__": END
})

builder.add_conditional_edges("jd_node", route_to_ats, {
    "ats_node": "ats_node",
    "aggregator_node": "aggregator_node",
    "wait_node": "wait_node",
    "__end__": END
})

builder.add_edge("ats_node", "aggregator_node")

builder.add_edge("error_node", END)
builder.add_edge("aggregator_node", END)

app = builder.compile()