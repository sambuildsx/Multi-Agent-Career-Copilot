from typing import Optional, List, Annotated
from pydantic import BaseModel
import operator

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

class GitHubData(BaseModel):
    username: str
    repos: List[dict]
    pinned_repos: List[dict]
    languages: dict
    overall_github_score: int
    repo_quality_score: int
    diversity_score: int
    activity_score: int
    readme_quality_score: int
    portfolio_feedback: List[str]
    improvement_suggestions: List[str]

class FinalReport(BaseModel):
    resume_score: int
    ats_score: int
    github_score: int
    top_recommendations: List[str]
    missing_skills: List[str]
    report_markdown: str

class CareerOSState(BaseModel):
    # Input
    job_id: str
    user_id: str
    resume_pdf_path: str
    jd_text: str
    github_repo_url: Optional[str] = None

    # Agent outputs (None until agent completes)
    resume_data: Optional[ResumeData] = None
    jd_data: Optional[JDData] = None
    ats_result: Optional[ATSResult] = None
    github_data: Optional[GitHubData] = None
    final_report: Optional[FinalReport] = None

    # Orchestration metadata
    errors: Annotated[List[str], operator.add] = []
    completed_agents: Annotated[List[str], operator.add] = []
    status: str = "pending"
