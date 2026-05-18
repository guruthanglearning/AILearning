"""ASGI middleware: correlation_id injection and security headers."""
from __future__ import annotations

import uuid

import structlog.contextvars
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability import correlation_id_var


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("X-Correlation-ID")
        cid = incoming if _is_valid_uuid(incoming) else str(uuid.uuid4())

        token = correlation_id_var.set(cid)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=cid)
        try:
            response = await call_next(request)
        finally:
            response.headers["X-Correlation-ID"] = cid
            correlation_id_var.reset(token)
            structlog.contextvars.clear_contextvars()
        return response


def _is_valid_uuid(value: str | None) -> bool:
    if not value:
        return False
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security-relevant response headers to every response, including error responses."""

    _HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-XSS-Protection": "0",  # disables legacy IE XSS filter; modern browsers handle XSS natively
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for name, value in self._HEADERS.items():
            response.headers[name] = value
        return response
