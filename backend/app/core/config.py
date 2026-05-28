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
    # Safety net: include the prod frontend so a deploy that forgets to set
    # TERRASHIELD_CORS_ORIGINS still allows the live app (avoids "Backend offline").
    cors_origins: str = (
        "http://localhost:3000,"
        "https://terrashield-frontend-352605264721.asia-south1.run.app"
    )

    # --- earth engine ---
    gee_project: str | None = None
    gee_sa_key: str | None = None

    # --- auth (prototype: shared API key) ---
    # Comma-separated accepted API keys. EMPTY = open API (local dev / tests).
    # Set in production (via Secret Manager) to require an X-API-Key header.
    api_keys: str = ""

    # --- performance / abuse limits ---
    cache_ttl_seconds: int = 3600
    rate_limit_per_min: int = 60          # general compute endpoints, per key/IP
    copilot_rate_limit_per_min: int = 12  # stricter: copilot calls the paid LLM

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
    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}

    @property
    def auth_enabled(self) -> bool:
        return bool(self.api_key_set)

    @property
    def is_prod(self) -> bool:
        return self.env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
