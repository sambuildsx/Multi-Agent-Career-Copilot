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

        question = transcript[-1]["question"] if transcript else "None"
        answer = current_answer or "None"

        logger.info("=" * 60)
        logger.info("INTERVIEW EVALUATOR STARTED")
        logger.info(f"question={question}")
        logger.info(f"answer={answer}")
        logger.info("=" * 60)

        if not transcript:
            logger.warning(
                "interview_evaluator called with an empty transcript — skipping evaluation until a question exists."
            )
            logger.info("Returning evaluator output")
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
            logger.info("Returning evaluator output")
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
            logger.info("Calling Groq evaluator")
            result = self.llm_service.extract_structured_data(
                text=text, schema=InterviewEvaluationResult, system_prompt=EVALUATION_PROMPT
            )
            logger.info("Groq evaluator finished")
        except Exception:
            logger.exception("Interview node crashed")
            raise

        logger.info(
            f"technical={result.technical.score}, "
            f"communication={result.communication.confidence}"
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
        # Store full feedback text inside the turn dict so the final summary
        # can be assembled from the transcript alone (no extra DB columns needed).
        last_turn["technical_feedback"] = result.technical.feedback
        last_turn["communication_feedback"] = result.communication.feedback
        last_turn["feedback"] = (
            f"Technical: {result.technical.feedback}\n"
            f"Communication: {result.communication.feedback}"
        )

        updated_transcript = interview.transcript[:-1] + [last_turn]
        new_interview = interview.model_copy(update={
            "transcript": updated_transcript,
            "technical_scores": interview.technical_scores + [result.technical],
            "communication_scores": interview.communication_scores + [result.communication],
            "current_answer": None,  # Clear so the interview agent doesn't re-enter evaluation path.
        })
        logger.info("Returning evaluator output")
        return {"interview": new_interview, "completed_agents": ["interview_evaluator"]}