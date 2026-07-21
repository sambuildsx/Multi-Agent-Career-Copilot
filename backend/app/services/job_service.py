"""Job service — deterministic role inference and query building.

All logic is pure Python (no LLM calls).  This module is imported by the
/jobs route; it should never import from routes or graph modules.
"""

from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Skill → (role, weight) mapping (all keys lowercase)
# Higher weight = stronger signal for that role.
# ---------------------------------------------------------------------------
_ROLE_SIGNALS: Dict[str, Tuple[str, int]] = {
    # Backend
    "fastapi":       ("Backend Developer", 3),
    "django":        ("Backend Developer", 3),
    "spring":        ("Backend Developer", 3),
    "spring boot":   ("Backend Developer", 3),
    "flask":         ("Backend Developer", 2),
    "golang":        ("Backend Developer", 2),
    "go":            ("Backend Developer", 1),
    "rust":          ("Backend Developer", 2),
    "express":       ("Backend Developer", 2),
    # Frontend
    "react":         ("Frontend Developer", 3),
    "next.js":       ("Frontend Developer", 3),
    "nextjs":        ("Frontend Developer", 3),
    "vue":           ("Frontend Developer", 2),
    "vue.js":        ("Frontend Developer", 2),
    "angular":       ("Frontend Developer", 2),
    "typescript":    ("Frontend Developer", 1),
    "svelte":        ("Frontend Developer", 2),
    # Full Stack
    "mongodb":       ("Full Stack Developer", 2),
    "node":          ("Full Stack Developer", 2),
    "node.js":       ("Full Stack Developer", 2),
    "graphql":       ("Full Stack Developer", 2),
    # AI / ML
    "langchain":     ("AI Engineer", 3),
    "langgraph":     ("AI Engineer", 3),
    "rag":           ("AI Engineer", 3),
    "tensorflow":    ("AI Engineer", 3),
    "pytorch":       ("AI Engineer", 3),
    "sklearn":       ("AI Engineer", 2),
    "scikit-learn":  ("AI Engineer", 2),
    "openai":        ("AI Engineer", 2),
    "huggingface":   ("AI Engineer", 2),
    "transformers":  ("AI Engineer", 2),
    "ml":            ("AI Engineer", 1),
    "ai":            ("AI Engineer", 1),
    # Data
    "pandas":        ("Data Scientist", 2),
    "numpy":         ("Data Scientist", 2),
    "spark":         ("Data Scientist", 2),
    "hadoop":        ("Data Scientist", 2),
}

ALL_ROLES = [
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "AI Engineer",
    "Data Scientist",
]


def _score_tokens(tokens: List[str], weight_factor: float) -> Dict[str, float]:
    """Accumulate role scores from a list of raw skill/tech strings."""
    totals: Dict[str, float] = {r: 0.0 for r in ALL_ROLES}
    for tok in tokens:
        key = tok.strip().lower()
        if key in _ROLE_SIGNALS:
            role, pts = _ROLE_SIGNALS[key]
            totals[role] += pts * weight_factor
    return totals


def infer_roles(
    resume_data: Optional[dict],
    jd_data: Optional[dict],
) -> Tuple[str, List[str]]:
    """
    Deterministically infer (primary_role, secondary_roles).

    With JD:  70% JD weight + 30% resume weight
    Without JD: projects 50% + extracted_technologies 30% + skills 20%
    """
    totals: Dict[str, float] = {r: 0.0 for r in ALL_ROLES}

    has_jd = bool(
        jd_data and (
            jd_data.get("required_skills") or
            jd_data.get("technologies") or
            jd_data.get("important_keywords")
        )
    )

    if has_jd:
        jd_tokens = (
            jd_data.get("required_skills", []) +  # type: ignore[union-attr]
            jd_data.get("technologies", []) +       # type: ignore[union-attr]
            jd_data.get("important_keywords", [])   # type: ignore[union-attr]
        )
        for role, score in _score_tokens(jd_tokens, 0.70).items():
            totals[role] += score

    if resume_data:
        # Project stacks — strongest resume signal
        project_tokens: List[str] = []
        for proj in resume_data.get("projects", []):
            project_tokens.extend(proj.get("stack", []))
        proj_w = 0.30 if has_jd else 0.50
        for role, score in _score_tokens(project_tokens, proj_w).items():
            totals[role] += score

        # Extracted technologies
        tech_w = 0.20 if has_jd else 0.30
        for role, score in _score_tokens(
            resume_data.get("extracted_technologies", []), tech_w
        ).items():
            totals[role] += score

        # Skills list (weakest signal)
        skill_w = 0.10 if has_jd else 0.20
        for role, score in _score_tokens(
            resume_data.get("skills", []), skill_w
        ).items():
            totals[role] += score

    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0][0]
    secondary = [r for r, s in ranked[1:] if s > 0][:2]
    return primary, secondary


