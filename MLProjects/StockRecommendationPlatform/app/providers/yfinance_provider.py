from __future__ import annotations

import asyncio
from datetime import datetime
from functools import partial
from typing import Any

import pandas as pd
import yfinance as yf

from app.providers.base import MarketDataProvider

_PERIOD_MAP = {
    "5d": "5d",
    "3mo": "3mo",
    "6mo": "6mo",
    "1y": "1y",
}


def _run_sync(fn, *args):
    """Run a blocking yfinance call in a thread pool so we don't block the event loop."""
    return asyncio.get_event_loop().run_in_executor(None, partial(fn, *args))


class YFinanceProvider(MarketDataProvider):
    """yfinance-backed provider — used for local dev and as fallback when POLYGON_API_KEY is unset."""

    SOURCE = "yfinance"

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        def _fetch():
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            return hist

        try:
            hist = await _run_sync(lambda: yf.Ticker(symbol).history(period="5d"))
            if hist is None or hist.empty:
                return self._empty_quote()
            last = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
            change = (last - prev) / prev * 100 if prev else None
            vol = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else None
            return {
                "last_price": last,
                "previous_close": prev,
                "day_change_pct": change,
                "volume": vol,
                "source": self.SOURCE,
            }
        except Exception:
            return self._empty_quote()

    async def get_price_history(self, symbol: str, period: str) -> pd.DataFrame:
        yf_period = _PERIOD_MAP.get(period, period)
        try:
            hist = await _run_sync(lambda: yf.Ticker(symbol).history(period=yf_period))
            if hist is None or hist.empty:
                return pd.DataFrame()
            return hist[["Open", "High", "Low", "Close", "Volume"]].sort_index()
        except Exception:
            return pd.DataFrame()

    async def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        try:
            info = await _run_sync(lambda: yf.Ticker(symbol).info) or {}
            return {
                "company_name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "market_cap": float(m) if (m := info.get("marketCap")) is not None else None,
                "pe_ratio": float(p) if (p := info.get("trailingPE")) is not None else None,
                "forward_pe": float(p) if (p := info.get("forwardPE")) is not None else None,
                "revenue_growth": float(r) if (r := info.get("revenueGrowth")) is not None else None,
                "avg_volume": info.get("averageVolume10days") or info.get("averageVolume"),
                "earnings_dates": None,
                "source": self.SOURCE,
            }
        except Exception:
            return self._empty_fundamentals()

    async def get_option_chain(self, symbol: str) -> dict[str, Any]:
        try:
            t = yf.Ticker(symbol)
            expiries = await _run_sync(lambda: t.options)
            if not expiries:
                return self._empty_chain()

            chosen = expiries[0]
            for e in expiries[:12]:
                try:
                    if (datetime.strptime(e, "%Y-%m-%d") - datetime.utcnow()).days >= 5:
                        chosen = e
                        break
                except ValueError:
                    chosen = e
                    break

            chain = await _run_sync(lambda: t.option_chain(chosen))
            hist = await _run_sync(lambda: t.history(period="5d"))
            spot = float(hist["Close"].iloc[-1]) if not hist.empty else None

            return {
                "expiries": list(expiries),
                "chosen_expiry": chosen,
                "spot": spot,
                "calls": chain.calls.copy() if chain else None,
                "puts": chain.puts.copy() if chain else None,
                "source": self.SOURCE,
                # atm_iv / chain_liquidity_hint / implied_move computed by OptionsAgent
                "atm_iv": None,
                "chain_liquidity_hint": "unknown",
                "implied_move_1d_pct": None,
            }
        except Exception:
            return self._empty_chain()

    # --- helpers ---

    def _empty_quote(self) -> dict[str, Any]:
        return {
            "last_price": None,
            "previous_close": None,
            "day_change_pct": None,
            "volume": None,
            "source": self.SOURCE,
        }

    def _empty_fundamentals(self) -> dict[str, Any]:
        return {
            "company_name": None,
            "sector": None,
            "market_cap": None,
            "pe_ratio": None,
            "forward_pe": None,
            "revenue_growth": None,
            "avg_volume": None,
            "earnings_dates": None,
            "source": self.SOURCE,
        }

    def _empty_chain(self) -> dict[str, Any]:
        return {
            "expiries": [],
            "chosen_expiry": None,
            "spot": None,
            "calls": None,
            "puts": None,
            "atm_iv": None,
            "chain_liquidity_hint": "unknown",
            "implied_move_1d_pct": None,
            "source": self.SOURCE,
        }
