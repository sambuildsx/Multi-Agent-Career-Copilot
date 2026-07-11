import logging
from app.graph.optimizer.state import CareerOSState

logger = logging.getLogger("uvicorn")


def route_ingestion(state: CareerOSState):
    errors = state.get("errors", [])
    if errors:
        return "error_node"
    return "fanout"


def route_to_ats(state: CareerOSState):
    errors = state.get("errors", [])
    if errors:
        logger.info(f"route_to_ats: Found errors={errors}, routing to error_node")
        return "error_node"

    jd_text = state.get("jd_text")
    resume_data = state.get("resume_data")
    jd_data = state.get("jd_data")

    logger.info(f"route_to_ats: jd_text exists={bool(jd_text)}, resume_data exists={resume_data is not None}, jd_data exists={jd_data is not None}")

    # ── No-JD (normal) mode ───────────────────────────────────────────────────
    # jd_node emits a stub JDData with no_jd=True in this case.
    # We must NOT route jd_node to aggregator_node in no-JD mode — only
    # resume_node should trigger the aggregator when no JD was supplied.
    if not jd_text:
        # If this is the stub jd_node invocation, short-circuit to END.
        if state.get("no_jd"):
            logger.info("route_to_ats: no_jd flag set — jd_node skipping to __end__")
            return "__end__"
        if resume_data is not None:
            logger.info("route_to_ats: Routing to aggregator_node (no JD text, resume_data ready)")
            return "aggregator_node"
        # resume_node hasn't landed yet — wait_node now edges to aggregator_node
        # so this path will still complete once state converges.
        logger.info("route_to_ats: Routing to wait_node (no JD text, resume_data not yet in state)")
        return "wait_node"

    # ── JD mode ──────────────────────────────────────────────────────────────
    if resume_data is not None and jd_data is not None:
        logger.info("route_to_ats: Routing to ats_node (both resume_data and jd_data ready)")
        return "ats_node"

    # One of the parallel branches hasn't finished yet.
    # wait_node → aggregator_node edge ensures we don't dead-end.
    logger.info("route_to_ats: Routing to wait_node (JD mode, waiting for both resume_data and jd_data)")
    return "wait_node"