from typing import Optional, List, Literal, Annotated
import operator

from pydantic import BaseModel
from langgraph.graph import MessagesState

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

class FinalReport(BaseModel):
    """Pydantic model used inside the LangGraph state (resume graph aggregator).
    Not to be confused with the ORM model in models/job.py which shares the
    same name but serves a different purpose (DB persistence)."""
    resume_score: Optional[int] = None
    ats_score: Optional[int] = None
    top_recommendations: List[str] = []
    missing_skills: List[str] = []
    report_markdown: str = ""


class CareerReport(BaseModel):
    """Comprehensive career report produced by the CareerCoachAgent.
    Used across all workflows — interview, resume, and GitHub."""

    resume_score: Optional[int] = None

    ats_score: Optional[int] = None

    github_score: Optional[int] = None

    interview_score: Optional[int] = None

    overall_score: Optional[int] = None

    strengths: List[str] = []

    weaknesses: List[str] = []

    missing_skills: List[str] = []

    recommendations: List[str] = []

    learning_roadmap: List[str] = []

    markdown: str = ""


# ---------------- LangGraph State ---------------- #

class CareerOSState(BaseModel):

    # ==========================
    # User
    # ==========================

    workflow_type: Literal[
        "resume",
        "resume_jd",
        "github",
        "interview",
    ] = "resume"

    user_goal: str = ""

    user_id: str

    job_id: str

    # ==========================
    # Orchestration
    # ==========================

    current_agent: Optional[str] = None

    next_agent: Optional[str] = None

    workflow_complete: bool = False

    status: str = "pending"

    completed_agents: Annotated[List[str], operator.add] = []

    errors: Annotated[List[str], operator.add] = []

    # ==========================
    # Resume Flow
    # ==========================

    resume_pdf_path: Optional[str] = None

    resume_data: Optional[ResumeData] = None

    jd_text: Optional[str] = None

    jd_data: Optional[JDData] = None

    ats_result: Optional[ATSResult] = None

    # ==========================
    # GitHub Flow
    # ==========================

    github_url: Optional[str] = None

    github_analysis: Optional[GitHubState] = None

    # ==========================
    # Interview Flow
    # ==========================

    interview: InterviewState = InterviewState()

    # ==========================
    # Final Output
    # ==========================

    report: Optional[CareerReport] = None

    final_report: Optional[FinalReport] = None