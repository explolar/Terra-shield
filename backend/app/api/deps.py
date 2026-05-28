"""Shared FastAPI dependencies."""
from __future__ import annotations

from ..core.auth import make_api_key_auth
from ..core.config import get_settings
from ..core.ratelimit import make_rate_limiter

_settings = get_settings()

# API-key auth (open unless TERRASHIELD_API_KEYS is set).
require_api_key = make_api_key_auth(_settings)

# Shared limiters: a general one for compute endpoints and a stricter one for
# the copilot (it calls the paid LLM, so it's the prime cost/abuse target).
rate_limit = make_rate_limiter(_settings.rate_limit_per_min)
copilot_rate_limit = make_rate_limiter(_settings.copilot_rate_limit_per_min)
