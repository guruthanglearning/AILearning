from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from opentelemetry import trace as _otrace

from app.observability import get_tracer
from app.schemas.agents import AgentResultBase, AgentStatus, DataProvenance

if TYPE_CHECKING:
    from app.providers.base import MarketDataProvider

T = TypeVar("T", bound=AgentResultBase)

_tracer = get_tracer("app.agents.base")


class AgentContext:
    def __init__(
        self,
        symbol: str,
        timeout_s: float = 45.0,
        provider: MarketDataProvider | None = None,
    ) -> None:
        self.symbol = symbol.upper().strip()
        self.timeout_s = timeout_s
        self.provider = provider


class BaseAgent(ABC, Generic[T]):
    name: str
    output_model: ClassVar[type]  # concrete subclasses set this to their output type

    @abstractmethod
    async def run(self, ctx: AgentContext) -> T:
        ...

    async def safe_run(self, ctx: AgentContext) -> T:
        """Run with timeout + OTel span.  Always returns a valid T — never raises."""
        with _tracer.start_as_current_span(
            f"agent.{self.name}",
            attributes={"agent_name": self.name, "symbol": ctx.symbol},
        ) as span:
            t0 = time.perf_counter()
            try:
                result = await asyncio.wait_for(self.run(ctx), timeout=ctx.timeout_s)
                span.set_attribute("agent.status", result.status.value)
                return result
            except asyncio.TimeoutError:
                span.set_attribute("agent.status", "timeout")
                span.set_status(_otrace.StatusCode.ERROR, "timeout")
                return self._fail(
                    self.output_model, t0, "timeout", f"Timed out after {ctx.timeout_s}s"
                )
            except Exception as exc:
                span.set_attribute("agent.status", "error")
                span.record_exception(exc)
                span.set_status(_otrace.StatusCode.ERROR, str(exc))
                return self._fail(self.output_model, t0, "error", str(exc))

    def _prov(self, source: str, t0: float) -> DataProvenance:
        return DataProvenance(source=source, latency_ms=(time.perf_counter() - t0) * 1000)

    def _fail(self, model: type[T], t0: float, source: str, err: str) -> T:
        return model(
            agent_name=self.name,
            status=AgentStatus.failed,
            provenance=self._prov(source, t0),
            error_message=err,
            raw_artifact={},
        )
