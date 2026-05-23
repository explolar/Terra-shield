"""LLM client for GeoCopilot — Llama via Groq or Ollama.

Providers:
  * ``groq``   — Llama 3.x hosted on Groq (OpenAI-compatible API). Needs an API key.
  * ``ollama`` — local Llama via Ollama (default base http://localhost:11434).
  * ``none``   — no LLM; the copilot uses deterministic templated summaries.

The copilot always works without an LLM; the LLM only upgrades the prose.
"""
from __future__ import annotations

import logging

import httpx

from ..core.config import get_settings

log = logging.getLogger("terrashield.llm")


def provider() -> str:
    return get_settings().llm_provider.lower()


def is_enabled() -> bool:
    s = get_settings()
    p = s.llm_provider.lower()
    if p == "groq":
        return bool(s.llm_api_key)
    if p == "ollama":
        return True
    return False


async def complete(system: str, user: str, temperature: float = 0.2) -> str | None:
    """Return an LLM completion, or None if no provider is configured/available."""
    s = get_settings()
    p = s.llm_provider.lower()
    try:
        if p == "groq":
            return await _groq(s, system, user, temperature)
        if p == "ollama":
            return await _ollama(s, system, user, temperature)
    except Exception as exc:
        log.warning("LLM call failed (%s): %s", p, exc)
        return None
    return None


async def _groq(s, system: str, user: str, temperature: float) -> str | None:
    if not s.llm_api_key:
        return None
    url = (s.llm_base_url or "https://api.groq.com/openai/v1") + "/chat/completions"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {s.llm_api_key}"},
            json={
                "model": s.llm_model,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


async def _ollama(s, system: str, user: str, temperature: float) -> str | None:
    base = s.llm_base_url or "http://localhost:11434"
    model = s.llm_model if "llama" in s.llm_model else "llama3.1"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base}/api/chat",
            json={
                "model": model,
                "stream": False,
                "options": {"temperature": temperature},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
