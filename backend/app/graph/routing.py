from app.graph.state import CareerOSState

def route_ingestion(state: CareerOSState):
    if state.errors:
        return "error_node"
    return "fanout"

def route_to_ats(state: CareerOSState):
    if state.resume_data is not None and state.jd_data is not None:
        return "ats_node"
    return "__end__"

def route_to_aggregator(state: CareerOSState):
    if state.ats_result is not None and state.github_data is not None:
        return "aggregator_node"
    return "__end__"
