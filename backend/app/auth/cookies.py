from fastapi import Response

from app.core.config import settings


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=refresh_token,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.auth_cookie_name, path="/")
