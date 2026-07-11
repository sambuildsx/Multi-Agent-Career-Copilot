import re
import logging
from typing import List, Optional, Dict

from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent
from app.graph.optimizer.state import CareerOSState, ResumeData    
from app.services.resume_parser import PDFService
from app.services.llm_service import LLMService

logger = logging.getLogger("uvicorn")   

ACTION_VERBS = {
    "achieved", "built", "optimized", "reduced", "improved", "developed", 
    "managed", "led", "created", "designed", "implemented", "increased", 
    "decreased", "spearheaded", "delivered", "architected", "engineered",
    "deployed", "orchestrated", "automated", "streamlined", "resolved",
    "transformed", "modernized"
}

GENERIC_VERBS = {
    "worked on", "helped", "responsible for", "assisted", "participated in"
}

# --- Pydantic Models for Output ---

class RewrittenBullet(BaseModel):
    original: str = Field(description="The original weak bullet point")
    rewritten: str = Field(description="The improved, quantifiable, and action-oriented bullet point")
    why: str = Field(description="Why this change was made")
    impact: str = Field(description="The impact of this change on the resume's quality")

class ProjectReview(BaseModel):
    project_name: str
    review: str = Field(description="A brief review of the project's presentation")
    score: int = Field(description="Score for this project out of 100")
    strengths: List[str] = Field(description="Strengths of the project presentation")
    weaknesses: List[str] = Field(description="Weaknesses, including missing deployment/testing/CI-CD")
    improved_description: str = Field(description="An improved way to describe this project")
    expected_ATS_improvement: str = Field(description="Expected ATS improvement (e.g., '+5 points')")

class SectionScores(BaseModel):
    experience: int = Field(description="Score out of 100")
    education: int = Field(description="Score out of 100")
    projects: int = Field(description="Score out of 100")
    skills: int = Field(description="Score out of 100")
    formatting: int = Field(description="Score out of 100")
    ats_readiness: int = Field(description="Score out of 100")
    overall_impact: int = Field(description="Score out of 100")

class PriorityAction(BaseModel):
    action: str = Field(description="The priority action to take")
    priority: str = Field(description="High, Medium, or Low")
    estimated_time: str = Field(description="Estimated time to complete (e.g., '15 mins')")
    estimated_ATS_gain: str = Field(description="Expected ATS score increase")
    difficulty: str = Field(description="Easy, Medium, or Hard")
    reason: str = Field(description="Why this is a priority")

class Recommendation(BaseModel):
    recommendation: str = Field(description="The strength or weakness point")
    why: str = Field(description="Why this is a strength or weakness")
    impact: str = Field(description="The impact of this on the resume")
    improved_version: Optional[str] = Field(description="An improved version or example, if applicable", default=None)

class ResumeReviewLLMOutput(BaseModel):
    section_scores: SectionScores
    resume_heatmap: Dict[str, str] = Field(description="Heatmap rating per section. E.g., {'Projects': 'Excellent', 'Experience': 'Average'}")
    strengths: List[Recommendation]
    weaknesses: List[Recommendation]
    rewritten_bullets: List[RewrittenBullet]
    project_reviews: List[ProjectReview]
    priority_actions: List[PriorityAction]

class ResumeReview(BaseModel):
    overall_score: int
    section_scores: SectionScores
    resume_heatmap: Dict[str, str]
    strengths: List[Recommendation]
    weaknesses: List[Recommendation]
    rewritten_bullets: List[RewrittenBullet]
    project_reviews: List[ProjectReview]
    duplicate_skills: List[str]
    missing_sections: List[str]
    priority_actions: List[PriorityAction]


# --- Prompts ---

RESUME_PROMPT = """You are an expert technical recruiter. Extract the candidate's information from the provided resume text.
Ensure you accurately extract all skills, experiences, education, projects, and certifications.
Keep descriptions and extracted experience/project bullet points extremely concise (maximum 15 words per bullet point) during extraction.
For technologies, extract all tools, languages, and frameworks mentioned across the resume into `extracted_technologies`.
"""

