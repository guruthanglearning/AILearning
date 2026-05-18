"""Rate-limiter singleton — keyed by API key prefix when present, else by IP."""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings


def get_api_key_or_ip(request: Request) -> str:
    """Rate-limit key: API key prefix (8 chars) when X-API-Key header present, else client IP."""
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        return f"apikey:{api_key[:8]}"  # never include full key in limit storage
    return get_remote_address(request)


_storage_uri = settings.redis_url if settings.use_redis else "memory://"

limiter = Limiter(
    key_func=get_api_key_or_ip,
    default_limits=[settings.rate_limit_default],
    storage_uri=_storage_uri,
)
