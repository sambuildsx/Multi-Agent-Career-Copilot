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

from app.graph.optimizer.state import CareerOSState
from app.services.llm_service import LLMService

logger = logging.getLogger("uvicorn")

MAX_RETRIES = 3

# Final, merged agent set. jd_agent, planner_agent, technical_evaluator,
# communication_agent, and difficulty_controller no longer exist as
# separate agents — their responsibilities live inside ats_agent,
# interview_agent, and interview_evaluator respectively.
ALL_AGENTS = [
    "resume_agent",
    "ats_agent",
    "interview_agent",
    "interview_evaluator",
    "career_coach",
]

WORKFLOW_AGENTS = {
    "resume": ["resume_agent", "career_coach"],
    "resume_jd": ["resume_agent", "ats_agent", "career_coach"],
    "interview": [
        "interview_agent",
        "interview_evaluator",
        "career_coach",
    ],
}

# Agents that should only ever run once per job. interview_agent and
# interview_evaluator are deliberately excluded — they legitimately
# repeat every turn of the interview.
ONE_SHOT_AGENTS = {"resume_agent", "ats_agent"}

REQUIRED_BEFORE_DONE = {
    "resume": ["resume_agent"],
    "resume_jd": ["resume_agent", "ats_agent"],
    "interview": [],  # interview completion is judged by interview.interview_complete, not completed_agents
}

AGENT_DESCRIPTIONS = {
    "resume_agent": "Extracts structured information from the candidate's resume and produces a recruiter-style review.",
    "ats_agent": "Extracts job description requirements and compares them against the resume to produce a deterministic ATS score.",
    "interview_agent": "Plans the interview, asks the next question, and adapts topic/difficulty/follow-ups based on evaluator feedback.",
    "interview_evaluator": "Evaluates the candidate's last answer — technical correctness, communication quality, confidence, clarity.",
    "career_coach": "Produces the final personalized report and recommendations.",
}


class OrchestratorDecision(BaseModel):
    """Reference shape of an orchestrator decision. The actual LLM call
    uses a dynamically narrowed version of this (see _decision_schema)
    so the model is structurally prevented from choosing an agent
    outside the current workflow — not just told not to in the prompt."""

    next_agent: Literal[
        "resume_agent",
        "ats_agent",
        "interview_agent",
        "interview_evaluator",
        "career_coach",
        "DONE",
    ]
    reason: str


def _decision_schema(allowed_agents: List[str]):
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
    from app.graph.optimizer.state import InterviewState
    interview = state.get("interview") or InterviewState()
    transcript = interview.transcript if not isinstance(interview, dict) else interview.get("transcript", [])
    current_answer = (interview.current_answer if not isinstance(interview, dict)
                      else interview.get("current_answer"))

    # True when the last transcript turn has a question but no answer yet —
    # the candidate hasn't responded yet, so the evaluator must NOT run.
    last_turn_unanswered = (
        bool(transcript) and
        transcript[-1].get("answer") is None
    )
    # True when there is a pending answer submitted but not yet scored.
    answer_pending_evaluation = bool(current_answer) and (
        not transcript or transcript[-1].get("technical_score") is None
    )

    lines = [
        f"workflow_type={state.get('workflow_type', 'resume')}",
        f"completed_agents={state.get('completed_agents', [])}",
        f"errors={state.get('errors', [])}",
        f"resume_data_present={state.get('resume_data') is not None}",
        f"jd_text_present={bool(state.get('jd_text'))}",
        f"jd_data_present={state.get('jd_data') is not None}",
        f"ats_result_present={state.get('ats_result') is not None}",
        f"interview_plan_present={interview.plan is not None}",
        f"interview_turn_number={interview.turn_number}",
        f"interview_technical_scores_count={len(interview.technical_scores)}",
        f"interview_communication_scores_count={len(interview.communication_scores)}",
        f"interview_complete={interview.interview_complete}",
        # Key signals for interview routing:
        f"interview_last_turn_unanswered={last_turn_unanswered}  # True = question asked, waiting for candidate answer",
        f"interview_answer_pending_evaluation={answer_pending_evaluation}  # True = answer submitted, needs scoring",
    ]
    return "\n".join(lines)


