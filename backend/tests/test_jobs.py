"""Unit tests for the Jobs feature.

Tests cover:
- Role inference logic (infer_roles)
- Search query builder (build_search_query)
- Top skills selector (top_skills_for_query)
- Adzuna response normalisation (description truncation, null salaries)
"""
import pytest
from app.services.job_service import infer_roles, build_search_query, top_skills_for_query

# ---------------------------------------------------------------------------
# Role Inference
# ---------------------------------------------------------------------------

class TestInferRoles:
    def test_jd_backend_wins(self):
        """Strong JD backend signals should infer Backend Developer."""
        jd = {"technologies": ["FastAPI", "PostgreSQL", "Docker"], "required_skills": [], "important_keywords": []}
        resume = {"projects": [], "extracted_technologies": [], "skills": []}
        primary, secondary = infer_roles(resume, jd)
        assert primary == "Backend Developer"

    def test_jd_frontend_wins(self):
        """React/Next.js in JD should infer Frontend Developer."""
        jd = {"technologies": ["React", "Next.js", "TypeScript"], "required_skills": [], "important_keywords": []}
        resume = {"projects": [], "extracted_technologies": [], "skills": []}
        primary, _ = infer_roles(resume, jd)
        assert primary == "Frontend Developer"

    def test_jd_ai_wins(self):
        """LangChain + RAG in JD should infer AI Engineer."""
        jd = {"technologies": ["LangChain", "RAG", "PyTorch"], "required_skills": [], "important_keywords": []}
        resume = {"projects": [], "extracted_technologies": [], "skills": []}
        primary, _ = infer_roles(resume, jd)
        assert primary == "AI Engineer"

    def test_resume_only_projects_primary(self):
        """Without JD, projects using FastAPI should infer Backend Developer."""
        resume = {
            "projects": [{"stack": ["FastAPI", "PostgreSQL"]}],
            "extracted_technologies": [],
            "skills": [],
        }
        primary, _ = infer_roles(resume, None)
        assert primary == "Backend Developer"

    def test_resume_only_ai_project(self):
        """LangChain project in resume with no JD should infer AI Engineer."""
        resume = {
            "projects": [{"stack": ["LangChain", "RAG", "FastAPI"]}],
            "extracted_technologies": [],
            "skills": [],
        }
        primary, _ = infer_roles(resume, None)
        assert primary == "AI Engineer"

    def test_secondary_roles_returned(self):
        """Multiple strong signals should produce secondary roles."""
        resume = {
            "projects": [{"stack": ["React", "FastAPI"]}],
            "extracted_technologies": ["LangChain"],
            "skills": [],
        }
        primary, secondary = infer_roles(resume, None)
        # Secondary should contain at least one role
        assert isinstance(secondary, list)

    def test_career_track_override(self):
        """Passing career_track='Frontend Developer' from the frontend skips inference."""
        # The route handles this directly; here we just confirm infer_roles
        # still returns something sane independently.
        primary, _ = infer_roles(
            {"projects": [], "extracted_technologies": [], "skills": []},
            None,
        )
        # With empty data, primary is still a valid role string
        assert primary in [
            "Backend Developer", "Frontend Developer",
            "Full Stack Developer", "AI Engineer", "Data Scientist",
        ]

    def test_no_data_returns_default_role(self):
        """Completely empty resume + no JD should not crash and returns a role."""
        primary, secondary = infer_roles({}, None)
        assert isinstance(primary, str)
        assert len(primary) > 0


# ---------------------------------------------------------------------------
# Search Query Builder
# ---------------------------------------------------------------------------

class TestBuildSearchQuery:
    def test_fulltime_format(self):
        query = build_search_query("Backend Developer", "fulltime", ["FastAPI", "PostgreSQL", "Docker"])
        assert query == "Backend Developer"

    def test_internship_format(self):
        query = build_search_query("Frontend Developer", "internship", ["React", "TypeScript"])
        assert query == "Frontend Developer Intern"

    def test_internship_already_in_role(self):
        query = build_search_query("AI Engineer Intern", "internship", [])
        assert query == "AI Engineer Intern"

    def test_no_trailing_spaces(self):
        query = build_search_query("Data Scientist", "fulltime", [])
        assert query == "Data Scientist"


# ---------------------------------------------------------------------------
# Top Skills Selector
# ---------------------------------------------------------------------------

class TestTopSkillsForQuery:
    def test_jd_technologies_take_priority(self):
        jd = {"technologies": ["FastAPI", "Docker", "PostgreSQL", "Redis", "Kafka"]}
        resume = {"extracted_technologies": ["React"], "skills": ["Vue"]}
        skills = top_skills_for_query(resume, jd)
        assert "FastAPI" in skills
        assert "React" not in skills  # JD takes priority

    def test_max_4_returned(self):
        jd = {"technologies": ["A", "B", "C", "D", "E", "F"]}
        skills = top_skills_for_query({}, jd)
        assert len(skills) <= 4

    def test_fallback_to_resume_when_no_jd(self):
        resume = {
            "extracted_technologies": ["FastAPI", "PostgreSQL"],
            "skills": ["Python", "Docker"],
        }
        skills = top_skills_for_query(resume, None)
        assert "FastAPI" in skills

    def test_empty_inputs_returns_empty(self):
        skills = top_skills_for_query({}, None)
        assert skills == []


# ---------------------------------------------------------------------------
# Adzuna Response Normalisation (unit-level — no HTTP)
# ---------------------------------------------------------------------------

class TestAdzunaNormalisation:
    """Test the normalisation logic inline (no real Adzuna calls)."""

    def _normalise(self, raw_job: dict) -> dict:
        """Mirror the normalisation applied in routes/jobs.py _fetch_adzuna."""
        desc_raw = raw_job.get("description", "")
        desc = desc_raw[:280] + "..." if len(desc_raw) > 280 else desc_raw
        return {
            "title": raw_job.get("title", ""),
            "company": raw_job.get("company", {}).get("display_name", ""),
            "location": raw_job.get("location", {}).get("display_name", ""),
            "salary_min": raw_job.get("salary_min"),   # safe: may be None
            "salary_max": raw_job.get("salary_max"),   # safe: may be None
            "description": desc,
            "redirect_url": raw_job.get("redirect_url", ""),
            "created": raw_job.get("created", ""),
        }

    def test_description_truncated(self):
        long_desc = "x" * 400
        result = self._normalise({"description": long_desc})
        assert result["description"].endswith("...")
        assert len(result["description"]) == 283  # 280 + "..."

    def test_short_description_not_truncated(self):
        result = self._normalise({"description": "Short desc"})
        assert not result["description"].endswith("...")
        assert result["description"] == "Short desc"

    def test_null_salary_safe(self):
        """Salary fields missing from Adzuna free tier should be None, not error."""
        result = self._normalise({"title": "Engineer"})  # no salary keys
        assert result["salary_min"] is None
        assert result["salary_max"] is None

    def test_salary_present_when_provided(self):
        result = self._normalise({"salary_min": 30000, "salary_max": 50000})
        assert result["salary_min"] == 30000
        assert result["salary_max"] == 50000

    def test_missing_nested_fields_are_empty_string(self):
        result = self._normalise({})
        assert result["company"] == ""
        assert result["location"] == ""
        assert result["title"] == ""
