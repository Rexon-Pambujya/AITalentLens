"""
Application configuration.

All runtime configuration is sourced from environment variables (see
`.env.example` at the repo root). Nothing here should ever contain a real
secret - defaults are safe-for-local-dev placeholders only.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- General ---
    PROJECT_NAME: str = "TalentLens AI"
    ENVIRONMENT: Literal["local", "test", "staging", "production"] = "local"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Security ---
    JWT_SECRET: str = "CHANGE_ME_LOCAL_DEV_ONLY"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h, tune down for prod

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+asyncpg://talentlens:talentlens@localhost:5432/talentlens"
    )
    # Sync URL is used by Alembic (asyncpg driver isn't supported there)
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://talentlens:talentlens@localhost:5432/talentlens"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- AI / LLM ---
    LLM_PROVIDER: Literal["openai", "ollama", "groq"] = "ollama"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    GROQ_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    PROMPT_VERSION: str = "v1"
    SCORING_VERSION: str = "v1"

    # --- Object storage ---
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_PATH: str = "./storage"
    S3_ENDPOINT: str | None = None
    S3_BUCKET: str = "talentlens-resumes"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"

    # --- Uploads ---
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_RESUME_MIME_TYPES: list[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
    )

    # --- CORS ---
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"])

    # --- Scoring defaults (section 10 of spec) - overridable per job ---
    DEFAULT_WEIGHT_SKILLS: float = 0.40
    DEFAULT_WEIGHT_SEMANTIC: float = 0.20
    DEFAULT_WEIGHT_EXPERIENCE: float = 0.20
    DEFAULT_WEIGHT_EDUCATION: float = 0.10
    DEFAULT_WEIGHT_PROJECTS: float = 0.10

    RECOMMENDATION_STRONG_MATCH: int = 90
    RECOMMENDATION_GOOD_MATCH: int = 75
    RECOMMENDATION_MODERATE_MATCH: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton - import this, not Settings() directly."""
    return Settings()
