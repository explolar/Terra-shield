"""Force deterministic DEMO mode for geo-engine tests (no Earth Engine/network)."""
import os

os.environ["TERRASHIELD_GEE_PROJECT"] = ""
os.environ.pop("TERRASHIELD_GEE_SA_KEY", None)

from terrashield_geo import gee  # noqa: E402

# Reset any prior init so is_live() re-evaluates to demo.
gee._state.initialized = False
gee.init()
