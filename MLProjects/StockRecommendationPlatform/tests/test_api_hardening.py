"""Phase 6 API hardening offline tests — no DB, no Redis, no live requests."""
from __future__ import annotations

# ---------------------------------------------------------------------------
# CORS origin parsing
# ---------------------------------------------------------------------------

def test_parse_cors_wildcard():
    from app.main import _parse_cors_origins
    assert _parse_cors_origins("*") == ["*"]
    assert _parse_cors_origins("  *  ") == ["*"]


def test_parse_cors_single():
    from app.main import _parse_cors_origins
    assert _parse_cors_origins("https://app.com") == ["https://app.com"]


def test_parse_cors_multiple():
    from app.main import _parse_cors_origins
    result = _parse_cors_origins("https://a.com, https://b.com")
    assert result == ["https://a.com", "https://b.com"]


def test_parse_cors_ignores_empty_segments():
    from app.main import _parse_cors_origins
    result = _parse_cors_origins("https://a.com,,https://b.com")
    assert "" not in result
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------

def test_security_headers_present():
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from app.middleware import SecurityHeadersMiddleware

    async def homepage(request: Request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(SecurityHeadersMiddleware)

    with TestClient(app) as client:
        resp = client.get("/")

    assert "X-Content-Type-Options" in resp.headers
    assert "X-Frame-Options" in resp.headers
    assert "Referrer-Policy" in resp.headers
    assert "X-XSS-Protection" in resp.headers


def test_security_headers_values():
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from app.middleware import SecurityHeadersMiddleware

    async def homepage(request: Request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(SecurityHeadersMiddleware)

    with TestClient(app) as client:
        resp = client.get("/")

    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert resp.headers["X-XSS-Protection"] == "0"


# ---------------------------------------------------------------------------
# Rate-limiter key function
# ---------------------------------------------------------------------------

def _make_request(headers: dict[str, str], client_ip: str = "192.168.1.1"):
    from starlette.requests import Request
    header_list = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": header_list,
        "query_string": b"",
        "client": (client_ip, 8000),
    }
    return Request(scope)


def test_limiter_key_func_api_key():
    from app.limiter import get_api_key_or_ip
    request = _make_request({"X-API-Key": "sk-abcdef1234567890"})
    key = get_api_key_or_ip(request)
    assert key.startswith("apikey:")
    assert "sk-abcde" in key       # first 8 chars of the key value
    assert "1234567890" not in key  # full key not exposed


def test_limiter_key_func_ip_fallback():
    from app.limiter import get_api_key_or_ip
    request = _make_request({}, client_ip="10.0.0.42")
    key = get_api_key_or_ip(request)
    assert "10.0.0.42" in key


# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

def test_rate_limit_config_defaults(monkeypatch):
    for var in ("CORS_ORIGINS", "RATE_LIMIT_DEFAULT", "RATE_LIMIT_ANALYSIS", "RATE_LIMIT_BATCH"):
        monkeypatch.delenv(var, raising=False)
    from app.config import Settings
    s = Settings()
    assert s.cors_origins == "*"
    assert s.rate_limit_default == "200/minute"
    assert s.rate_limit_analysis == "30/minute"
    assert s.rate_limit_batch == "5/minute"
