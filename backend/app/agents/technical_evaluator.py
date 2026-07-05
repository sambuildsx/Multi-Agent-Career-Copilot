from app.graph.state import TechnicalEvaluation
from app.services.llm_service import LLMService

TECHNICAL_EVAL_PROMPT = """You are an expert technical interviewer. Score the candidate's
answer 0-100 on technical correctness and depth. List concrete strengths and weaknesses."""


class TechnicalEvaluatorAgent:
    def __init__(self):
        self.llm_service = LLMService()

    def evaluate(self, topic: str, question: str, answer: str) -> TechnicalEvaluation:
        text = f"Topic: {topic}\nQuestion: {question}\nAnswer: {answer}"
        return self.llm_service.extract_structured_data(
            text=text, schema=TechnicalEvaluation, system_prompt=TECHNICAL_EVAL_PROMPT
        )