class OrchestratorAgent:
    def __init__(self):
        self.llm_service = LLMService()

    def decide(self, state: CareerOSState) -> OrchestratorDecision:
        wf_type = state.get("workflow_type", "resume")
        job_id = state.get("job_id", "unknown")
        allowed_agents = WORKFLOW_AGENTS.get(wf_type)
        if not allowed_agents:
            logger.error(f"[{job_id}] Unknown workflow_type '{wf_type}' — defaulting to DONE")
            return OrchestratorDecision(next_agent="DONE", reason=f"Unknown workflow_type '{wf_type}'")

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
                logger.warning(f"[{job_id}] Orchestrator LLM call failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                rejection_feedback = f"Your previous attempt failed with an error: {e}. Try again."
                continue

            is_valid, rejection_reason = self._validate(decision, state, allowed_agents)
            if is_valid:
                logger.info(f"[{job_id}] Orchestrator selected '{decision.next_agent}' — {decision.reason}")
                return OrchestratorDecision(next_agent=decision.next_agent, reason=decision.reason)

            logger.warning(
                f"[{job_id}] Orchestrator rejected '{decision.next_agent}' "
                f"(attempt {attempt}/{MAX_RETRIES}): {rejection_reason}"
            )
            rejection_feedback = (
                f"Your previous choice '{decision.next_agent}' was rejected: {rejection_reason}. "
                f"Choose a different agent."
            )

        fallback = self._fallback_decision(state, allowed_agents)
        logger.error(
            f"[{job_id}] Orchestrator exhausted {MAX_RETRIES} retries — "
            f"falling back to deterministic choice '{fallback.next_agent}'"
        )
        return fallback

    def _validate(
        self, decision: BaseModel, state: CareerOSState, allowed_agents: List[str]
    ) -> Tuple[bool, Optional[str]]:
        from app.graph.optimizer.state import InterviewState
        next_agent = decision.next_agent
        wf_type = state.get("workflow_type", "resume")
        completed = state.get("completed_agents", [])

        if next_agent != "DONE" and next_agent not in allowed_agents:
            return False, f"'{next_agent}' is not valid for workflow '{wf_type}'."

        if next_agent in ONE_SHOT_AGENTS and next_agent in completed:
            return False, f"'{next_agent}' already completed for this job."

        # Hard rule: interview_evaluator must only run when there is a submitted
        # candidate answer and at least one transcript turn to score.
        if next_agent == "interview_evaluator":
            interview = state.get("interview") or InterviewState()
            transcript = interview.transcript if not isinstance(interview, dict) else interview.get("transcript", [])
            current_answer = (interview.current_answer if not isinstance(interview, dict)
                              else interview.get("current_answer"))
            if current_answer is None or (isinstance(current_answer, str) and not current_answer.strip()):
                return False, (
                    "interview_evaluator requires a submitted candidate answer "
                    "(current_answer). No answer is pending — pick interview_agent instead."
                )
            if not transcript:
                return False, "interview_evaluator requires at least one transcript turn."

        if next_agent == "DONE":
            required = REQUIRED_BEFORE_DONE.get(wf_type, [])
            missing = [a for a in required if a not in completed]
            if missing:
                return False, f"Cannot end — required agents not yet completed: {missing}."
            interview = state.get("interview") or InterviewState()
            if wf_type == "interview" and not interview.interview_complete:
                return False, "Cannot end — interview.interview_complete is still False."

        return True, None

    def _fallback_decision(self, state: CareerOSState, allowed_agents: List[str]) -> OrchestratorDecision:
        completed = state.get("completed_agents", [])
        for agent in allowed_agents:
            if agent in ONE_SHOT_AGENTS and agent in completed:
                continue
            return OrchestratorDecision(
                next_agent=agent, reason="Deterministic fallback after repeated invalid LLM decisions."
            )
        return OrchestratorDecision(next_agent="DONE", reason="All agents completed; deterministic fallback.")


def orchestrator_node(state: CareerOSState) -> dict:
    agent = OrchestratorAgent()
    decision = agent.decide(state)

    return {
        "next_agent": decision.next_agent,
        "current_agent": "orchestrator",
        "messages": [AIMessage(content=f"Routing to {decision.next_agent} — {decision.reason}")],
    }