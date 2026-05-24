"""Application configuration — single env-driven Settings object."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TERRASHIELD_",
        env_file=(".env", "../.env"),
        extra="ignore",
        case_sensitive=False,
    )

    # --- app ---
    env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    # --- earth engine ---
    gee_project: str | None = None
    gee_sa_key: str | None = None

    # --- performance ---
    cache_ttl_seconds: int = 900
    rate_limit_per_min: int = 60

    # --- GeoCopilot LLM (Llama by default) ---
    # provider: groq | ollama | none
    llm_provider: str = "none"
    llm_api_key: str | None = None
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str | None = None  # e.g. http://localhost:11434 for ollama

    # --- GeoCopilot persona (Terra Lens) ---
    # Override the default forecaster voice live, without a code change.
    copilot_persona: str | None = None

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_prod(self) -> bool:
        return self.env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
