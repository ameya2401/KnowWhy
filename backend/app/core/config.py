from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "KnowWhy API"
    app_version: str = "0.2.0"
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
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    github_client_id: str = Field(default="", alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", alias="GITHUB_CLIENT_SECRET")
    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
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
