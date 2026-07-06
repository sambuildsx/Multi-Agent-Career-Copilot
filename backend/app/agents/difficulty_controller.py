import logging
from typing import List

from app.graph.state import DifficultyDecision, TechnicalEvaluation, CommunicationEvaluation
from app.services.llm_service import LLMService

logger = logging.getLogger("uvicorn")

DIFFICULTY_PROMPT = """You are a difficulty calibration engine for a live technical interview.
Your job is NOT to ask questions. You never generate questions. You only decide what should
happen next based on the candidate's performance so far.

Given the interview transcript with technical and communication scores, decide one of:
- "increase_difficulty": candidate is handling this level comfortably, push harder
- "decrease_difficulty": candidate is struggling significantly, ease up
- "follow_up": the last answer was interesting enough to probe deeper on the same topic
- "change_topic": this topic has been sufficiently explored, move to another planned topic
- "end_interview": enough signal has been gathered across topics to produce a meaningful report

Consider:
- If average technical score > 75 and at least 2 questions answered, consider increasing difficulty
- If average technical score < 40 over recent answers, consider decreasing
- If the same topic has had 3+ questions already, lean toward changing topic
- If total questions answered >= estimated_questions from the plan, lean toward ending
- If communication scores are consistently low, that alone is not a reason to end — but factor it into difficulty

Return the action, your reasoning, and optionally a suggested difficulty level or topic."""


class DifficultyControllerAgent:
    """Reads evaluation scores and interview history to recommend how the
    interview should progress. Never generates questions — only advises the
    orchestrator on pacing, difficulty, and topic transitions."""

    def __init__(self):
        self.llm_service = LLMService()

    def evaluate(
        self,
        transcript: List[dict],
        technical_scores: List[TechnicalEvaluation],
        communication_scores: List[CommunicationEvaluation],
        current_topic: str,
        current_difficulty: str,
        estimated_questions: int,
        topics: List[str],
    ) -> DifficultyDecision:
        # Build a compact summary the LLM can reason over without needing
        # the full transcript text (which would blow up the context for
        # long interviews for no real benefit).
        score_lines = []
        for i, turn in enumerate(transcript):
            tech = turn.get("technical_score", "n/a")
            comm = turn.get("communication_score", "n/a")
            score_lines.append(
                f"Turn {turn.get('turn_number', i+1)} | Topic: {turn.get('topic')} | "
                f"Difficulty: {turn.get('difficulty', 'medium')} | "
                f"Technical: {tech} | Communication: {comm} | "
                f"Followup: {turn.get('is_followup', False)}"
            )

        recent_tech = [s.score for s in technical_scores[-3:]] if technical_scores else []
        recent_comm = []
        for s in communication_scores[-3:]:
            avg = (s.confidence + s.clarity + s.grammar + s.professionalism) // 4
            recent_comm.append(avg)

        context = (
            f"Current topic: {current_topic}\n"
            f"Current difficulty: {current_difficulty}\n"
            f"Planned topics: {topics}\n"
            f"Estimated total questions: {estimated_questions}\n"
            f"Questions asked so far: {len(transcript)}\n"
            f"Recent technical scores (last 3): {recent_tech}\n"
            f"Recent communication scores (last 3): {recent_comm}\n\n"
            f"Turn-by-turn summary:\n" + "\n".join(score_lines)
        )

        return self.llm_service.extract_structured_data(
            text=context,
            schema=DifficultyDecision,
            system_prompt=DIFFICULTY_PROMPT,
        )
