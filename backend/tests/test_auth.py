"""API-key auth + rate-limit keying."""
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import deps
from app.core.auth import make_api_key_auth
from app.core.config import Settings
from app.core.ratelimit import client_key
from app.main import app

AOI = {"type": "bbox", "bbox": [73.9, 17.6, 74.3, 18.0]}


class _Req:
    def __init__(self, headers=None, client_host=None):
        self.headers = headers or {}
        self.client = type("C", (), {"host": client_host})() if client_host else None


def test_auth_open_when_no_keys_configured():
    dep = make_api_key_auth(Settings(api_keys=""))
    assert dep(x_api_key=None) is None  # anonymous allowed in open mode


def test_auth_enforced_when_keys_set():
    dep = make_api_key_auth(Settings(api_keys="alpha, beta"))
    assert dep(x_api_key="beta") == "beta"
    for bad in (None, "", "wrong"):
        try:
            dep(x_api_key=bad)
            assert False, f"expected 401 for {bad!r}"
        except HTTPException as exc:
            assert exc.status_code == 401


def test_rate_limit_key_prefers_api_key_then_xff():
    r = _Req(headers={"x-forwarded-for": "1.2.3.4, 5.6.7.8"}, client_host="10.0.0.1")
    assert client_key(r, "abc") == "key:abc"          # API key wins
    assert client_key(r, None) == "ip:1.2.3.4"        # first XFF hop, not the proxy
    assert client_key(_Req(client_host="10.0.0.1"), None) == "ip:10.0.0.1"  # peer fallback


def test_protected_routes_require_key_when_enforced():
    app.dependency_overrides[deps.require_api_key] = make_api_key_auth(
        Settings(api_keys="secret123"))
    try:
        c = TestClient(app)
        assert c.post("/api/v1/flood/susceptibility", json={"aoi": AOI}).status_code == 401
        ok = c.post("/api/v1/flood/susceptibility", json={"aoi": AOI},
                    headers={"X-API-Key": "secret123"})
        assert ok.status_code == 200
        assert c.get("/api/v1/health").status_code == 200  # health stays open
    finally:
        app.dependency_overrides.clear()
