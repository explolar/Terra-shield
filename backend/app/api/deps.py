"""Shared FastAPI dependencies."""
from __future__ import annotations

from ..core.config import get_settings
from ..core.ratelimit import make_rate_limiter

# One shared limiter instance for all compute endpoints.
rate_limit = make_rate_limiter(get_settings().rate_limit_per_min)
