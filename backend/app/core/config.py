from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KnowWhy API"
    app_version: str = "0.3.0"
    environment: Literal["development", "testing", "production"] = Field(
        default="development",
        alias="ENVIRONMENT",
    )
    database_url: str = Field(
        default="postgresql+asyncpg://knowwhy:knowwhy@localhost:5432/knowwhy",
        alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    validate_external_services_on_startup: bool = Field(
        default=False,
        alias="VALIDATE_EXTERNAL_SERVICES_ON_STARTUP",
    )
    jwt_secret: str = Field(default="development-only-secret", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(
        default=15,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    jwt_refresh_token_expire_days: int = Field(default=30, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    auth_cookie_name: str = "knowwhy_refresh_token"
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    github_client_id: str = Field(default="", alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", alias="GITHUB_CLIENT_SECRET")
    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    notion_client_id: str = Field(default="", alias="NOTION_CLIENT_ID")
    notion_client_secret: str = Field(default="", alias="NOTION_CLIENT_SECRET")
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @computed_field
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
