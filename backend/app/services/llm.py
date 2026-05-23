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
from ..core.sanitize import cap_output, clean_text

log = logging.getLogger("terrashield.llm")

MAX_TOKENS = 400  # guardrail: keep copilot answers short and bounded


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
    """Return a cleaned, bounded LLM completion, or None if unavailable.

    Guardrails: inputs are length-capped, the response is token- and length-capped
    and stripped of code fences, and one retry covers transient failures. The
    caller (copilot) always has a deterministic fallback if this returns None.
    """
    s = get_settings()
    p = s.llm_provider.lower()
    system = clean_text(system, 2000)
    user = clean_text(user, 4000)

    for attempt in range(2):
        try:
            if p == "groq":
                out = await _groq(s, system, user, temperature)
            elif p == "ollama":
                out = await _ollama(s, system, user, temperature)
            else:
                return None
            return cap_output(out)
        except Exception as exc:
            # Never log the API key; log only the exception type/message.
            log.warning("LLM call failed (%s, attempt %d): %s", p, attempt + 1, exc)
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
                "max_tokens": MAX_TOKENS,
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
                "options": {"temperature": temperature, "num_predict": MAX_TOKENS},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
