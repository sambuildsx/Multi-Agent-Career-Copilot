from fastapi import APIRouter, HTTPException
from app.agents.github_agent import GitHubAgent

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/")
async def get_github(repo_url: str):
    """Analyze a GitHub repository.

    Expects a full repository URL (e.g. https://github.com/owner/repo).
    Returns the structured analysis result from GitHubAgent.
    """
    agent = GitHubAgent()
    result = agent.run(repo_url)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])

    return result.get("data")
