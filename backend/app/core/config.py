from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    DATABASE_URL_SYNC: str = Field(..., alias="DATABASE_URL_SYNC")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
