from typing import List, Optional
from pydantic import BaseModel
from typing import Literal

from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, InterviewPlan, InterviewState
from app.services.llm_service import LLMService


class NextStepDecision(BaseModel):
    """Replaces what used to be two separate calls (difficulty_controller +
    interviewer) with one: decide how the interview should progress AND,
    if continuing, generate the next question in the same response."""
    action: Literal["ask_question", "end_interview"]
    reasoning: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    is_followup: bool = False
    next_question: Optional[str] = None


PLANNER_PROMPT = """You are an expert technical interview designer. Given the candidate's
background and (optionally) a target job description, design an interview blueprint.

Only include topics with real evidence of relevance in the resume or JD — don't ask about
a technology that's absent from both. If a JD is provided, weight topic selection toward
what it emphasizes over what the resume happens to list. Keep estimated_questions realistic
for the difficulty and topic count (roughly 2-4 questions per topic)."""

FIRST_QUESTION_PROMPT = """You are conducting a live technical interview. Given the interview
plan, ask an appropriate opening question for the first topic. Return the question, its
topic, and difficulty. is_followup must be false for an opening question."""

NEXT_STEP_PROMPT = """You are conducting a live technical interview and deciding what happens
next, given the plan and the full transcript so far (including the latest evaluated answer).

Decide ONE of:
- end_interview: if enough topics/questions have been meaningfully covered relative to the
  plan's estimated_questions, or the candidate has clearly struggled across multiple topics
  with no value in continuing.
- ask_question: otherwise. When asking:
  - Follow up on the most recent answer if it was weak, shallow, or worth probing deeper
    (up to the plan's follow_up_depth for that topic).
  - Otherwise move to whichever planned topic has had the fewest questions asked so far.
  - Adjust difficulty up if the candidate is scoring consistently high, down if consistently
    struggling.

Always populate next_question when action is ask_question."""


class InterviewAgent(BaseAgent):
    """Owns the full interview flow: planning, question generation, topic
    switching, adaptive difficulty, and follow-ups. Merges what used to be
    three separate agents (PlannerAgent, InterviewerAgent,
    DifficultyController) into one, per the simplified architecture.
    Never evaluates answers — that's InterviewEvaluator's job."""

    def __init__(self):
        self.llm_service = LLMService()

    def _plan(self, target_role: str, resume_text: Optional[str], jd_text: Optional[str]) -> InterviewPlan:
        parts = [f"Target role: {target_role}"]
        if resume_text:
            parts.append(f"Candidate resume:\n{resume_text}")
        if jd_text:
            parts.append(f"Job description:\n{jd_text}")
        if not resume_text and not jd_text:
            parts.append("No resume or JD provided — design a general blueprint for this role.")
        context = "\n\n".join(parts)

        plan = self.llm_service.extract_structured_data(
            text=context, schema=InterviewPlan, system_prompt=PLANNER_PROMPT
        )
        plan.target_role = target_role
        return plan

    def _first_question(self, plan: InterviewPlan) -> NextStepDecision:
        context = (
            f"Plan: topics={plan.topics}, estimated_questions={plan.estimated_questions}, "
            f"follow_up_depth={plan.follow_up_depth}, difficulty={plan.difficulty}"
        )
        return self.llm_service.extract_structured_data(
            text=context, schema=NextStepDecision, system_prompt=FIRST_QUESTION_PROMPT
        )

    def _next_step(self, interview: InterviewState) -> NextStepDecision:
        plan = interview.plan
        transcript_text = "\n\n".join(
            f"Turn {t['turn_number']} | Topic: {t['topic']} | Followup: {t['is_followup']}\n"
            f"Q: {t['question']}\nA: {t.get('answer')}\n"
            f"Technical score: {t.get('technical_score')}\nCommunication score: {t.get('communication_score')}"
            for t in interview.transcript
        )
        context = (
            f"Plan: topics={plan.topics}, estimated_questions={plan.estimated_questions}, "
            f"follow_up_depth={plan.follow_up_depth}\n"
            f"Current difficulty: {interview.current_difficulty}\n\n"
            f"Transcript so far:\n{transcript_text}"
        )
        return self.llm_service.extract_structured_data(
            text=context, schema=NextStepDecision, system_prompt=NEXT_STEP_PROMPT
        )

    def run(self, state: CareerOSState) -> dict:
        interview = state.get("interview") or InterviewState()

        # Phase 1: no plan yet — design the interview blueprint.
        if interview.plan is None:
            resume_data = state.get("resume_data")
            resume_text = resume_data.raw_text if resume_data else None
            plan = self._plan(state.get("user_goal", ""), resume_text, state.get("jd_text"))
            new_interview = interview.model_copy(update={
                "plan": plan, "current_difficulty": plan.difficulty
            })
            return {"interview": new_interview, "completed_agents": ["interview_agent"]}

        # Phase 2: plan exists but no question asked yet — ask the opener.
        if not interview.transcript:
            decision = self._first_question(interview.plan)
            return self._apply_question(interview, decision)

        # Phase 3: last turn has been evaluated (both scores present) —
        # decide what happens next and ask (or end).
        last_turn = interview.transcript[-1]
        if last_turn.get("answer") is not None and last_turn.get("technical_score") is not None:
            decision = self._next_step(interview)
            if decision.action == "end_interview":
                new_interview = interview.model_copy(update={"interview_complete": True})
                return {"interview": new_interview, "completed_agents": ["interview_agent"]}
            return self._apply_question(interview, decision)

        # Shouldn't normally be reached — a question is pending an answer,
        # which the graph halts on before returning control here.
        return {"completed_agents": ["interview_agent"]}

    def _apply_question(self, interview: InterviewState, decision: NextStepDecision) -> dict:
        new_turn = {
            "turn_number": interview.turn_number + 1,
            "topic": decision.topic or (interview.plan.topics[0] if interview.plan.topics else "General"),
            "difficulty": decision.difficulty or interview.current_difficulty,
            "is_followup": decision.is_followup,
            "question": decision.next_question,
            "answer": None,
            "technical_score": None,
            "communication_score": None,
        }
        updates = {
            "transcript": interview.transcript + [new_turn],
            "turn_number": interview.turn_number + 1,
            "current_topic": new_turn["topic"],
            "current_question": new_turn["question"],
            "current_answer": None,
        }
        if decision.difficulty:
            updates["current_difficulty"] = decision.difficulty

        new_interview = interview.model_copy(update=updates)
        return {"interview": new_interview, "completed_agents": ["interview_agent"]}