"""
Central orchestrator for the AI Career Coach system.

The orchestrator answers exactly one question: who should work next?
It never performs business logic itself — it doesn't parse resumes,
ask interview questions, evaluate answers, or talk to GitHub. It reads
CareerOSState, asks an LLM which specialized agent should run next, and
validates that choice against hard rules before acting on it.

Design principle: the LLM reasons, Python enforces. A bad or invalid
LLM decision never reaches the graph — it gets rejected and retried,
and if retries exhaust, a deterministic safe fallback takes over.
"""

import logging
from typing import List, Optional, Tuple
from pydantic import BaseModel, create_model
from typing import Literal
from langchain_core.messages import AIMessage

from app.graph.state import CareerOSState
from app.services.llm_service import LLMService

logger = logging.getLogger("uvicorn")

MAX_RETRIES = 3

# Every agent that can ever be selected, across all workflows. Used for
# typing/documentation purposes; the LLM is actually constrained per-call
# to a narrower set via a dynamically built schema (see _decision_schema).
ALL_AGENTS = [
    "resume_agent",
    "jd_agent",
    "ats_agent",
    "planner_agent",
    "interviewer_agent",
    "technical_evaluator",
    "communication_agent",
    "difficulty_controller",
    "career_coach",
    "github_agent",
]

# Which agents are legal for each workflow. The orchestrator will never
# be offered (or allowed to pick) an agent outside this set for the
# current workflow, regardless of what the LLM tries to say.
WORKFLOW_AGENTS = {
    "resume": ["resume_agent", "career_coach"],
    "resume_jd": ["resume_agent", "jd_agent", "ats_agent", "career_coach"],
    "github": ["github_agent", "career_coach"],
    "interview": [
        "planner_agent",
        "interviewer_agent",
        "technical_evaluator",
        "communication_agent",
        "difficulty_controller",
        "career_coach",
    ],
}

# Agents that should only ever run once per job. If completed, picking
# them again is rejected. Interview agents are deliberately excluded —
# interviewer/evaluator/communication legitimately repeat every turn.
ONE_SHOT_AGENTS = {"resume_agent", "jd_agent", "ats_agent", "github_agent", "planner_agent"}

# What must already be completed before DONE is a valid choice for a
# given workflow. Prevents the orchestrator from ending a job that never
# actually did its core work.
REQUIRED_BEFORE_DONE = {
    "resume": ["resume_agent"],
    "resume_jd": ["resume_agent", "jd_agent", "ats_agent"],
    "github": ["github_agent"],
    "interview": [],  # interview completion is judged by interview.interview_complete, not completed_agents
}

AGENT_DESCRIPTIONS = {
    "resume_agent": "Extracts structured information from the candidate's resume.",
    "jd_agent": "Extracts structured requirements from a job description.",
    "ats_agent": "Compares resume and job description, produces an ATS-style match score.",
    "planner_agent": "Designs an interview blueprint — topics, question counts, difficulty.",
    "interviewer_agent": "Asks the next interview question based on the current plan and state.",
    "technical_evaluator": "Scores the technical correctness of the candidate's last answer.",
    "communication_agent": "Evaluates the clarity, confidence, and professionalism of the last answer.",
    "difficulty_controller": "Reads scores and history to recommend interview progression — difficulty, topic changes, or ending.",
    "career_coach": "Produces the final personalized report and recommendations.",
    "github_agent": "Reviews a candidate's GitHub profile and repositories.",
}


class OrchestratorDecision(BaseModel):
    """Reference shape of an orchestrator decision. The actual LLM call
    uses a dynamically narrowed version of this (see _decision_schema)
    so the model is structurally prevented from choosing an agent
    outside the current workflow — not just told not to in the prompt."""

    next_agent: Literal[
        "resume_agent",
        "jd_agent",
        "ats_agent",
        "planner_agent",
        "interviewer_agent",
        "technical_evaluator",
        "communication_agent",
        "career_coach",
        "github_agent",
        "DONE",
    ]
    reason: str


def _decision_schema(allowed_agents: List[str]):
    """Builds a one-off Pydantic model whose next_agent field is a Literal
    restricted to exactly the agents valid for the current workflow, plus
    DONE. This is a schema-level constraint, not a prompt-level suggestion
    — the LLM's structured output literally cannot name an agent outside
    this set. Named 'OrchestratorDecision' regardless of workflow so
    LLMService's mock-fallback dispatch (which matches by class name)
    still finds it."""
    choices = tuple(allowed_agents + ["DONE"])
    return create_model(
        "OrchestratorDecision",
        next_agent=(Literal[choices], ...),
        reason=(str, ...),
    )


def _build_system_prompt(allowed_agents: List[str]) -> str:
    agent_lines = "\n".join(
        f"- {name}: {AGENT_DESCRIPTIONS[name]}" for name in allowed_agents
    )
    return f"""You are the central orchestrator of an AI Career Coach system.

Your job is NOT to solve the user's task yourself. Your job is to coordinate
specialized AI agents by choosing exactly one to run next.

Agents available for this workflow:
{agent_lines}

Rules:
- Choose exactly ONE next agent from the list above, or DONE if the workflow
  is genuinely complete.
- Never choose an agent that has already completed its one-time work.
- If you're unsure, prefer the agent that unblocks the most progress next.
- Base your decision on the current state: workflow type, which agents have
  already completed, any errors, and interview progress if applicable."""