RESUME_REVIEW_PROMPT = """You are a Senior Technical Recruiter with 15+ years of experience hiring software engineers.
Comprehensively review the candidate's resume.
You will be provided with the extracted resume data, deterministic score, missing sections, duplicate skills, and identified weak bullets.

To optimize generation speed, keep all generated feedback extremely brief, concise, and punchy.
Your review must include:
- Section scores (Experience, Education, Projects, Skills, Formatting, ATS Readiness, Overall Impact) out of 100.
- A resume heatmap (e.g., {"Projects": "Excellent", "Experience": "Average", "Formatting": "Needs Improvement"}).
- Strengths and Weaknesses of the resume (explain why, impact, and provide an improved version where applicable). LIMIT descriptions/explanations to 20 words maximum per item.
- Rewritten versions for ALL weak bullets provided, making them impactful, quantifiable, and action-oriented. LIMIT rewritten bullets to 15 words maximum.
- Detailed Project reviews evaluating technical depth, presentation, impact, and identifying missing elements like deployment/testing/CI-CD. LIMIT strengths/weaknesses and improved descriptions to 20 words maximum per item.
- Priority Actions including priority level, estimated time, expected ATS gain, difficulty, and reason. LIMIT reason to 15 words maximum.

Return everything in ONE structured response."""


# --- Agent Implementation ---

