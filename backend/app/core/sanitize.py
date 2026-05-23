"""Input cleaning & guardrails for user text that reaches the LLM / external APIs.

Keeps requests well-formed and reduces prompt-injection surface. The copilot is
already grounded (the LLM may only phrase engine-computed numbers), but cleaning
the input is cheap defense-in-depth.
"""
from __future__ import annotations

import re

# Common prompt-injection / jailbreak phrasings to neutralize.
_INJECTION = re.compile(
    r"(ignore (all |the )?(previous|prior|above) (instructions|prompts?)"
    r"|disregard (the |all )?(system|previous)"
    r"|you are now|act as (an?|the)|developer mode|jailbreak"
    r"|reveal (your )?(system )?prompt|print (your )?(system )?prompt"
    r"|api[_ ]?key|secret key|password)",
    re.IGNORECASE,
)

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str, max_len: int = 500) -> str:
    """Normalize whitespace, strip control characters, and cap length."""
    if not text:
        return ""
    text = _CONTROL.sub(" ", str(text))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip()
    return text


def strip_injection(text: str) -> str:
    """Neutralize obvious prompt-injection phrases (replace with a marker)."""
    return _INJECTION.sub("[filtered]", text)


def clean_question(text: str, max_len: int = 500) -> str:
    """Full cleaning pipeline for a user question before it reaches the LLM."""
    return strip_injection(clean_text(text, max_len))


def cap_output(text: str | None, max_len: int = 1200) -> str | None:
    """Guardrail on LLM output: trim, drop code fences, cap length."""
    if not text:
        return text
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|```$", "", text).strip()
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0].rstrip() + "…"
    return text
