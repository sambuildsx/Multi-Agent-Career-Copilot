import re
from typing import List, Optional, Dict

from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, ResumeData
from app.services.resume_parser import PDFService
from app.services.llm_service import LLMService

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
Ensure you accurately extract all skills, experiences (with detailed bullet points), education, projects, and certifications.
For technologies, extract all tools, languages, and frameworks mentioned across the resume into `extracted_technologies`.
"""

RESUME_REVIEW_PROMPT = """You are a Senior Technical Recruiter with 15+ years of experience hiring software engineers.
Comprehensively review the candidate's resume.
You will be provided with the extracted resume data, deterministic score, missing sections, duplicate skills, and identified weak bullets.

Your review must include:
- Section scores (Experience, Education, Projects, Skills, Formatting, ATS Readiness, Overall Impact) out of 100.
- A resume heatmap (e.g., {"Projects": "Excellent", "Experience": "Average", "Formatting": "Needs Improvement"}).
- Strengths and Weaknesses of the resume (explain why, impact, and provide an improved version where applicable).
- Rewritten versions for ALL weak bullets provided, making them impactful, quantifiable, and action-oriented.
- Detailed Project reviews evaluating technical depth, presentation, impact, and identifying missing elements like deployment/testing/CI-CD. Return strengths, weaknesses, an improved description, and expected ATS improvement.
- Priority Actions including priority level, estimated time, expected ATS gain, difficulty, and reason.

Return everything in ONE structured response."""


# --- Agent Implementation ---

class ResumeAgent(BaseAgent):
    def __init__(self):
        self.pdf_service = PDFService()
        self.llm_service = LLMService()

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
        
    def calculate_resume_score(self, resume_data: ResumeData, missing_sections: List[str], duplicate_skills: List[str], weak_bullets: List[str]) -> int:
        score = 100
        
        # Missing sections penalty
        score -= len(missing_sections) * 10
        
        # Duplicate skills penalty
        score -= len(duplicate_skills) * 2
        
        # Weak bullets penalty
        score -= len(weak_bullets) * 2
        
        # Number of projects penalty
        if not resume_data.projects:
            score -= 15
        elif len(resume_data.projects) == 1:
            score -= 5
            
        # Skills count penalty
        if not resume_data.skills or len(resume_data.skills) < 5:
            score -= 10
            
        # Number of quantified bullets bonus / penalty could be implicitly handled by weak_bullets
        # Action verbs are also captured in weak_bullets
        
        return max(0, min(100, score))

    def run(self, state: CareerOSState) -> dict:
        try:
            # 1. Parse resume
            raw_text = self.pdf_service.extract_text(state.resume_pdf_path)
            
            # 2. Extract structured resume information (LLM Call 1)
            resume_data = self.llm_service.extract_structured_data(
                text=raw_text,
                schema=ResumeData,
                system_prompt=RESUME_PROMPT
            )
            if not resume_data:
                raise ValueError("Failed to extract resume data.")
                
            resume_data.raw_text = raw_text
            
            # 3. Deterministic checks
            weak_bullets = self._detect_weak_bullets(resume_data)
            resume_data.weak_bullets = weak_bullets
            
            duplicate_skills = self._detect_duplicate_skills(resume_data.skills)
            missing_sections = self._detect_missing_sections(resume_data)
            
            # 4. Calculate deterministic score
            overall_score = self.calculate_resume_score(resume_data, missing_sections, duplicate_skills, weak_bullets)
            
            # 5. One Recruiter Review LLM Call (LLM Call 2)
            review_prompt_data = (
                f"Candidate Resume Data:\n{resume_data.model_dump_json()}\n\n"
                f"Calculated Deterministic Overall Score: {overall_score}/100\n"
                f"Missing sections identified: {missing_sections}\n"
                f"Duplicate skills identified: {duplicate_skills}\n"
                f"Weak bullets identified:\n" + "\n".join(f"- {b}" for b in weak_bullets)
            )
            
            llm_review = self.llm_service.extract_structured_data(
                text=review_prompt_data,
                schema=ResumeReviewLLMOutput,
                system_prompt=RESUME_REVIEW_PROMPT
            )
            
            if llm_review:
                resume_review = ResumeReview(
                    overall_score=overall_score,
                    section_scores=llm_review.section_scores,
                    resume_heatmap=llm_review.resume_heatmap,
                    strengths=llm_review.strengths,
                    weaknesses=llm_review.weaknesses,
                    rewritten_bullets=llm_review.rewritten_bullets,
                    project_reviews=llm_review.project_reviews,
                    duplicate_skills=duplicate_skills,
                    missing_sections=missing_sections,
                    priority_actions=llm_review.priority_actions
                )
            else:
                # Fallback if LLM extraction fails
                resume_review = ResumeReview(
                    overall_score=overall_score,
                    section_scores=SectionScores(experience=50, education=50, projects=50, skills=50, formatting=50, ats_readiness=50, overall_impact=50),
                    resume_heatmap={},
                    strengths=[],
                    weaknesses=[],
                    rewritten_bullets=[],
                    project_reviews=[],
                    duplicate_skills=duplicate_skills,
                    missing_sections=missing_sections,
                    priority_actions=[]
                )

            return {
                "resume_data": resume_data,
                "resume_review": resume_review,
                "completed_agents": ["resume"]
            }
        except Exception as e:
            return {
                "errors": [f"ResumeAgent failed: {str(e)}"],
                "completed_agents": ["resume"]
            }
