"""Cache warm-up: proactively fetch quote + option chain for a list of symbols."""
from __future__ import annotations

import asyncio

import structlog

from app.providers.base import MarketDataProvider, ProviderError

log = structlog.get_logger(__name__)

_SEMAPHORE = asyncio.Semaphore(5)


async def _warm_one(symbol: str, provider: MarketDataProvider) -> None:
    async with _SEMAPHORE:
        try:
            await provider.get_quote(symbol)
            await provider.get_option_chain(symbol)
        except ProviderError as exc:
            log.warning("ingest_warm_failed", symbol=symbol, error=str(exc))
        except Exception as exc:
            log.warning("ingest_warm_unexpected", symbol=symbol, error=str(exc))


async def warm_cache(symbols: list[str], provider: MarketDataProvider) -> None:
    """Warm provider cache for each symbol concurrently; errors are logged, never raised."""
    await asyncio.gather(*[_warm_one(s, provider) for s in symbols])
