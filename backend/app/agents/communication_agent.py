from app.graph.state import CommunicationEvaluation
from app.services.llm_service import LLMService

COMMUNICATION_PROMPT = """You are evaluating a candidate's communication in a technical
interview. Score confidence, clarity, grammar, and professionalism, each 0-100, based only
on how the answer was communicated — not its technical correctness."""


class CommunicationAgent:
    def __init__(self):
        self.llm_service = LLMService()

    def evaluate(self, question: str, answer: str) -> CommunicationEvaluation:
        text = f"Question: {question}\nAnswer: {answer}"
        return self.llm_service.extract_structured_data(
            text=text, schema=CommunicationEvaluation, system_prompt=COMMUNICATION_PROMPT
        )