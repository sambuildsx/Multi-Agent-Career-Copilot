from typing import Optional, List, Literal, Annotated, Any, TypedDict
import operator

from pydantic import BaseModel
from langgraph.graph import MessagesState

def merge_optional(existing: Any, new: Any) -> Any:
    return new if new is not None else existing

# ---------------- Existing Models ---------------- #

class ResumeData(BaseModel):
    raw_text: str
    skills: List[str]
    experience: List[dict]
    education: List[dict]
    projects: List[dict]
    certifications: List[str]
    weak_bullets: List[str]
    extracted_technologies: List[str]


class JDData(BaseModel):
    raw_text: str
    required_skills: List[str]
    preferred_skills: List[str]
    responsibilities: List[str]
    technologies: List[str]
    experience_level: str
    important_keywords: List[str]


class ATSResult(BaseModel):
    overall_score: int
    keyword_match_score: int
    required_skills_match: int
    preferred_skills_match: int
    completeness_score: int
    project_relevance_score: int
    action_verb_score: int
    quantification_score: int
    strengths: List[str]
    weaknesses: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    score_explanations: dict
    matched_technologies: List[str] = []
    missing_technologies: List[str] = []


# ---------------- GitHub ---------------- #

class GitHubState(BaseModel):
    username: str
    repositories: List[dict]
    languages: dict

    overall_score: int

    activity_score: int
    repository_score: int
    readme_score: int

    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


# ---------------- Interview ---------------- #

class InterviewPlan(BaseModel):
    target_role: str
    domain: str
    difficulty: str

    topics: List[str]

    estimated_questions: int

    follow_up_depth: int


class TechnicalEvaluation(BaseModel):
    score: int
    strengths: List[str]
    weaknesses: List[str]
    feedback: str


class CommunicationEvaluation(BaseModel):
    confidence: int
    clarity: int
    grammar: int
    professionalism: int
    feedback: str


class DifficultyDecision(BaseModel):
    action: str          # increase_difficulty | decrease_difficulty | follow_up | change_topic | end_interview
    reasoning: str
    suggested_difficulty: Optional[str] = None   # easy | medium | hard
    suggested_topic: Optional[str] = None        # only populated when action is change_topic


class InterviewState(BaseModel):
    plan: Optional[InterviewPlan] = None

    current_topic: Optional[str] = None

    current_question: Optional[str] = None

    current_answer: Optional[str] = None

    current_difficulty: str = "medium"

    transcript: List[dict] = []

    turn_number: int = 0

    technical_scores: List[TechnicalEvaluation] = []

    communication_scores: List[CommunicationEvaluation] = []

    last_difficulty_decision: Optional[DifficultyDecision] = None

    interview_complete: bool = False


# ---------------- Final Report ---------------- #

class RecommendationCard(TypedDict, total=False):
    """Structured recommendation card shown in the dashboard.
    All three fields are required when the card is populated."""
    current: str   # what the resume currently says/does — 1 sentence
    better: str    # the specific improved version — 1 sentence
    impact: str    # why this matters to a recruiter — 1 short phrase

class FinalReport(TypedDict, total=False):
    """TypedDict used inside the LangGraph state (resume graph aggregator)."""
    resume_score: Optional[int]
    ats_score: Optional[int]
    top_recommendations: List[str]
    missing_skills: List[str]
    recommendation_cards: List[RecommendationCard]
    report_markdown: str
    has_jd_analysis: Optional[bool]
    matched_technologies: List[str]



class CareerReport(TypedDict, total=False):
    """Comprehensive career report produced by the CareerCoachAgent.
    Used across all workflows — interview, resume, and GitHub."""

    resume_score: Optional[int]
    ats_score: Optional[int]
    github_score: Optional[int]
    interview_score: Optional[int]
    overall_score: Optional[int]
    strengths: List[str]
    weaknesses: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    recommendation_cards: List[RecommendationCard]
    learning_roadmap: List[str]
    markdown: str
    has_jd_analysis: Optional[bool]


# ---------------- LangGraph State ---------------- #

class CareerOSState(TypedDict, total=False):

    # ==========================
    # User
    # ==========================

    workflow_type: str  # "resume" | "resume_jd" | "github" | "interview"

    user_goal: str

    user_id: str

    job_id: str

    target_role: Optional[str]  # technical domain for interview (Backend, Frontend, DSA, etc.)
    # ==========================
    # Orchestration
    # ==========================

    current_agent: Optional[str]

    next_agent: Optional[str]

    workflow_complete: bool

    status: str

    completed_agents: Annotated[list[str], operator.add]

    errors: Annotated[list[str], operator.add]

    # ==========================
    # Resume Flow
    # ==========================

    resume_pdf_path: Optional[str]

    resume_data: Optional[ResumeData]

    jd_text: Optional[str]

    jd_data: Optional[JDData]

    ats_result: Optional[ATSResult]

    resume_review: Optional[Any]

    # ==========================
    # GitHub Flow
    # ==========================

    github_url: Optional[str]

    github_analysis: Optional[GitHubState]

    # ==========================
    # Interview Flow
    # ==========================

    interview: Optional[InterviewState]

    # ==========================
    # Final Output
    # ==========================

    report: Optional[CareerReport]

    final_report: Optional[FinalReport]

    no_jd: Optional[bool]  # True when jd_node ran in no-JD mode; used by routing to skip aggregator