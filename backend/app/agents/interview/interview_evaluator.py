from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, TechnicalEvaluation, CommunicationEvaluation
from app.services.llm_service import LLMService


class InterviewEvaluationResult(BaseModel):
    technical: TechnicalEvaluation
    communication: CommunicationEvaluation


EVALUATION_PROMPT = """You are evaluating a candidate's answer in a live technical interview.
Score BOTH dimensions in one pass:
- Technical: correctness and depth (0-100), with concrete strengths/weaknesses and feedback.
- Communication: confidence, clarity, grammar, and professionalism (each 0-100), based only
  on how the answer was communicated, not its technical correctness, with feedback.
"""


class InterviewEvaluatorAgent(BaseAgent):
    """Owns all interview answer evaluation — technical and communication —
    in a single LLM call (previously two separate agents/calls: this is
    the main latency/quota win in Phase 2). Never generates questions;
    that's InterviewAgent's job."""

    def __init__(self):
        self.llm_service = LLMService()

    def run(self, state: CareerOSState) -> dict:
        interview = state.get("interview")
        last_turn = dict(interview.transcript[-1])
        text = (
            f"Topic: {last_turn['topic']}\n"
            f"Question: {last_turn['question']}\n"
            f"Answer: {interview.current_answer}"
        )
        result = self.llm_service.extract_structured_data(
            text=text, schema=InterviewEvaluationResult, system_prompt=EVALUATION_PROMPT
        )

        last_turn["answer"] = interview.current_answer
        last_turn["technical_score"] = result.technical.score
        # Composite communication score — average of all four sub-dimensions,
        # rather than picking just one (confidence), as the old
        # CommunicationAgent did.
        last_turn["communication_score"] = int(
            (result.communication.confidence + result.communication.clarity +
             result.communication.grammar + result.communication.professionalism) / 4
        )

        updated_transcript = interview.transcript[:-1] + [last_turn]
        new_interview = interview.model_copy(update={
            "transcript": updated_transcript,
            "technical_scores": interview.technical_scores + [result.technical],
            "communication_scores": interview.communication_scores + [result.communication],
        })
        return {"interview": new_interview, "completed_agents": ["interview_evaluator"]}