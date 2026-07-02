from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.cookies import clear_refresh_cookie, set_refresh_cookie
from app.auth.schemas import AuthTokenResponse, OAuthTokenRequest, RefreshTokenRequest
from app.auth.service import AuthService
from app.core.config import settings
from app.database.session import get_database_session
from app.models.user import AuthProvider

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=AuthTokenResponse)
async def login_google(
    payload: OAuthTokenRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> AuthTokenResponse:
    service = AuthService(session)
    auth_response, refresh_token = await service.authenticate_oauth_with_refresh(
        AuthProvider.GOOGLE,
        payload.access_token,
    )
    set_refresh_cookie(response, refresh_token)
    return auth_response


@router.post("/github", response_model=AuthTokenResponse)
async def login_github(
    payload: OAuthTokenRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> AuthTokenResponse:
    service = AuthService(session)
    auth_response, refresh_token = await service.authenticate_oauth_with_refresh(
        AuthProvider.GITHUB,
        payload.access_token,
    )
    set_refresh_cookie(response, refresh_token)
    return auth_response


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    refresh_cookie: Annotated[str | None, Cookie(alias=settings.auth_cookie_name)] = None,
) -> AuthTokenResponse:
    refresh_value = payload.refresh_token or refresh_cookie
    service = AuthService(session)
    auth_response, refresh_token = await service.refresh_with_token(refresh_value)
    set_refresh_cookie(response, refresh_token)
    return auth_response


@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_database_session)],
    refresh_cookie: Annotated[str | None, Cookie(alias=settings.auth_cookie_name)] = None,
) -> dict[str, bool]:
    await AuthService(session).logout(payload.refresh_token or refresh_cookie)
    clear_refresh_cookie(response)
    return {"success": True}
