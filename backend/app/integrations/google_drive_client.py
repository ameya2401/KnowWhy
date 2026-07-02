from typing import Any

import httpx

from app.core.config import settings


class GoogleDriveAPIClient:
    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.base_url = "https://www.googleapis.com/drive/v3"
        self._headers = {}
        if access_token:
            self._headers["Authorization"] = f"Bearer {access_token}"

    async def list_files(
        self,
        q: str = "",
        fields: str = (
            "files(id, name, mimeType, parents, size, owners, webViewLink, "
            "createdTime, modifiedTime, trashed)"
        ),
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List files in Google Drive.
        GET https://www.googleapis.com/drive/v3/files
        """
        params = {
            "pageSize": page_size,
            "fields": fields,
        }
        if q:
            params["q"] = q

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/files",
                headers=self._headers,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json().get("files", [])

    async def get_file_metadata(
        self,
        file_id: str,
        fields: str = (
            "id, name, mimeType, parents, size, owners, webViewLink, "
            "createdTime, modifiedTime, trashed"
        ),
    ) -> dict[str, Any]:
        """
        Get metadata for a specific file.
        GET https://www.googleapis.com/drive/v3/files/{file_id}
        """
        params = {"fields": fields}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/files/{file_id}",
                headers=self._headers,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_file_content(self, file_id: str, mime_type: str) -> str:
        """
        Get the content of a file. Native Google Docs/Sheets/Slides are exported,
        binary/text files are downloaded as media.
        """
        async with httpx.AsyncClient() as client:
            # 1. Native Google Workspace document exports
            if mime_type == "application/vnd.google-apps.document":
                # Export as plain text
                response = await client.get(
                    f"{self.base_url}/files/{file_id}/export",
                    params={"mimeType": "text/plain"},
                    headers=self._headers,
                    timeout=15.0,
                )
                response.raise_for_status()
                return response.text

            elif mime_type == "application/vnd.google-apps.spreadsheet":
                # Export as CSV
                response = await client.get(
                    f"{self.base_url}/files/{file_id}/export",
                    params={"mimeType": "text/csv"},
                    headers=self._headers,
                    timeout=15.0,
                )
                response.raise_for_status()
                return response.text

            elif mime_type == "application/vnd.google-apps.presentation":
                # Export as plain text
                response = await client.get(
                    f"{self.base_url}/files/{file_id}/export",
                    params={"mimeType": "text/plain"},
                    headers=self._headers,
                    timeout=15.0,
                )
                response.raise_for_status()
                return response.text

            # 2. Binary / Text files download
            else:
                # If unsupported binary file other than PDF, return empty
                # or skip content (we store metadata anyway)
                # We also support Text, Markdown, and PDF
                is_supported_text = (
                    "text/" in mime_type
                    or "application/json" in mime_type
                    or "markdown" in mime_type
                )
                is_pdf = mime_type == "application/pdf"

                if not (is_supported_text or is_pdf):
                    return ""

                # Download media
                response = await client.get(
                    f"{self.base_url}/files/{file_id}",
                    params={"alt": "media"},
                    headers=self._headers,
                    timeout=15.0,
                )
                response.raise_for_status()
                if is_pdf:
                    # In real app, run PDF parsing. For MVP, store text/binary
                    # representation or placeholder
                    return f"[PDF Document Content: {len(response.content)} bytes]"
                else:
                    return response.text

    @staticmethod
    async def exchange_code_for_token(code: str, redirect_uri: str) -> dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        POST https://oauth2.googleapis.com/token
        """
        payload = {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                err_msg = data.get("error_description", data["error"])
                raise ValueError(f"Google OAuth error: {err_msg}")
            return data
