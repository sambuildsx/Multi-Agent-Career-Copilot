import logging
from typing import List, Optional, Any

from app.graph.state import CareerReport, ResumeData, ATSResult, JDData
from app.services.llm_service import InterviewLLMService

logger = logging.getLogger("uvicorn")

INTERVIEW_COACH_PROMPT = """You are a career coach summarizing a completed technical interview.
Given the full transcript with technical and communication scores, produce an overall
interview_score (0-100), strengths, weaknesses, recommendations, and a markdown summary."""

RESUME_COACH_PROMPT = """You are a Senior Engineering Hiring Manager reviewing a specific candidate.

You are being handed a ResumeReview that has ALREADY been computed by a specialist review
agent — it already contains section scores, a heatmap, identified strengths/weaknesses,
rewritten bullets, project reviews, and priority actions. Your job is to SYNTHESIZE this
into a final recruiter-facing report, not rediscover it from scratch. Do not re-derive
section scores or re-identify weak bullets — they're already given to you as ground truth.

You may also be given JD data and ATS results if the candidate is being matched against a
specific job. If those are absent, this is Normal Optimization mode — there is no job to
match against.

STRICT RULES — violating any rule means the report is rejected:
1. Reference every recommendation by the candidate's ACTUAL project names, skill names, or
   resume section names — pull these directly from the ResumeReview and resume data you were
   given. Never write "your projects" — name them.
2. Do NOT recommend Kubernetes, AWS, Docker, CI/CD, or certifications unless they explicitly
   appear in the JD's required/preferred skills, or are already present in the candidate's
   resume, or are a direct logical extension already implied by the ResumeReview's priority
   actions.
3. missing_skills must ONLY be populated when ATS results are present (i.e. a JD was
   provided). In Normal Optimization mode (no JD, no ATS result), missing_skills must be an
   empty list — there is nothing to be "missing" against without a target job. Suggested
   next skills belong in recommendations/learning_roadmap instead, framed as growth, not gaps.
4. With a JD: every recommendation must address a specific gap between the JD's required
   skills and the candidate's skills/projects, using the ATS result's missing_skills as the
   source of truth for what's actually missing.
5. Every recommendation must answer: WHAT to change, WHY it matters, and EXPECTED IMPACT.
6. recommendation_cards: produce 3-5 cards (ranked by recruiter impact, highest first).
   Prefer pulling directly from the ResumeReview's priority_actions and rewritten_bullets
   where they exist — don't invent new ones when good ones are already computed.
   Each card:
     current  — one sentence describing what the resume currently says or lacks
     better   — one sentence giving the specific improved version
     impact   — one short phrase (≤10 words) explaining why this matters to a recruiter
7. Populate the markdown field with a concise coaching summary (200-300 words max), using
   the candidate's actual data and the ResumeReview's heatmap/strengths/weaknesses as your
   source material. No boilerplate paragraphs.
8. overall_score = ATS overall_score if a JD was provided, else = the ResumeReview's
   overall_score (the deterministic score already computed — do not invent a different one).

Return a complete CareerReport dict."""


class CareerCoachAgent:
    """Produces final career reports across all workflows. Each method handles
    a different workflow's data shape, but they all output the same CareerReport
    schema so downstream consumers (routes, frontend) have a consistent contract."""

    def __init__(self):
        self.llm_service = InterviewLLMService()

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
        resume_review: Optional[Any] = None,
        jd_data: Optional[JDData] = None,
        ats_result: Optional[ATSResult] = None,
    ) -> CareerReport:
        """Generate a CareerReport, synthesizing the already-computed ResumeReview
        rather than re-deriving section quality from raw resume_data alone.

        Args:
            resume_data:   Structured resume object from ResumeAgent.
            resume_review: The ResumeReview object ResumeAgent already computed —
                            section scores, heatmap, project reviews, priority
                            actions, rewritten bullets. Must be synthesized, not
                            rediscovered.
            jd_data:       Structured JD object (may be None in Normal-Opt mode).
            ats_result:    ATSResult object (None in no-JD mode).
        """
        parts: List[str] = []

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

            if resume_data.projects:
                parts.append("Projects:")
                for proj in resume_data.projects:
                    stack = ", ".join(proj.get("stack", [])) or "no stack listed"
                    parts.append(f"  - {proj.get('name', 'Unnamed')} [{stack}]")
        else:
            parts.append("=== CANDIDATE RESUME DATA ===\nNo resume data available.")

        # ── Already-computed ResumeReview — this is the key addition ──────
        if resume_review:
            parts.append("\n=== RESUME REVIEW (already computed — synthesize, do not redo) ===")
            parts.append(f"Deterministic overall score: {resume_review.overall_score}/100")
            parts.append(f"Section scores: {resume_review.section_scores.model_dump()}")
            parts.append(f"Heatmap: {resume_review.resume_heatmap}")

            if resume_review.strengths:
                parts.append("Identified strengths:")
                for s in resume_review.strengths:
                    parts.append(f"  - {s.recommendation} (why: {s.why})")

            if resume_review.weaknesses:
                parts.append("Identified weaknesses:")
                for w in resume_review.weaknesses:
                    parts.append(f"  - {w.recommendation} (why: {w.why})")

            if resume_review.project_reviews:
                parts.append("Project reviews:")
                for pr in resume_review.project_reviews:
                    parts.append(f"  - {pr.project_name}: score {pr.score}/100 — {pr.review}")

            if resume_review.priority_actions:
                parts.append("Priority actions (already ranked — prefer these for recommendation_cards):")
                for pa in resume_review.priority_actions:
                    parts.append(f"  - [{pa.priority}] {pa.action} (reason: {pa.reason})")

            if resume_review.duplicate_skills:
                parts.append(f"Duplicate skills flagged: {', '.join(resume_review.duplicate_skills)}")
            if resume_review.missing_sections:
                parts.append(f"Missing sections flagged: {', '.join(resume_review.missing_sections)}")
        else:
            parts.append("\n=== RESUME REVIEW ===\nNot available — synthesize from raw resume data only.")

        has_jd = jd_data and (jd_data.required_skills or jd_data.technologies)
        if has_jd:
            parts.append("\n=== JOB DESCRIPTION DATA ===")
            parts.append(f"Experience level expected: {jd_data.experience_level or 'not specified'}")
            parts.append(f"Required skills: {', '.join(jd_data.required_skills) or 'none'}")
            parts.append(f"Preferred skills: {', '.join(jd_data.preferred_skills) or 'none'}")
            parts.append(f"Key technologies: {', '.join(jd_data.technologies) or 'none'}")
        else:
            parts.append("\n=== MODE: Normal Resume Optimization (no JD provided) ===")
            parts.append("missing_skills MUST be an empty list in this mode.")

        if ats_result:
            parts.append("\n=== ATS SCORING RESULTS ===")
            parts.append(f"Overall ATS score: {ats_result.overall_score}/100")
            parts.append(f"Required-skills match: {ats_result.required_skills_match}/100")
            if ats_result.missing_skills:
                parts.append(f"Missing required skills: {', '.join(ats_result.missing_skills)}")

        context = "\n".join(parts)
        report = self.llm_service.extract_structured_data(
            text=context, schema=CareerReport, system_prompt=RESUME_COACH_PROMPT
        )
        if isinstance(report, dict):
            report["has_jd_analysis"] = ats_result is not None
        else:
            setattr(report, "has_jd_analysis", ats_result is not None)
        return report