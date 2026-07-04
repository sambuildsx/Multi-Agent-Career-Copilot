from app.agents.base_agent import BaseAgent
from app.graph.state import CareerOSState, GitHubData
from app.services.github_service import GitHubService

class GitHubAgent(BaseAgent):
    def __init__(self):
        self.service = GitHubService()

    def run(self, state: CareerOSState) -> dict:
        # Expect the repo URL to be provided in the state (github_repo_url)
        if not getattr(state, "github_repo_url", None):
            return {
                "errors": ["GitHubAgent: no repository URL supplied in state"],
                "completed_agents": ["github"],
            }
        parsed = self.service.parse_owner_repo(state.github_repo_url)
        if not parsed:
            return {
                "errors": ["GitHubAgent: could not parse repository URL"],
                "completed_agents": ["github"],
            }
        owner, repo = parsed
        try:
            meta = self.service.get_repo_metadata(owner, repo)
            files = self.service.list_repo_files(owner, repo)
            commits = self.service.list_recent_commits(owner, repo)
            github_data = GitHubData(
                username=owner,
                repos=[meta.model_dump()],
                pinned_repos=[],
                languages={meta.language or "Unknown": meta.stargazers_count},
                overall_github_score=meta.stargazers_count,
                repo_quality_score=meta.forks_count,
                diversity_score=0,
                activity_score=len(commits) * 20,
                readme_quality_score=0,
                portfolio_feedback=[meta.description or ""],
                improvement_suggestions=[],
            )
            return {
                "github_data": github_data,
                "completed_agents": ["github"],
            }
        except Exception as e:
            return {
                "errors": [f"GitHubAgent failed: {e}"],
                "completed_agents": ["github"],
            }

