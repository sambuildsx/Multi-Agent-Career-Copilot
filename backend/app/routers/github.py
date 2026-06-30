from fastapi import APIRouter, HTTPException
from app.agents.github_agent import GitHubAgent
from app.graph.state import CareerOSState

router = APIRouter(prefix="/github", tags=["github"])

@router.get("/")
async def get_github(repo_url: str):
    """Fetch basic GitHub repository information.
    The endpoint expects a full repository URL (e.g. https://github.com/owner/repo).
    It returns the structured ``GitHubData`` model defined in ``app.graph.state``.
    """
    # Build a minimal state containing the repo URL for the agent
    state = CareerOSState(
        job_id="temp",
        user_id="cli",
        resume_pdf_path="",
        jd_text="",
        github_input="",
        github_repo_url=repo_url,
    )
    agent = GitHubAgent()
    result = agent.run(state)
    if result.get("errors"):
        raise HTTPException(status_code=400, detail=result["errors"])
    return result.get("github_data")
