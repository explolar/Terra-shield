"""Force deterministic DEMO mode for tests, regardless of a local .env.

Tests must not depend on Earth Engine credentials or the network. We clear the
GEE project before the app (and its cached Settings) are imported.
"""
import os

os.environ["TERRASHIELD_GEE_PROJECT"] = ""
os.environ.pop("TERRASHIELD_GEE_SA_KEY", None)
