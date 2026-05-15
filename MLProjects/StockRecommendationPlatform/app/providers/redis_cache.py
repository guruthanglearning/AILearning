from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd
import redis.asyncio as aioredis

from app.config import settings
from app.providers.base import MarketDataProvider

log = logging.getLogger(__name__)

_DF_ORIENT = "split"  # compact JSON representation for DataFrames


class RedisCache(MarketDataProvider):
    """
    Cache-first wrapper around any MarketDataProvider.
    Redis failures are silently swallowed — the inner provider is called instead.
    """

    def __init__(self, inner: MarketDataProvider, redis_url: str | None = None) -> None:
        self._inner = inner
        url = redis_url or settings.redis_url
        self._redis: aioredis.Redis = aioredis.from_url(url, decode_responses=True)

    # --- cache helpers ---

    async def _get(self, key: str) -> Any | None:
        try:
            raw = await self._redis.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:
            log.debug("Redis GET miss/error key=%s: %s", key, exc)
            return None

    async def _set(self, key: str, value: Any, ttl: int) -> None:
        try:
            await self._redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as exc:
            log.debug("Redis SET error key=%s: %s", key, exc)

    # --- provider methods ---

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        key = f"quote:{symbol.upper()}"
        cached = await self._get(key)
        if cached:
            return cached
        result = await self._inner.get_quote(symbol)
        await self._set(key, result, settings.quote_stale_seconds)
        return result

    async def get_price_history(self, symbol: str, period: str) -> pd.DataFrame:
        key = f"history:{symbol.upper()}:{period}"
        cached = await self._get(key)
        if cached:
            try:
                return pd.read_json(json.dumps(cached), orient=_DF_ORIENT)
            except Exception:
                pass
        df = await self._inner.get_price_history(symbol, period)
        if not df.empty:
            await self._set(key, json.loads(df.to_json(orient=_DF_ORIENT)), settings.quote_stale_seconds)
        return df

    async def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        key = f"fundamentals:{symbol.upper()}"
        cached = await self._get(key)
        if cached:
            return cached
        result = await self._inner.get_fundamentals(symbol)
        await self._set(key, result, 86_400)  # 24h — fundamentals are slow-changing
        return result

    async def get_option_chain(self, symbol: str) -> dict[str, Any]:
        key = f"chain:{symbol.upper()}"
        cached = await self._get(key)
        if cached:
            # Reconstruct DataFrames from cached dicts
            for col in ("calls", "puts"):
                v = cached.get(col)
                if v is not None:
                    try:
                        cached[col] = pd.read_json(json.dumps(v), orient=_DF_ORIENT)
                    except Exception:
                        cached[col] = None
            return cached

        result = await self._inner.get_option_chain(symbol)

        # Serialise DataFrames before caching
        cacheable = {**result}
        for col in ("calls", "puts"):
            df = cacheable.get(col)
            if isinstance(df, pd.DataFrame) and not df.empty:
                cacheable[col] = json.loads(df.to_json(orient=_DF_ORIENT))
            else:
                cacheable[col] = None

        await self._set(key, cacheable, settings.quote_stale_seconds * 2)
        return result
