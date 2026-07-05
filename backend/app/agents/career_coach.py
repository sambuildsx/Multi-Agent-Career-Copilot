from typing import List
from app.graph.state import CareerReport
from app.services.llm_service import LLMService

COACH_PROMPT = """You are a career coach summarizing a completed technical interview.
Given the full transcript with technical and communication scores, produce an overall
interview_score (0-100), strengths, weaknesses, recommendations, and a markdown summary."""


class CareerCoachAgent:
    def __init__(self):
        self.llm_service = LLMService()

    def summarize_interview(self, transcript: List[dict]) -> CareerReport:
        transcript_text = "\n\n".join(
            f"Topic: {t['topic']}\nQ: {t['question']}\nA: {t.get('answer')}\n"
            f"Technical: {t.get('technical_score')} | Communication: {t.get('communication_score')}"
            for t in transcript
        )
        return self.llm_service.extract_structured_data(
            text=transcript_text, schema=CareerReport, system_prompt=COACH_PROMPT
        )