class ResumeAgent(BaseAgent):
    def __init__(self):
        self.pdf_service = PDFService()
        self.llm_service = LLMService()

    def run(self, state: CareerOSState) -> dict:          # <-- NEW METHOD STARTS HERE
        try:
            pdf_path = state.get("resume_pdf_path")
            if not pdf_path:
                raise ValueError("resume_pdf_path is required for resume analysis.")

            raw_text = self.pdf_service.extract_text(pdf_path)

            resume_data: ResumeData = self.llm_service.extract_structured_data(
                text=raw_text, schema=ResumeData, system_prompt=RESUME_PROMPT
            )
            resume_data.raw_text = raw_text

            weak_bullets = self._detect_weak_bullets(resume_data)
            missing_sections = self._detect_missing_sections(resume_data)
            duplicate_skills = self._detect_duplicate_skills(resume_data.skills or [])
            resume_data.weak_bullets = weak_bullets

            overall_score = self.calculate_resume_score(
                resume_data, missing_sections, duplicate_skills, weak_bullets
            )

            review_context = (
                f"Deterministic overall score: {overall_score}/100\n"
                f"Missing sections: {', '.join(missing_sections) or 'none'}\n"
                f"Duplicate skills: {', '.join(duplicate_skills) or 'none'}\n"
                f"Weak bullets flagged:\n"
                + "\n".join(f"- {b}" for b in weak_bullets)
                + f"\n\nResume data:\n{resume_data.model_dump_json()}"
            )

            llm_output: ResumeReviewLLMOutput = self.llm_service.extract_structured_data(
                text=review_context,
                schema=ResumeReviewLLMOutput,
                system_prompt=RESUME_REVIEW_PROMPT,
            )

            resume_review = ResumeReview(
                overall_score=overall_score,
                duplicate_skills=duplicate_skills,
                missing_sections=missing_sections,
                **llm_output.model_dump(),
            )

            return {
                "resume_data": resume_data,
                "resume_review": resume_review,
                "completed_agents": ["resume"],
            }
        except Exception as e:
            logger.error(f"ResumeAgent.run failed: {e}", exc_info=True)
            return {
                "errors": [f"ResumeAgent failed: {str(e)}"],
                "completed_agents": ["resume"],
            }


    def _detect_weak_bullets(self, resume_data: ResumeData) -> List[str]:
        weak_bullets = []
        seen_verbs = set()
        candidate_skills = [s.lower() for s in resume_data.skills] if resume_data.skills else []

        def is_weak(bullet: str) -> bool:
            lower_b = bullet.lower()
            words = re.findall(r'\w+', lower_b)
            
            # 1. Shorter than 8 words
            if len(words) < 8:
                return True
                
            # 2. Generic verbs
            if any(generic in lower_b for generic in GENERIC_VERBS):
                return True
                
            # 3. Action verbs and repeated verbs
            bullet_verbs = [verb for verb in words if verb in ACTION_VERBS]
            has_action_verb = len(bullet_verbs) > 0
            
            repeated_verb = False
            for v in bullet_verbs:
                if v in seen_verbs:
                    repeated_verb = True
                seen_verbs.add(v)
                
            # 4. Quantification (Measurable impact)
            has_quantification = bool(re.search(r'\d+', bullet)) or bool(re.search(r'\b(one|two|three|four|five|six|seven|eight|nine|ten|percent|%)\b', lower_b))
            
            # 5. Missing technologies
            has_tech = any(s in lower_b for s in candidate_skills)
            
            return not has_action_verb or not has_quantification or not has_tech or repeated_verb

        for exp in resume_data.experience:
            for bullet in exp.get("bullets", []):
                if is_weak(bullet):
                    weak_bullets.append(bullet)
                    
        for proj in resume_data.projects:
            for bullet in proj.get("bullets", []):
                if is_weak(bullet):
                    weak_bullets.append(bullet)
                    
        return weak_bullets

    def _detect_missing_sections(self, resume_data: ResumeData) -> List[str]:
        missing = []
        if not resume_data.experience:
            missing.append("Experience")
        if not resume_data.education:
            missing.append("Education")
        if not resume_data.projects:
            missing.append("Projects")
        if not resume_data.skills:
            missing.append("Skills")
        return missing

    def _detect_duplicate_skills(self, skills: List[str]) -> List[str]:
        seen = set()
        duplicates = set()
        for skill in skills:
            normalized = skill.lower().strip()
            if normalized in seen:
                duplicates.add(skill)
            else:
                seen.add(normalized)
        return list(duplicates)
        
    def calculate_resume_score(
        self,
        resume_data: ResumeData,
        missing_sections: List[str],
        duplicate_skills: List[str],
        weak_bullets: List[str],
    ) -> int:
        """Deterministic, additive-and-subtractive scoring. The old version was
        purely subtractive — a resume with zero flaws but thin substance could
        outscore one with excellent projects and one typo. This version rewards
        real signal (project count, experience, quantification quality) before
        applying penalties, so strong resumes land in a realistic 75-90 range
        instead of getting dragged down by minor deductions."""

        all_bullets: List[str] = []
        for exp in resume_data.experience:
            all_bullets.extend(exp.get("bullets", []))
        for proj in resume_data.projects:
            all_bullets.extend(proj.get("bullets", []))

        total_bullets = len(all_bullets)
        weak_count = len(weak_bullets)
        # Fraction of bullets that are NOT flagged weak — i.e. actually strong.
        strong_ratio = 1.0 if total_bullets == 0 else max(0.0, (total_bullets - weak_count) / total_bullets)

        # --- Experience: presence + volume + quality of bullets ---
        if not resume_data.experience:
            experience_score = 0
        else:
            base = min(100, 50 + len(resume_data.experience) * 15)
            experience_score = int(base * (0.5 + 0.5 * strong_ratio))

        # --- Projects: presence + volume + whether a stack is listed + quality ---
        if not resume_data.projects:
            project_score = 0
        else:
            base = min(100, 40 + len(resume_data.projects) * 15)
            with_stack = sum(1 for p in resume_data.projects if p.get("stack"))
            stack_bonus = int((with_stack / len(resume_data.projects)) * 20)
            project_score = min(100, base + stack_bonus)
            project_score = int(project_score * (0.5 + 0.5 * strong_ratio))

        # --- Skills: breadth, penalized for duplicates ---
        skill_count = len(resume_data.skills or [])
        if skill_count == 0:
            skills_score = 0
        else:
            skills_score = max(0, min(100, skill_count * 8) - len(duplicate_skills) * 5)

        # --- Education: presence only (depth isn't extracted reliably enough to score) ---
        education_score = 100 if resume_data.education else 30

        # --- Certifications: small bonus, not a core component ---
        cert_bonus = min(10, len(resume_data.certifications or []) * 5)

        # --- Missing sections: real penalty, applied after the positive signal is counted ---
        completeness_penalty = len(missing_sections) * 12

        weighted = (
            experience_score * 0.30
            + project_score * 0.30
            + skills_score * 0.20
            + education_score * 0.10
            + (strong_ratio * 100) * 0.10
        )

        final_score = weighted + cert_bonus - completeness_penalty
        return max(0, min(100, int(round(final_score))))