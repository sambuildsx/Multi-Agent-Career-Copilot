import logging
from typing import List, Optional

from app.graph.state import CareerReport, ResumeData, ATSResult
from app.services.llm_service import LLMService

logger = logging.getLogger("uvicorn")

INTERVIEW_COACH_PROMPT = """You are a career coach summarizing a completed technical interview.
Given the full transcript with technical and communication scores, produce an overall
interview_score (0-100), strengths, weaknesses, recommendations, and a markdown summary."""

RESUME_COACH_PROMPT = """You are a career coach reviewing a candidate's resume analysis results.
Given the parsed resume data and (optionally) ATS comparison results, produce a comprehensive
career report. Evaluate the candidate's positioning, identify skill gaps, and provide a
concrete learning roadmap. Be specific — don't say "improve skills", say which skills and how."""

GITHUB_COACH_PROMPT = """You are a career coach reviewing a candidate's GitHub portfolio analysis.
Given the repository data, language distribution, activity metrics, and quality scores,
produce a career report focused on the candidate's public engineering presence. Identify
what their portfolio communicates to recruiters, what's missing, and how to improve it."""


class CareerCoachAgent:
    """Produces final career reports across all workflows. Each method handles
    a different workflow's data shape, but they all output the same CareerReport
    model so downstream consumers (routes, frontend) have a consistent contract."""

    def __init__(self):
        self.llm_service = LLMService()

    def summarize_interview(self, transcript: List[dict]) -> CareerReport:
        """Generate a career report from a completed mock interview."""
        transcript_text = "\n\n".join(
            f"Topic: {t['topic']}\nQ: {t['question']}\nA: {t.get('answer')}\n"
            f"Technical: {t.get('technical_score')} | Communication: {t.get('communication_score')}"
            for t in transcript
        )
        return self.llm_service.extract_structured_data(
            text=transcript_text, schema=CareerReport, system_prompt=INTERVIEW_COACH_PROMPT
        )

    def summarize_resume(
        self,
        resume_data: ResumeData,
        ats_result: Optional[ATSResult] = None,
    ) -> CareerReport:
        """Generate a career report from resume analysis (with optional ATS comparison)."""
        parts = [
            f"Skills: {', '.join(resume_data.skills)}",
            f"Technologies: {', '.join(resume_data.extracted_technologies)}",
            f"Experience entries: {len(resume_data.experience)}",
            f"Projects: {len(resume_data.projects)}",
            f"Certifications: {', '.join(resume_data.certifications) if resume_data.certifications else 'None'}",
            f"Weak bullets identified: {len(resume_data.weak_bullets)}",
        ]

        if resume_data.weak_bullets:
            sample = resume_data.weak_bullets[:5]
            parts.append(f"Example weak bullets:\n" + "\n".join(f"  - {b}" for b in sample))

        if ats_result:
            parts.extend([
                f"\nATS Overall Score: {ats_result.overall_score}/100",
                f"Keyword Match: {ats_result.keyword_match_score}/100",
                f"Required Skills Match: {ats_result.required_skills_match}/100",
                f"Missing Skills: {', '.join(ats_result.missing_skills) if ats_result.missing_skills else 'None'}",
                f"ATS Strengths: {', '.join(ats_result.strengths)}",
                f"ATS Weaknesses: {', '.join(ats_result.weaknesses)}",
            ])

        context = "\n".join(parts)
        return self.llm_service.extract_structured_data(
            text=context, schema=CareerReport, system_prompt=RESUME_COACH_PROMPT
        )

    def summarize_github(self, github_data: dict) -> CareerReport:
        """Generate a career report from GitHub portfolio analysis."""
        parts = [
            f"Username: {github_data.get('username', 'unknown')}",
            f"Repositories analyzed: {len(github_data.get('repos', []))}",
            f"Languages: {github_data.get('languages', {})}",
            f"Overall GitHub Score: {github_data.get('overall_github_score', 0)}",
            f"Repo Quality Score: {github_data.get('repo_quality_score', 0)}",
            f"Activity Score: {github_data.get('activity_score', 0)}",
            f"README Quality Score: {github_data.get('readme_quality_score', 0)}",
            f"Portfolio Feedback: {github_data.get('portfolio_feedback', [])}",
        ]
        context = "\n".join(parts)
        return self.llm_service.extract_structured_data(
            text=context, schema=CareerReport, system_prompt=GITHUB_COACH_PROMPT
        )