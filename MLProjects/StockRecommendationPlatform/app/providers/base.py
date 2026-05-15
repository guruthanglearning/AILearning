from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


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
