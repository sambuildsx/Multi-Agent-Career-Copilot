import logging

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, TechnicalEvaluation, CommunicationEvaluation
from app.services.llm_service import InterviewLLMService

logger = logging.getLogger("uvicorn")


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
        self.llm_service = InterviewLLMService()

    def run(self, state: CareerOSState) -> dict:
        interview = state.get("interview")
        if not interview:
            raise ValueError("interview_evaluator called with no interview state")

        transcript = interview.transcript if not isinstance(interview, dict) else interview.get("transcript", [])
        current_answer = (interview.current_answer if not isinstance(interview, dict)
                          else interview.get("current_answer"))

        if not transcript:
            logger.warning(
                "interview_evaluator called with an empty transcript — skipping evaluation until a question exists."
            )
            return {
                "errors": [
                    "interview_evaluator received an empty transcript and cannot evaluate an answer."
                ],
                "completed_agents": [],
            }
        if not current_answer:
            logger.warning(
                "interview_evaluator called with no current_answer — skipping evaluation until an answer is submitted."
            )
            return {
                "errors": [
                    "interview_evaluator requires a submitted current_answer before evaluation."
                ],
                "completed_agents": [],
            }

        last_turn = dict(transcript[-1])
        text = (
            f"Topic: {last_turn['topic']}\n"
            f"Question: {last_turn['question']}\n"
            f"Answer: {current_answer}"
        )
        try:
            result = self.llm_service.extract_structured_data(
                text=text, schema=InterviewEvaluationResult, system_prompt=EVALUATION_PROMPT
            )
        except Exception as exc:
            logger.exception("InterviewEvaluatorAgent failed during LLM evaluation")
            return {
                "errors": [str(exc)],
                "completed_agents": [],
            }

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