def top_skills_for_query(
    resume_data: Optional[dict],
    jd_data: Optional[dict],
    max_skills: int = 3,  # Keep low — Adzuna strict AND means >3 skills kills results
) -> List[str]:
    """
    Return up to max_skills skills/technologies to append to the Adzuna query.
    JD technologies take priority; falls back to resume extracted technologies.
    """
    if jd_data:
        jd_techs = jd_data.get("technologies", []) or jd_data.get("required_skills", [])
        if jd_techs:
            return jd_techs[:max_skills]

    if resume_data:
        techs = resume_data.get("extracted_technologies", [])
        skills = resume_data.get("skills", [])
        combined = list(dict.fromkeys(techs + skills))  # deduplicate preserving order
        return combined[:max_skills]

    return []


def build_search_query(role: str, employment_type: str, skills: List[str]) -> str:
    """
    Build a concise Adzuna search query.
    We purposely omit appending raw skills to the free-text query 
    because Adzuna's engine treats space-separated words as a strict AND condition,
    which leads to 0 results for overly specific queries (especially internships).

    Full-time:   "{role}"
    Internship:  "{role} Intern"
    """
    if employment_type == "internship" and "intern" not in role.lower():
        return f"{role} Intern".strip()
    return role.strip()


# ---------------------------------------------------------------------------
# Demo fallback — returned when Adzuna yields 0 results or raises an exception.
# Uses real company career pages so "Apply" links are always live.
# The shape mirrors what _fetch_adzuna() returns so the frontend needs no changes.
# ---------------------------------------------------------------------------
_FALLBACK_JOBS: List[dict] = [
    {
        "title": "Software Engineer – Backend",
        "company": "Razorpay",
        "location": "Bengaluru, India",
        "salary_min": None,
        "salary_max": None,
        "description": (
            "Join Razorpay's engineering team to build highly scalable payment "
            "infrastructure powering millions of businesses across India."
        ),
        "redirect_url": "https://razorpay.com/careers/",
        "created": "",
    },
    {
        "title": "Software Development Engineer – Full Stack",
        "company": "Meesho",
        "location": "Bengaluru, India",
        "salary_min": None,
        "salary_max": None,
        "description": (
            "Work on Meesho's social commerce platform, building features used "
            "by 100M+ entrepreneurs and shoppers across Bharat."
        ),
        "redirect_url": "https://www.meesho.io/jobs",
        "created": "",
    },
    {
        "title": "Software Development Engineer",
        "company": "Flipkart",
        "location": "Bengaluru, India",
        "salary_min": None,
        "salary_max": None,
        "description": (
            "Build and scale systems that serve India's largest e-commerce platform, "
            "handling millions of transactions and catalog items every day."
        ),
        "redirect_url": "https://www.flipkartcareers.com",
        "created": "",
    },
    {
        "title": "Software Engineer – Platform",
        "company": "Zomato",
        "location": "Gurugram, India",
        "salary_min": None,
        "salary_max": None,
        "description": (
            "Help Zomato deliver food to millions of customers by engineering the "
            "core platform that powers ordering, logistics, and restaurant tools."
        ),
        "redirect_url": "https://careers.zomato.com",
        "created": "",
    },
    {
        "title": "Software Engineer – Engineering",
        "company": "Swiggy",
        "location": "Bengaluru, India",
        "salary_min": None,
        "salary_max": None,
        "description": (
            "Join Swiggy's tech team to solve hard engineering problems in "
            "hyperlocal logistics, real-time tracking, and consumer product."
        ),
        "redirect_url": "https://careers.swiggy.com",
        "created": "",
    },
]


def get_fallback_jobs() -> List[dict]:
    """Return the hardcoded demo fallback job list.

    Called by routes/jobs.py when Adzuna returns 0 results (after the primary
    query and its single retry) OR when the Adzuna call itself raises an
    exception.  The returned list has the exact same field shape as the dicts
    produced by _fetch_adzuna(), so the frontend JobCard component renders them
    without any changes.
    """
    return list(_FALLBACK_JOBS)
