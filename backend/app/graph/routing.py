from app.graph.state import CareerOSState


def route_ingestion(state: CareerOSState):
    if state.errors:
        return "error_node"
    return "fanout"


def route_to_ats(state: CareerOSState):
    # Resume-only mode: no JD was ever supplied, so there's nothing for
    # jd_node to produce and nothing for ats_node to compare against.
    # Go straight to the aggregator once resume parsing is done.
    if not state.jd_text:
        if state.resume_data is not None:
            return "aggregator_node"
        return "__end__"

    # JD-based mode: wait for both resume and JD before running ATS.
    if state.resume_data is not None and state.jd_data is not None:
        return "ats_node"
    return "__end__"