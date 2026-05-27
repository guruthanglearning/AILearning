from __future__ import annotations

import zoneinfo
from abc import ABC, abstractmethod
from datetime import datetime
from datetime import time as _time
from typing import Any

import pandas as pd


def _infer_market_state() -> str:
    """Best-effort NYSE market state derived from current wall-clock time."""
    try:
        now_et = datetime.now(tz=zoneinfo.ZoneInfo("America/New_York"))
        t = now_et.time()
        if now_et.weekday() >= 5:
            return "CLOSED"
        if _time(4, 0) <= t < _time(9, 30):
            return "PRE"
        if _time(9, 30) <= t < _time(16, 0):
            return "REGULAR"
        if _time(16, 0) <= t < _time(20, 0):
            return "POST"
    except Exception:
        pass
    return "CLOSED"


class ProviderError(Exception):
    """Raised by providers for unrecoverable fetch errors (e.g. 403, 429)."""


class MarketDataProvider(ABC):
    """
    Abstract interface for market data sources.
    All methods are async and must not block the event loop.
    Methods return None fields (never raise) for missing data so agents
    can handle degraded state uniformly. Only raises ProviderError on
    hard failures (invalid API key, rate-limit exhaustion).
    """

    @abstractmethod
    async def get_quote(self, symbol: str) -> dict[str, Any]:
        """
        Returns:
            last_price: float | None
            previous_close: float | None
            day_change_pct: float | None
            volume: int | None
            source: str
        """

    @abstractmethod
    async def get_price_history(self, symbol: str, period: str) -> pd.DataFrame:
        """
        Returns a DataFrame with columns Open, High, Low, Close, Volume
        indexed by date (UTC), sorted ascending.
        Empty DataFrame on failure — callers must check .empty / len().
        period: "5d" | "3mo" | "6mo" | "1y"
        """

    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        """
        Returns:
            company_name: str | None
            sector: str | None
            market_cap: float | None
            pe_ratio: float | None
            forward_pe: float | None
            revenue_growth: float | None
            avg_volume: int | None
            source: str
        """

    @abstractmethod
    async def get_option_chain(self, symbol: str) -> dict[str, Any]:
        """
        Returns:
            expiries: list[str]           # sorted YYYY-MM-DD
            chosen_expiry: str | None
            atm_iv: float | None
            chain_liquidity_hint: str     # "adequate" | "thin" | "unknown"
            implied_move_1d_pct: float | None
            calls: pd.DataFrame | None    # strike, bid, ask, impliedVolatility, openInterest, lastPrice
            puts: pd.DataFrame | None
            source: str
        """
