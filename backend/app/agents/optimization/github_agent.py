from typing import Optional
from pydantic import BaseModel
from app.services.github_service import GitHubService


class GitHubAnalysisResult(BaseModel):
    username: str
    repos: list[dict]
    languages: dict
    overall_github_score: int
    repo_quality_score: int
    diversity_score: int
    activity_score: int
    readme_quality_score: int
    portfolio_feedback: list[str]
    improvement_suggestions: list[str]


class GitHubAgent:
    """Standalone GitHub analysis agent — not a LangGraph node. Takes a
    repo URL directly rather than pulling it from CareerOSState, since
    GitHub optimization is its own independent flow, not part of the
    resume/JD pipeline."""

    def __init__(self):
        self.service = GitHubService()

    def run(self, github_repo_url: Optional[str]) -> dict:
        if not github_repo_url:
            return {"error": "No repository URL supplied."}

        parsed = self.service.parse_owner_repo(github_repo_url)
        if not parsed:
            return {"error": "Could not parse repository URL. Expected format: https://github.com/owner/repo"}

        owner, repo = parsed
        try:
            meta = self.service.get_repo_metadata(owner, repo)
            commits = self.service.list_recent_commits(owner, repo)

            result = GitHubAnalysisResult(
                username=owner,
                repos=[meta.model_dump()],
                languages={meta.language or "Unknown": meta.stargazers_count},
                overall_github_score=meta.stargazers_count,
                repo_quality_score=meta.forks_count,
                diversity_score=0,
                activity_score=len(commits) * 20,
                readme_quality_score=0,
                portfolio_feedback=[meta.description or ""],
                improvement_suggestions=[],
            )
            return {"data": result.model_dump()}
        except Exception as e:
            return {"error": f"GitHub analysis failed: {e}"}