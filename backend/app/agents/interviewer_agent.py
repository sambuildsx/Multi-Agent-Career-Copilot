from typing import List
from pydantic import BaseModel
from app.graph.state import InterviewPlan
from app.services.llm_service import LLMService


class QuestionDecision(BaseModel):
    question: str
    topic: str
    difficulty: str
    is_followup: bool


INTERVIEWER_PROMPT = """You are conducting a live technical interview. Given the interview
plan and the transcript so far, decide what to ask next:
- Follow up on the most recent answer if it was weak, shallow, or worth probing deeper —
  up to the plan's follow_up_depth per topic.
- Otherwise move to whichever planned topic has had the fewest questions asked so far.
Return the question itself, which topic it's on, an appropriate difficulty, and whether
it's a follow-up."""


class InterviewerAgent:
    def __init__(self):
        self.llm_service = LLMService()

    def next_question(self, plan: InterviewPlan, transcript: List[dict]) -> QuestionDecision:
        transcript_text = "\n\n".join(
            f"Turn {t['turn_number']} | Topic: {t['topic']} | Followup: {t['is_followup']}\n"
            f"Q: {t['question']}\nA: {t.get('answer')}\n"
            f"Technical score: {t.get('technical_score')}\nCommunication score: {t.get('communication_score')}"
            for t in transcript
        ) or "No questions asked yet."

        context = (
            f"Plan: topics={plan.topics}, estimated_questions={plan.estimated_questions}, "
            f"follow_up_depth={plan.follow_up_depth}, difficulty={plan.difficulty}\n\n"
            f"Transcript so far:\n{transcript_text}"
        )
        return self.llm_service.extract_structured_data(
            text=context, schema=QuestionDecision, system_prompt=INTERVIEWER_PROMPT
        )