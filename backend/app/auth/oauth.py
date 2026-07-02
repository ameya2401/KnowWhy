from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status
from pydantic import EmailStr

from app.models.user import AuthProvider


@dataclass(frozen=True)
class OAuthUserInfo:
    provider_id: str
    email: EmailStr
    full_name: str
    profile_picture_url: str | None


class OAuthService:
    async def verify_provider_token(
        self,
        provider: AuthProvider,
        access_token: str,
    ) -> OAuthUserInfo:
        if provider == AuthProvider.GOOGLE:
            return await self._verify_google(access_token)
        if provider == AuthProvider.GITHUB:
            return await self._verify_github(access_token)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported provider.")

    async def _verify_google(self, access_token: str) -> OAuthUserInfo:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo", headers=headers
            )

        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Google OAuth failed."
            )

        payload = response.json()
        email = payload.get("email")
        provider_id = payload.get("sub")
        if not email or not provider_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Google profile is incomplete."
            )

        return OAuthUserInfo(
            provider_id=provider_id,
            email=email,
            full_name=payload.get("name") or email,
            profile_picture_url=payload.get("picture"),
        )

    async def _verify_github(self, access_token: str) -> OAuthUserInfo:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            profile_response = await client.get("https://api.github.com/user", headers=headers)
            email_response = await client.get("https://api.github.com/user/emails", headers=headers)

        if profile_response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub OAuth failed."
            )

        profile = profile_response.json()
        email = profile.get("email") or self._select_primary_github_email(email_response)
        provider_id = profile.get("id")
        if not email or provider_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub profile is incomplete."
            )

        return OAuthUserInfo(
            provider_id=str(provider_id),
            email=email,
            full_name=profile.get("name") or profile.get("login") or email,
            profile_picture_url=profile.get("avatar_url"),
        )

    @staticmethod
    def _select_primary_github_email(response: httpx.Response) -> str | None:
        if response.status_code != status.HTTP_200_OK:
            return None
        emails = response.json()
        for email in emails:
            if email.get("primary") and email.get("verified"):
                return email.get("email")
        return None
