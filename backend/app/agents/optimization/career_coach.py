import logging
from typing import List, Optional, Any

from app.graph.state import CareerReport, ResumeData, ATSResult, JDData
from app.services.llm_service import LLMService

logger = logging.getLogger("uvicorn")

INTERVIEW_COACH_PROMPT = """You are a career coach summarizing a completed technical interview.
Given the full transcript with technical and communication scores, produce an overall
interview_score (0-100), strengths, weaknesses, recommendations, and a markdown summary."""

RESUME_COACH_PROMPT = """You are a Senior Engineering Hiring Manager reviewing a specific candidate.
You have been handed the raw extracted resume data plus (if a job description was provided) the
ATS scoring results. Your task is to produce a final CareerReport.

STRICT RULES — violating any rule means the report is rejected:
1. Reference every recommendation by the candidate's ACTUAL project names, skill names, or
   resume section names.  Never write "your projects" — name them ("the E-commerce Platform
   project", "the DevOps Starter Kit", etc.).
2. Do NOT recommend Kubernetes, AWS, Docker, CI/CD, or certifications unless they explicitly
   appear in the JD's required/preferred skills or are already present in the candidate's resume.
3. Without a JD: recommend logical NEXT skills derived from the candidate's current stack.
   A Python/FastAPI developer's logical next skill might be async task queues (Celery/RQ),
   not an unrelated cloud platform.
4. With a JD: every recommendation must address a specific gap between the JD's required
   skills and the candidate's skills/projects.
5. Every recommendation must answer: WHAT to change, WHY it matters, and EXPECTED IMPACT.
6. recommendation_cards: produce 3-5 cards (ranked by recruiter impact, highest first).
   Each card:
     current  — one sentence describing what the resume currently says or lacks
     better   — one sentence giving the specific improved version
     impact   — one short phrase (≤10 words) explaining why this matters to a recruiter
7. Populate the markdown field with a concise coaching summary (200-300 words max), using
   the candidate's actual data.  No boilerplate paragraphs.
8. overall_score = ATS overall_score if a JD was provided, else = resume_score from the data.

Return a complete CareerReport dict."""

GITHUB_COACH_PROMPT = """You are a career coach reviewing a candidate's GitHub portfolio analysis.
Given the repository data, language distribution, activity metrics, and quality scores,
produce a career report focused on the candidate's public engineering presence. Identify
what their portfolio communicates to recruiters, what's missing, and how to improve it."""


class CareerCoachAgent:
    """Produces final career reports across all workflows. Each method handles
    a different workflow's data shape, but they all output the same CareerReport
    schema so downstream consumers (routes, frontend) have a consistent contract."""

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
        resume_data: Optional[ResumeData],
        jd_data: Optional[JDData] = None,
        ats_result: Optional[ATSResult] = None,
    ) -> CareerReport:
        """Generate a CareerReport from actual agent output objects.

        Args:
            resume_data: Structured resume object from ResumeAgent.
            jd_data:     Structured JD object from ATSAgent.extract_jd (may be None
                         in Normal-Optimization / no-JD mode).
            ats_result:  ATSResult object from ATSAgent.run (None in no-JD mode).
        """
        parts: List[str] = []

        # ── Resume data section ───────────────────────────────────────────
        if resume_data:
            parts.append("=== CANDIDATE RESUME DATA ===")
            parts.append(f"Skills on resume: {', '.join(resume_data.skills) or 'none listed'}")
            parts.append(f"Extracted technologies: {', '.join(resume_data.extracted_technologies) or 'none'}")

            if resume_data.experience:
                parts.append("Experience:")
                for exp in resume_data.experience:
                    parts.append(
                        f"  - {exp.get('title', '?')} at {exp.get('company', '?')} "
                        f"({exp.get('duration', '?')})"
                    )
                    for b in exp.get("bullets", [])[:4]:  # cap at 4 bullets per role
                        parts.append(f"    • {b}")

            if resume_data.projects:
                parts.append("Projects:")
                for proj in resume_data.projects:
                    stack = ", ".join(proj.get("stack", [])) or "no stack listed"
                    parts.append(f"  - {proj.get('name', 'Unnamed')} [{stack}]")
                    for b in proj.get("bullets", [])[:3]:
                        parts.append(f"    • {b}")

            if resume_data.education:
                parts.append("Education:")
                for edu in resume_data.education:
                    parts.append(
                        f"  - {edu.get('degree', '?')} from {edu.get('institution', '?')} "
                        f"({edu.get('year', '?')})"
                    )

            if resume_data.weak_bullets:
                parts.append(f"Identified weak bullets ({len(resume_data.weak_bullets)}):")
                for wb in resume_data.weak_bullets[:5]:
                    parts.append(f"  - \"{wb}\"")
        else:
            parts.append("=== CANDIDATE RESUME DATA ===\nNo resume data available.")

        # ── JD data section (present only in JD-match mode) ───────────────
        has_jd = jd_data and (jd_data.required_skills or jd_data.technologies)
        if has_jd:
            parts.append("\n=== JOB DESCRIPTION DATA ===")
            parts.append(f"Experience level expected: {jd_data.experience_level or 'not specified'}")
            parts.append(f"Required skills: {', '.join(jd_data.required_skills) or 'none'}")
            parts.append(f"Preferred skills: {', '.join(jd_data.preferred_skills) or 'none'}")
            parts.append(f"Key technologies: {', '.join(jd_data.technologies) or 'none'}")
            parts.append(f"Important keywords: {', '.join(jd_data.important_keywords) or 'none'}")
        else:
            parts.append("\n=== MODE: Normal Resume Optimization (no JD provided) ===")

        # ── ATS result section (JD-match mode only) ───────────────────────
        if ats_result:
            parts.append("\n=== ATS SCORING RESULTS ===")
            parts.append(f"Overall ATS score: {ats_result.overall_score}/100")
            parts.append(f"Keyword match: {ats_result.keyword_match_score}/100")
            parts.append(f"Required-skills match: {ats_result.required_skills_match}/100")
            parts.append(f"Preferred-skills match: {ats_result.preferred_skills_match}/100")
            parts.append(f"Project relevance: {ats_result.project_relevance_score}/100")
            parts.append(f"Quantification score: {ats_result.quantification_score}/100")
            if ats_result.missing_skills:
                parts.append(f"Missing required skills: {', '.join(ats_result.missing_skills)}")
            if ats_result.score_explanations:
                parts.append("Score breakdown:")
                for key, expl in ats_result.score_explanations.items():
                    parts.append(f"  [{key}] {expl}")

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