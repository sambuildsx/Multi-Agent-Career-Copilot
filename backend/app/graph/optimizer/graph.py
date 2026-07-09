from langgraph.graph import StateGraph, START, END
from app.graph.optimizer.state import CareerOSState
from app.graph.optimizer.nodes import (
    ingestion_node, error_node, fan_out_node, resume_node, jd_node,
    ats_node, aggregator_node
)
from app.graph.optimizer.routing import route_ingestion, route_to_ats

builder = StateGraph(CareerOSState)

import logging
logger = logging.getLogger("uvicorn")

def wait_node(state: CareerOSState) -> dict:
    logger.info(f"[{state['job_id']}] ---> RUNNING NODE: wait_node")
    res = {}
    logger.info("=" * 20 + f"\nOUTPUT FROM wait_node: \n{res}\n" + "=" * 20)
    return res

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
    "error_node": "error_node",
    "ats_node": "ats_node",
    "aggregator_node": "aggregator_node",
    "wait_node": "wait_node",
    "__end__": END
})

builder.add_conditional_edges("jd_node", route_to_ats, {
    "error_node": "error_node",
    "ats_node": "ats_node",
    "aggregator_node": "aggregator_node",
    "wait_node": "wait_node",
    "__end__": END
})

builder.add_edge("ats_node", "aggregator_node")

builder.add_edge("error_node", END)
builder.add_edge("wait_node", "aggregator_node")
builder.add_edge("aggregator_node", END)

app = builder.compile()