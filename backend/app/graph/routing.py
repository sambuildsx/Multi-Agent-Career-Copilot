from app.graph.state import CareerOSState


def route_ingestion(state: CareerOSState):
    errors = state.get("errors") if isinstance(state, dict) else state.errors
    if errors:
        return "error_node"
    return "fanout"


def route_to_ats(state: CareerOSState):
    jd_text = state.get("jd_text") if isinstance(state, dict) else state.jd_text
    resume_data = state.get("resume_data") if isinstance(state, dict) else state.resume_data
    jd_data = state.get("jd_data") if isinstance(state, dict) else state.jd_data

    # Resume-only mode: no JD was ever supplied, so there's nothing for
    # jd_node to meaningfully produce and nothing for ats_node to compare
    # against. Go straight to the aggregator once resume parsing is done.
    if not jd_text:
        if resume_data is not None:
            return "aggregator_node"
        # We're the jd_node finishing instantly, wait for resume_node to finish
        return "wait_node"

    # JD-based mode: wait for both resume and JD before running ATS.
    if resume_data is not None and jd_data is not None:
        return "ats_node"
    
    # One node finished before the other. Go to wait_node so we don't hit __end__ and kill the whole graph.
    return "wait_node"