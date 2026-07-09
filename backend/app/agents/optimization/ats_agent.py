import re
import logging
from typing import List, Dict, Set
from pydantic import BaseModel
from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, ATSResult, JDData
from app.services.llm_service import LLMService

logger = logging.getLogger("uvicorn")


class ProjectRelevanceExplanation(BaseModel):
    """LLM output for project relevance. Deliberately has NO score field —
    the score is computed deterministically in ATSAgent from stack/tech
    overlap. The LLM only ever explains, never invents the number."""
    explanation: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


PROJECT_RELEVANCE_PROMPT = """You are an expert ATS (Applicant Tracking System) evaluator.
Given the technologies required for the job and the candidate's projects, explain how relevant
their projects are to the job. A deterministic relevance score has already been computed from
technology overlap — do not invent or restate a score. Just explain the reasoning, and list
strengths, weaknesses, and recommendations."""

JD_PROMPT = """You are an expert technical recruiter. Extract the job requirements from the provided job description text.
Identify required skills, preferred skills, core responsibilities, and the general experience level expected.
Extract important keywords that represent core competencies.
"""

TECH_REGEX = re.compile(
    r'\b(python|java|javascript|typescript|c\+\+|golang|rust|react|angular|vue|node\.js|django|'
    r'flask|fastapi|spring|docker|kubernetes|aws|gcp|azure|sql|postgresql|mysql|mongodb|redis|'
    r'graphql|rest api|ci/cd|git|linux)\\b',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Alias normalisation map — maps any surface form to a canonical token.
# Keys are lowercase; values are the canonical lowercase token used for
# all set comparisons.  Add more entries as gaps are found in production.
# ---------------------------------------------------------------------------
_ALIAS_MAP: Dict[str, str] = {
    # React
    "react":        "react",
    "react.js":     "react",
    "reactjs":      "react",
    # Node
    "node":         "node",
    "node.js":      "node",
    "nodejs":       "node",
    # JavaScript
    "js":           "javascript",
    "javascript":   "javascript",
    # TypeScript
    "ts":           "typescript",
    "typescript":   "typescript",
    # MongoDB
    "mongo":        "mongodb",
    "mongodb":      "mongodb",
    # PostgreSQL
    "postgres":     "postgresql",
    "postgresql":   "postgresql",
    # Git / GitHub / GitLab (GitHub presence satisfies a "git" requirement)
    "git":          "git",
    "github":       "git",
    "gitlab":       "git",
    # Python
    "python":       "python",
    "python3":      "python",
    # Docker / containers
    "docker":       "docker",
    # Kubernetes
    "k8s":          "kubernetes",
    "kubernetes":   "kubernetes",
    # AWS
    "aws":          "aws",
    "amazon web services": "aws",
    # GCP
    "gcp":          "gcp",
    "google cloud": "gcp",
    # Azure
    "azure":        "azure",
    # Next.js
    "next":         "next.js",
    "next.js":      "next.js",
    "nextjs":       "next.js",
    # Vue
    "vue":          "vue",
    "vue.js":       "vue",
    "vuejs":        "vue",
    # Angular
    "angular":      "angular",
    "angularjs":    "angular",
    # Express
    "express":      "express",
    "express.js":   "express",
    "expressjs":    "express",
    # FastAPI
    "fastapi":      "fastapi",
    # Django
    "django":       "django",
    # Flask
    "flask":        "flask",
    # Redis
    "redis":        "redis",
    # GraphQL
    "graphql":      "graphql",
    # REST
    "rest":         "rest api",
    "rest api":     "rest api",
    "restful":      "rest api",
    # CI/CD
    "ci/cd":        "ci/cd",
    "cicd":         "ci/cd",
    "github actions": "ci/cd",
    "jenkins":      "ci/cd",
    # SQL / relational
    "sql":          "sql",
    "mysql":        "mysql",
    # Linux
    "linux":        "linux",
    "unix":         "linux",
    # Java
    "java":         "java",
    "spring":       "spring",
    "spring boot":  "spring",
    # Go
    "go":           "golang",
    "golang":       "golang",
}


def _normalize_tech_set(techs: List[str]) -> Set[str]:
    """Return a set of canonical technology tokens for a list of raw strings.
    Unknown tokens are kept as-is (lowercased) so we never silently discard
    anything the LLM extracted."""
    result: Set[str] = set()
    for raw in techs:
        token = raw.strip().lower()
        result.add(_ALIAS_MAP.get(token, token))
    return result


class ATSAgent(BaseAgent):
    """Owns all ATS intelligence, including JD extraction (previously a
    separate JDAgent — merged in here per the simplified architecture).

    Exposes two entry points:
    - extract_jd(jd_text): called by jd_node, runs CONCURRENTLY with
      resume_node so JD parsing doesn't add serial latency on top of
      resume parsing.
    - run(state): called by ats_node once both resume_data and jd_data
      are present in state; does deterministic scoring plus one LLM
      call for human-readable project-relevance explanation text only.
    """

    def __init__(self):
        self.llm_service = LLMService()

    def extract_jd(self, jd_text: str) -> JDData:
        """Parses raw JD text into structured JDData. Called directly by
        jd_node (not via run()) so it can execute in parallel with
        resume_node instead of after it."""
        jd_data = self.llm_service.extract_structured_data(
            text=jd_text,
            schema=JDData,
            system_prompt=JD_PROMPT
        )
        jd_data.raw_text = jd_text

        found_techs = set(jd_data.technologies)
        found_techs_lower = {t.lower() for t in found_techs}

        matches = TECH_REGEX.findall(jd_text)
        for match in matches:
            if match.lower() not in found_techs_lower:
                clean_tech = match.title() if len(match) > 3 else match.upper()
                if clean_tech.upper() == 'CI/CD':
                    clean_tech = 'CI/CD'
                found_techs.add(clean_tech)
                found_techs_lower.add(match.lower())

        jd_data.technologies = list(found_techs)
        return jd_data

    def _compute_project_relevance_score(
        self, projects: List[dict], jd_technologies: List[str]
    ) -> int:
        """Deterministic project relevance: how much of the JD's tech stack
        shows up across the candidate's project stacks. No LLM involved —
        this is the number that feeds the overall ATS score.
        Uses normalized aliases so React / React.js / ReactJS all match."""
        jd_norm = _normalize_tech_set(jd_technologies)
        if not jd_norm:
            return 100
        if not projects:
            return 0

        project_stack_raw: List[str] = []
        for p in projects:
            project_stack_raw.extend(p.get("stack", []))
        project_norm = _normalize_tech_set(project_stack_raw)

        if not project_norm:
            return 20

        matched = project_norm.intersection(jd_norm)
        coverage = len(matched) / len(jd_norm)
        return int(min(100, round(coverage * 100)))

    def run(self, state: CareerOSState) -> dict:
        try:
            resume = state.get("resume_data")
            jd = state.get("jd_data")

            if not resume or not jd:
                raise ValueError("Both Resume and JD data are required for ATS evaluation.")

            explanations = {}

            # ── Keyword match (normalized) ────────────────────────────────
            resume_norm = _normalize_tech_set(resume.skills + resume.extracted_technologies)
            jd_keywords_norm = _normalize_tech_set(jd.important_keywords)

            if jd_keywords_norm:
                kw_matched = resume_norm.intersection(jd_keywords_norm)
                keyword_match_score = int((len(kw_matched) / len(jd_keywords_norm)) * 100)
            else:
                kw_matched = set()
                keyword_match_score = 100

            if not kw_matched and not (jd_keywords_norm - resume_norm):
                logger.warning(
                    "ATS keyword match: 0 matched AND 0 missing after normalization — "
                    "alias map may be incomplete for this JD's tech vocabulary."
                )

            explanations["keyword_match"] = (
                f"Matched {len(kw_matched)} of {len(jd_keywords_norm)} key JD keywords "
                f"after alias normalization (e.g. React.js → react). "
                f"{'Strong keyword alignment.' if keyword_match_score >= 70 else 'Keyword gap detected — add missing terms to Skills section.'}"
            )

            # ── Required skills (normalized) ──────────────────────────────
            jd_req_norm = _normalize_tech_set(jd.required_skills)
            if jd_req_norm:
                req_matched = resume_norm.intersection(jd_req_norm)
                required_skills_match = int((len(req_matched) / len(jd_req_norm)) * 100)
                missing_req = sorted(jd_req_norm - req_matched)
            else:
                req_matched = set()
                required_skills_match = 100
                missing_req = []

            explanations["required_skills"] = (
                f"Matched {len(req_matched)} of {len(jd_req_norm)} required skills. "
                f"Missing: {', '.join(missing_req) if missing_req else 'none'}. "
                f"{'All required skills present — strong match.' if not missing_req else 'Add these skills to resume if applicable.'}"
            )

            # ── Preferred skills (normalized) ─────────────────────────────
            jd_pref_norm = _normalize_tech_set(jd.preferred_skills)
            if jd_pref_norm:
                pref_matched = resume_norm.intersection(jd_pref_norm)
                preferred_skills_match = int((len(pref_matched) / len(jd_pref_norm)) * 100)
            else:
                pref_matched = set()
                preferred_skills_match = 100

            explanations["preferred_skills"] = (
                f"Matched {len(pref_matched)} of {len(jd_pref_norm)} preferred/bonus skills. "
                f"{'Good preferred-skill coverage.' if preferred_skills_match >= 50 else 'Preferred-skill gap — lower priority than required skills.'}"
            )

            # ── Resume completeness ───────────────────────────────────────
            completeness = 0
            if resume.education:   completeness += 25
            if resume.experience:  completeness += 25
            if resume.projects:    completeness += 25
            if resume.skills:      completeness += 25
            completeness_score = completeness
            missing_sections = [
                s for s, present in [
                    ("Education",   bool(resume.education)),
                    ("Experience",  bool(resume.experience)),
                    ("Projects",    bool(resume.projects)),
                    ("Skills",      bool(resume.skills)),
                ] if not present
            ]
            explanations["completeness"] = (
                f"Resume is {completeness}% complete across the four key sections. "
                f"{('Missing: ' + ', '.join(missing_sections) + '.') if missing_sections else 'All key sections are present.'}"
            )

            # ── Project relevance ─────────────────────────────────────────
            project_relevance_score = self._compute_project_relevance_score(
                resume.projects, jd.technologies
            )

            project_text = ""
            for p in resume.projects:
                project_text += f"Project: {p.get('name', 'Unknown')}\nStack: {p.get('stack', [])}\nBullets:\n"
                for b in p.get("bullets", []):
                    project_text += f"- {b}\n"

            llm_input = (
                f"Job Technologies: {', '.join(jd.technologies)}\n\n"
                f"Computed Project Relevance Score: {project_relevance_score}/100\n\n"
                f"Candidate Projects:\n{project_text}"
            )

            relevance_explanation = self.llm_service.extract_structured_data(
                text=llm_input,
                schema=ProjectRelevanceExplanation,
                system_prompt=PROJECT_RELEVANCE_PROMPT,
            )
            explanations["project_relevance"] = (
                f"Project stack relevance score: {project_relevance_score}/100. "
                + relevance_explanation.explanation
            )

            # ── Bullet quality (action verbs + quantification) ────────────
            ACTION_VERBS = {
                "achieved", "built", "optimized", "reduced", "improved", "developed",
                "managed", "led", "created", "designed", "implemented", "increased",
                "decreased", "spearheaded", "delivered", "architected", "engineered",
                "deployed", "orchestrated", "automated", "streamlined",
            }

            all_bullets: List[str] = []
            for exp in resume.experience:
                all_bullets.extend(exp.get("bullets", []))
            for proj in resume.projects:
                all_bullets.extend(proj.get("bullets", []))

            action_verb_hits = 0
            quantification_hits = 0
            for bullet in all_bullets:
                words = set(re.findall(r'\w+', bullet.lower()))
                if any(verb in words for verb in ACTION_VERBS):
                    action_verb_hits += 1
                if re.search(r'\d+', bullet) or re.search(
                    r'\b(one|two|three|four|five|six|seven|eight|nine|ten|percent|%)\b',
                    bullet.lower()
                ):
                    quantification_hits += 1

            total_bullets = max(len(all_bullets), 1)
            action_verb_score   = int((action_verb_hits   / total_bullets) * 100)
            quantification_score = int((quantification_hits / total_bullets) * 100)

            explanations["bullet_quality"] = (
                f"{action_verb_hits}/{total_bullets} bullets use strong action verbs; "
                f"{quantification_hits}/{total_bullets} include metrics or numbers. "
                f"{'Quantification looks solid.' if quantification_score >= 50 else 'Add measurable outcomes to more bullets.'}"
            )

            # ── Overall score ─────────────────────────────────────────────
            # Weights revised so a strong resume with full sections, good
            # keyword overlap, and decent projects scores in the 75-90 range
            # rather than cratering on one missing category.
            raw_score = int(
                (keyword_match_score    * 0.30) +   # most direct JD signal
                (required_skills_match  * 0.25) +   # explicit requirements
                (project_relevance_score * 0.20) +  # evidence of hands-on use
                (completeness_score     * 0.10) +   # structural completeness
                (preferred_skills_match * 0.08) +   # bonus skills
                (action_verb_score      * 0.04) +   # writing quality
                (quantification_score   * 0.03)     # measurability
            )

            # Qualitative floor: a fully-complete resume with all four
            # sections always scores at least 50 regardless of keyword gaps.
            if completeness_score == 100:
                raw_score = max(raw_score, 50)

            overall_score = min(100, raw_score)

            # Produce a human-readable score breakdown summary
            drivers_up   = []
            drivers_down = []
            if keyword_match_score >= 70:
                drivers_up.append(f"keyword overlap ({keyword_match_score}%)")
            else:
                drivers_down.append(f"keyword gap ({keyword_match_score}% matched)")
            if required_skills_match >= 70:
                drivers_up.append(f"required-skill coverage ({required_skills_match}%)")
            else:
                drivers_down.append(f"missing required skills ({100 - required_skills_match}% gap)")
            if project_relevance_score >= 60:
                drivers_up.append(f"project stack alignment ({project_relevance_score}%)")
            else:
                drivers_down.append(f"project stack gap ({project_relevance_score}%)")
            if quantification_score < 40:
                drivers_down.append(f"few quantified bullets ({quantification_score}%)")

            summary_parts = []
            if drivers_up:
                summary_parts.append("Boosted by: " + ", ".join(drivers_up) + ".")
            if drivers_down:
                summary_parts.append("Pulled down by: " + ", ".join(drivers_down) + ".")
            explanations["overall"] = " ".join(summary_parts) or (
                "Weighted average of all ATS sub-scores. Scores computed deterministically."
            )

            ats_result = ATSResult(
                overall_score=overall_score,
                keyword_match_score=keyword_match_score,
                required_skills_match=required_skills_match,
                preferred_skills_match=preferred_skills_match,
                completeness_score=completeness_score,
                project_relevance_score=project_relevance_score,
                action_verb_score=action_verb_score,
                quantification_score=quantification_score,
                strengths=relevance_explanation.strengths,
                weaknesses=relevance_explanation.weaknesses,
                missing_skills=missing_req,
                recommendations=relevance_explanation.recommendations,
                score_explanations=explanations,
            )

            return {
                "ats_result": ats_result,
                "completed_agents": ["ats"],
            }
        except Exception as e:
            logger.error(f"ATSAgent.run failed: {e}", exc_info=True)
            return {
                "errors": [f"ATSAgent failed: {str(e)}"],
                "completed_agents": ["ats"],
            }