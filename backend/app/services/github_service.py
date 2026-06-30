import os
import re
from typing import List, Dict, Optional

import httpx
from pydantic import BaseModel

# Simple data models for internal use – they mirror the fields in GitHubData
class RepoInfo(BaseModel):
    name: str
    description: Optional[str]
    html_url: str
    stargazers_count: int
    forks_count: int
    language: Optional[str]

class CommitInfo(BaseModel):
    sha: str
    message: str
    html_url: str
    author_name: Optional[str]
    author_date: Optional[str]

class GitHubService:
    """A thin wrapper around the public GitHub REST API.
    Uses a personal access token if GITHUB_TOKEN is defined in the environment.
    All calls are performed synchronously via ``httpx`` to keep the existing
    ``BaseAgent.run`` signature simple (no async required)."""

    BASE_URL = "https://api.github.com"

    def __init__(self) -> None:
        token = os.getenv("GITHUB_TOKEN")
        self.headers = {"Accept": "application/vnd.github+json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(headers=self.headers, timeout=10.0)

    def _request(self, endpoint: str) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_repo_metadata(self, owner: str, repo: str) -> RepoInfo:
        data = self._request(f"/repos/{owner}/{repo}")
        return RepoInfo(
            name=data.get("name"),
            description=data.get("description"),
            html_url=data.get("html_url"),
            stargazers_count=data.get("stargazers_count", 0),
            forks_count=data.get("forks_count", 0),
            language=data.get("language"),
        )

    def list_repo_files(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """Return a flat list of files (name, path, type) at the given ``path``.
        GitHub returns a list of items; directories are represented as type "dir".
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}" if path else f"/repos/{owner}/{repo}/contents"
        items = self._request(endpoint)
        return items

    def list_recent_commits(self, owner: str, repo: str, count: int = 5) -> List[CommitInfo]:
        data = self._request(f"/repos/{owner}/{repo}/commits?per_page={count}")
        commits: List[CommitInfo] = []
        for item in data:
            commit = item.get("commit", {})
            commits.append(
                CommitInfo(
                    sha=item.get("sha"),
                    message=commit.get("message", ""),
                    html_url=item.get("html_url"),
                    author_name=commit.get("author", {}).get("name"),
                    author_date=commit.get("author", {}).get("date"),
                )
            )
        return commits

    @staticmethod
    def parse_owner_repo(url: str) -> Optional[tuple[str, str]]:
        """Extract ``owner`` and ``repo`` from a GitHub URL.
        Supports URLs like ``https://github.com/owner/repo`` or ``owner/repo``.
        """
        cleaned = url.strip().replace('.git', '')
        pattern = r"(?:https?://github\.com/)?([^/]+)/([^/]+)"
        match = re.match(pattern, cleaned)
        if match:
            return match.group(1), match.group(2)
        return None
