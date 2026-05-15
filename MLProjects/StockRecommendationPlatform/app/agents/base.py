from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from app.schemas.agents import AgentResultBase, AgentStatus, DataProvenance

if TYPE_CHECKING:
    from app.providers.base import MarketDataProvider

T = TypeVar("T", bound=AgentResultBase)


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

    @abstractmethod
    async def run(self, ctx: AgentContext) -> T:
        ...

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