def _build_state_context(state: CareerOSState) -> str:
    """Flattens the parts of CareerOSState the orchestrator needs to reason
    about into a compact, consistently formatted string."""
    lines = [
        f"workflow_type={state.workflow_type}",
        f"completed_agents={state.completed_agents}",
        f"errors={state.errors}",
        f"resume_data_present={state.resume_data is not None}",
        f"jd_text_present={bool(state.jd_text)}",
        f"jd_data_present={state.jd_data is not None}",
        f"ats_result_present={state.ats_result is not None}",
        f"github_analysis_present={state.github_analysis is not None}",
        f"interview_plan_present={state.interview.plan is not None}",
        f"interview_turn_number={state.interview.turn_number}",
        f"interview_technical_scores_count={len(state.interview.technical_scores)}",
        f"interview_communication_scores_count={len(state.interview.communication_scores)}",
        f"interview_complete={state.interview.interview_complete}",
    ]
    return "\n".join(lines)


class OrchestratorAgent:
    """Decides which agent runs next. Owns: workflow inspection, calling the
    LLM for a decision, validating that decision against hard rules, retry
    protection, and a deterministic fallback if the LLM can't produce a
    valid decision after MAX_RETRIES attempts."""

    def __init__(self):
        self.llm_service = LLMService()

    def decide(self, state: CareerOSState) -> OrchestratorDecision:
        allowed_agents = WORKFLOW_AGENTS.get(state.workflow_type)
        if not allowed_agents:
            logger.error(f"[{state.job_id}] Unknown workflow_type '{state.workflow_type}' — defaulting to DONE")
            return OrchestratorDecision(next_agent="DONE", reason=f"Unknown workflow_type '{state.workflow_type}'")

        schema = _decision_schema(allowed_agents)
        system_prompt = _build_system_prompt(allowed_agents)
        context = _build_state_context(state)

        rejection_feedback = ""
        for attempt in range(1, MAX_RETRIES + 1):
            prompt_text = context if not rejection_feedback else f"{context}\n\n{rejection_feedback}"

            try:
                decision = self.llm_service.extract_structured_data(
                    text=prompt_text, schema=schema, system_prompt=system_prompt
                )
            except Exception as e:
                logger.warning(f"[{state.job_id}] Orchestrator LLM call failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                rejection_feedback = f"Your previous attempt failed with an error: {e}. Try again."
                continue

            is_valid, rejection_reason = self._validate(decision, state, allowed_agents)
            if is_valid:
                logger.info(f"[{state.job_id}] Orchestrator selected '{decision.next_agent}' — {decision.reason}")
                return OrchestratorDecision(next_agent=decision.next_agent, reason=decision.reason)

            logger.warning(
                f"[{state.job_id}] Orchestrator rejected '{decision.next_agent}' "
                f"(attempt {attempt}/{MAX_RETRIES}): {rejection_reason}"
            )
            rejection_feedback = (
                f"Your previous choice '{decision.next_agent}' was rejected: {rejection_reason}. "
                f"Choose a different agent."
            )

        fallback = self._fallback_decision(state, allowed_agents)
        logger.error(
            f"[{state.job_id}] Orchestrator exhausted {MAX_RETRIES} retries — "
            f"falling back to deterministic choice '{fallback.next_agent}'"
        )
        return fallback

    def _validate(
        self, decision: BaseModel, state: CareerOSState, allowed_agents: List[str]
    ) -> Tuple[bool, Optional[str]]:
        next_agent = decision.next_agent

        if next_agent != "DONE" and next_agent not in allowed_agents:
            return False, f"'{next_agent}' is not valid for workflow '{state.workflow_type}'."

        if next_agent in ONE_SHOT_AGENTS and next_agent in state.completed_agents:
            return False, f"'{next_agent}' already completed for this job."

        if next_agent == "DONE":
            required = REQUIRED_BEFORE_DONE.get(state.workflow_type, [])
            missing = [a for a in required if a not in state.completed_agents]
            if missing:
                return False, f"Cannot end — required agents not yet completed: {missing}."
            if state.workflow_type == "interview" and not state.interview.interview_complete:
                return False, "Cannot end — interview.interview_complete is still False."

        return True, None

    def _fallback_decision(self, state: CareerOSState, allowed_agents: List[str]) -> OrchestratorDecision:
        """Deterministic safe choice when the LLM can't produce a valid
        decision. Picks the first allowed agent not yet completed; if
        everything's completed, ends the workflow."""
        for agent in allowed_agents:
            if agent in ONE_SHOT_AGENTS and agent in state.completed_agents:
                continue
            return OrchestratorDecision(
                next_agent=agent, reason="Deterministic fallback after repeated invalid LLM decisions."
            )
        return OrchestratorDecision(next_agent="DONE", reason="All agents completed; deterministic fallback.")


def orchestrator_node(state: CareerOSState) -> dict:
    """LangGraph node wrapper around OrchestratorAgent. Returns the state
    delta LangGraph expects: next_agent for routing, current_agent for
    bookkeeping, and an AIMessage so the decision shows up in the
    conversation transcript like any other agent action."""
    agent = OrchestratorAgent()
    decision = agent.decide(state)

    return {
        "next_agent": decision.next_agent,
        "current_agent": "orchestrator",
        "messages": [AIMessage(content=f"Routing to {decision.next_agent} — {decision.reason}")],
    }