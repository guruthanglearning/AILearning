"""Observability setup: structured logging, OpenTelemetry tracing, Prometheus metrics."""
from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog
import structlog.contextvars
import structlog.processors
import structlog.stdlib
from opentelemetry import trace
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings

# ---------------------------------------------------------------------------
# Correlation ID — ContextVar threaded through each request and batch task
# ---------------------------------------------------------------------------

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return correlation_id_var.get()


# ---------------------------------------------------------------------------
# Prometheus metric singletons (registered once at import time)
# ---------------------------------------------------------------------------

agent_latency_histogram = Histogram(
    "agent_latency_seconds",
    "Per-agent run latency",
    labelnames=["agent_name", "status"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 45.0, float("inf")),
)

batch_symbols_counter = Counter(
    "batch_job_symbols_total",
    "Batch symbols processed",
    labelnames=["outcome"],
)


# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------

def _inject_correlation_id(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Fallback processor: injects correlation_id from ContextVar if not already bound."""
    cid = correlation_id_var.get()
    if cid and "correlation_id" not in event_dict:
        event_dict["correlation_id"] = cid
    return event_dict


_logging_configured = False


def configure_logging() -> None:
    """Wire structlog to emit newline-delimited JSON on stdout.

    Also bridges stdlib logging (SQLAlchemy, uvicorn, httpx) through the same pipeline
    so all output is uniform JSON.  Safe to call multiple times — idempotent.
    """
    global _logging_configured
    if _logging_configured:
        return
    _logging_configured = True

    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _inject_correlation_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


# ---------------------------------------------------------------------------
# OpenTelemetry
# ---------------------------------------------------------------------------

def configure_otel(service_name: str = "stock-recommendation-platform") -> None:
    """Initialize OTel tracing.  No-op proxy installed when OTEL_ENABLED=false."""
    if not settings.otel_enabled:
        trace.set_tracer_provider(trace.ProxyTracerProvider())
        return

    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    if settings.otel_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint, insecure=True)
    else:
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Always-safe accessor — returns a no-op tracer when OTel is disabled."""
    return trace.get_tracer(name)


# ---------------------------------------------------------------------------
# Prometheus instrumentation factory
# ---------------------------------------------------------------------------

def create_instrumentator() -> Instrumentator:
    return Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=["/healthz", "/metrics"],
    )
