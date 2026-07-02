import base64
from typing import Any

import httpx

from app.core.config import settings


class NotionAPIClient:
    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.base_url = "https://api.notion.com/v1"
        self._headers = {
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        if access_token:
            self._headers["Authorization"] = f"Bearer {access_token}"

    async def search(self, query: str = "", filter_obj: dict | None = None) -> list[dict[str, Any]]:
        """
        Uses search API to find pages and databases.
        POST https://api.notion.com/v1/search
        """
        payload: dict[str, Any] = {
            "query": query,
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time",
            },
        }
        if filter_obj:
            payload["filter"] = filter_obj

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/search",
                headers=self._headers,
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            return results

    async def get_page(self, page_id: str) -> dict[str, Any]:
        """
        Retrieve a page.
        GET https://api.notion.com/v1/pages/{page_id}
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/pages/{page_id}",
                headers=self._headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_database(self, database_id: str) -> dict[str, Any]:
        """
        Retrieve a database.
        GET https://api.notion.com/v1/databases/{database_id}
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/databases/{database_id}",
                headers=self._headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def exchange_code_for_token(code: str, redirect_uri: str | None = None) -> dict[str, Any]:
        """
        Exchanges code for access token.
        POST https://api.notion.com/v1/oauth/token
        """
        client_id = settings.notion_client_id
        client_secret = settings.notion_client_secret
        auth_str = f"{client_id}:{client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json",
        }
        payload = {
            "grant_type": "authorization_code",
            "code": code,
        }
        if redirect_uri:
            payload["redirect_uri"] = redirect_uri

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.notion.com/v1/oauth/token",
                headers=headers,
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                err_msg = data.get("error_description", data["error"])
                raise ValueError(f"Notion OAuth error: {err_msg}")
            return data
