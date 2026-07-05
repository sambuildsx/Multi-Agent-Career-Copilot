from typing import Optional
from app.graph.state import InterviewPlan
from app.services.llm_service import LLMService

PLANNER_PROMPT = """You are an expert technical interview designer. Given the candidate's
background and (optionally) a target job description, design an interview blueprint.

Only include topics with real evidence of relevance in the resume or JD — don't ask about
a technology that's absent from both. If a JD is provided, weight topic selection toward
what it emphasizes over what the resume happens to list. Keep estimated_questions realistic
for the difficulty and topic count (roughly 2-4 questions per topic)."""


class PlannerAgent:
    def __init__(self):
        self.llm_service = LLMService()

    def run(
        self,
        target_role: str,
        difficulty: str = "medium",
        resume_text: Optional[str] = None,
        jd_text: Optional[str] = None,
    ) -> InterviewPlan:
        parts = [f"Target role: {target_role}", f"Requested difficulty: {difficulty}"]
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
        plan.difficulty = difficulty
        return plan