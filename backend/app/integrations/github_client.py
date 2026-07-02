from typing import Any

import httpx

from app.core.config import settings


class GitHubAPIClient:
    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-API-Version": "2022-11-28",
        }
        if access_token:
            self._headers["Authorization"] = f"Bearer {access_token}"

    async def get_user_info(self) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user",
                headers=self._headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_repositories(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/repos",
                headers=self._headers,
                params={"per_page": 100, "sort": "updated"},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=self._headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_commits(
        self, owner: str, repo: str, sha: str | None = None
    ) -> list[dict[str, Any]]:
        params = {"per_page": 50}
        if sha:
            params["sha"] = sha
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits",
                headers=self._headers,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_pull_requests(self, owner: str, repo: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls",
                headers=self._headers,
                params={"per_page": 50, "state": "all"},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_issues(self, owner: str, repo: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=self._headers,
                params={"per_page": 50, "state": "all"},
                timeout=10.0,
            )
            response.raise_for_status()
            raw_issues = response.json()
            return [issue for issue in raw_issues if "pull_request" not in issue]

    @staticmethod
    async def exchange_code_for_token(code: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                json={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                err_msg = data.get("error_description", data["error"])
                raise ValueError(f"GitHub OAuth error: {err_msg}")
            return data["access_token"]
