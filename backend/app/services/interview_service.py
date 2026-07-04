from typing import List, Optional, Literal
from pydantic import BaseModel
from app.services.llm_service import LLMService

ALLOWED_DOMAINS = ["backend", "frontend", "system_design", "dsa"]
MAX_TURNS = 8


class GeneratedQuestion(BaseModel):
    question: str


class AnswerEvaluation(BaseModel):
    score: int  # 0-100
    feedback: str
    strengths: List[str]
    weaknesses: List[str]


class NextStepDecision(BaseModel):
    action: Literal["follow_up", "new_topic", "end"]
    next_question: Optional[str] = None
    reasoning: str


class InterviewSummary(BaseModel):
    overall_score: int
    summary_markdown: str
    key_strengths: List[str]
    key_areas_to_improve: List[str]


class InterviewOrchestrator:
    """Drives the adaptive interview loop. Unlike the resume/JD pipeline,
    this genuinely needs LLM judgment at each step — whether to follow up,
    move on, or end depends on the quality of the conversation so far, not
    a fixed dependency graph. Each method is a single LLM call; the router
    layer is responsible for persisting turns between calls."""

    def __init__(self):
        self.llm_service = LLMService()

    def generate_first_question(self, domain: str) -> str:
        system_prompt = (
            f"You are conducting a technical interview for the '{domain}' domain. "
            "Ask one clear opening question suitable for evaluating a candidate's "
            "fundamentals in this domain. Return only the question."
        )
        result = self.llm_service.extract_structured_data(
            text=domain,
            schema=GeneratedQuestion,
            system_prompt=system_prompt,
        )
        return result.question

    def evaluate_answer(self, domain: str, question: str, answer: str) -> AnswerEvaluation:
        text = f"Domain: {domain}\nQuestion: {question}\nCandidate's Answer: {answer}"
        system_prompt = (
            "You are an expert technical interviewer. Evaluate the candidate's "
            "answer. Score 0-100. Be fair but rigorous. List concrete strengths "
            "and weaknesses."
        )
        return self.llm_service.extract_structured_data(
            text=text, schema=AnswerEvaluation, system_prompt=system_prompt
        )

    def decide_next_step(self, domain: str, transcript: List[dict]) -> NextStepDecision:
        if len(transcript) >= MAX_TURNS:
            return NextStepDecision(
                action="end", next_question=None, reasoning="Reached maximum turn limit."
            )

        transcript_text = "\n\n".join(
            f"Q{i+1}: {t['question']}\nA{i+1}: {t['answer']}\nScore: {t['score']}/100"
            for i, t in enumerate(transcript)
        )
        system_prompt = f"""You are supervising a technical interview in the '{domain}' domain.
Given the transcript so far, decide what happens next:
- "follow_up": probe deeper on the most recent answer — either because it was weak/shallow, or because it was strong and worth pushing further
- "new_topic": move to a new topic within the domain, since the current one is sufficiently covered
- "end": end the interview — typically once 4-6 solid exchanges have happened and enough ground is covered

If continuing, provide the exact next question to ask."""
        return self.llm_service.extract_structured_data(
            text=transcript_text, schema=NextStepDecision, system_prompt=system_prompt
        )

    def summarize(self, domain: str, transcript: List[dict]) -> InterviewSummary:
        transcript_text = "\n\n".join(
            f"Q{i+1}: {t['question']}\nA{i+1}: {t['answer']}\nScore: {t['score']}/100\nFeedback: {t['feedback']}"
            for i, t in enumerate(transcript)
        )
        system_prompt = (
            f"You are summarizing a completed technical interview in the '{domain}' "
            "domain. Provide an overall score (0-100) and a clear, constructive summary."
        )
        return self.llm_service.extract_structured_data(
            text=transcript_text, schema=InterviewSummary, system_prompt=system_prompt
        )