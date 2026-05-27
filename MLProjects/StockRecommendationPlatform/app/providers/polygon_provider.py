from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx
import pandas as pd

from app.providers.base import MarketDataProvider, ProviderError

_BASE = "https://api.polygon.io"

_PERIOD_DAYS = {
    "5d": 7,
    "3mo": 92,
    "6mo": 184,
    "1y": 366,
}


class PolygonProvider(MarketDataProvider):
    """
    Polygon.io REST client.
    Auth is via ?apiKey=... query param (standard for Polygon REST).
    Raises ProviderError on 403 (bad key) or 429 (rate limit).
    Returns empty/None fields on other errors so agents degrade gracefully.
    """

    SOURCE = "polygon"

    def __init__(self, api_key: str) -> None:
        self._key = api_key
        self._client = httpx.AsyncClient(
            base_url=_BASE,
            timeout=httpx.Timeout(15.0),
            params={"apiKey": api_key},
        )

    async def _get(self, path: str, **params) -> dict:
        try:
            r = await self._client.get(path, params=params)
        except httpx.RequestError as exc:
            raise ProviderError(f"Polygon network error: {exc}") from exc
        if r.status_code == 403:
            raise ProviderError("Polygon API key invalid or unauthorised (403)")
        if r.status_code == 429:
            raise ProviderError("Polygon rate limit exceeded (429)")
        r.raise_for_status()
        return r.json()

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        try:
            # /v2/aggs/ticker/{symbol}/prev works on the free Polygon plan
            prev_data = await self._get(f"/v2/aggs/ticker/{symbol}/prev")
            results = prev_data.get("results") or []
            if not results:
                return {
                    "last_price": None, "previous_close": None,
                    "day_change_pct": None, "volume": None,
                    "source": self.SOURCE,
                }
            r = results[0]
            close = r.get("c")      # closing price (most recent session)
            open_ = r.get("o")      # opening price of that session
            volume = r.get("v")
            change = (
                (close - open_) / open_ * 100
                if close is not None and open_
                else None
            )
            return {
                "last_price": float(close) if close is not None else None,
                "previous_close": float(open_) if open_ is not None else None,
                "day_change_pct": float(change) if change is not None else None,
                "volume": int(volume) if volume is not None else None,
                "source": self.SOURCE,
            }
        except ProviderError:
            raise
        except Exception:
            return {
                "last_price": None,
                "previous_close": None,
                "day_change_pct": None,
                "volume": None,
                "source": self.SOURCE,
            }

    async def get_price_history(self, symbol: str, period: str) -> pd.DataFrame:
        days = _PERIOD_DAYS.get(period, 92)
        to_date = date.today()
        from_date = to_date - timedelta(days=days)
        try:
            data = await self._get(
                f"/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}",
                adjusted="true",
                sort="asc",
                limit=500,
            )
            bars = data.get("results") or []
            if not bars:
                return pd.DataFrame()
            df = pd.DataFrame(bars)
            df["date"] = pd.to_datetime(df["t"], unit="ms", utc=True)
            df = df.set_index("date").rename(
                columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"}
            )
            return df[["Open", "High", "Low", "Close", "Volume"]].sort_index()
        except ProviderError:
            raise
        except Exception:
            return pd.DataFrame()

    async def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        try:
            ref = await self._get(f"/v3/reference/tickers/{symbol}")
            snap = await self._get(
                f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            )
            info = ref.get("results") or {}
            day = (snap.get("ticker") or {}).get("day") or {}
            market_cap = info.get("market_cap")

            # Polygon does not supply PE ratios — merge them from yfinance
            yf_data = await self._yf_fundamentals_fallback(symbol)

            return {
                "company_name": info.get("name") or yf_data.get("company_name"),
                "sector": info.get("sic_description") or yf_data.get("sector"),
                "market_cap": float(market_cap) if market_cap is not None else yf_data.get("market_cap"),
                "pe_ratio": yf_data.get("pe_ratio"),
                "forward_pe": yf_data.get("forward_pe"),
                "revenue_growth": yf_data.get("revenue_growth"),
                "avg_volume": day.get("v") or yf_data.get("avg_volume"),
                "earnings_dates": yf_data.get("earnings_dates"),
                "source": self.SOURCE,
            }
        except ProviderError:
            raise
        except Exception:
            return await self._yf_fundamentals_fallback(symbol)

    async def _yf_fundamentals_fallback(self, symbol: str) -> dict[str, Any]:
        """Fall back to yfinance when Polygon fundamentals endpoint is unavailable."""
        try:
            from app.providers.yfinance_provider import YFinanceProvider
            data = await YFinanceProvider().get_fundamentals(symbol)
            data["source"] = f"{self.SOURCE}+yfinance_fundamentals"
            return data
        except Exception:
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

    async def get_option_chain(self, symbol: str) -> dict[str, Any]:
        try:
            data = await self._get(
                f"/v3/snapshot/options/{symbol}",
                limit=250,
                sort="expiration_date",
                order="asc",
            )
            contracts = data.get("results") or []
            if not contracts:
                return await self._yf_chain_fallback(symbol)

            expiries = sorted({c["details"]["expiration_date"] for c in contracts})
            chosen = expiries[0] if expiries else None

            # Build calls / puts DataFrames in yfinance-compatible column shape
            rows_c, rows_p = [], []
            for c in contracts:
                det = c.get("details", {})
                day = c.get("day", {})
                greeks = c.get("greeks", {})
                if det.get("expiration_date") != chosen:
                    continue
                row = {
                    "strike": det.get("strike_price"),
                    "bid": day.get("close"),
                    "ask": day.get("close"),
                    "lastPrice": day.get("last_quote", {}).get("ask") or day.get("close"),
                    "impliedVolatility": greeks.get("implied_volatility"),
                    "openInterest": c.get("open_interest"),
                }
                if det.get("contract_type") == "call":
                    rows_c.append(row)
                elif det.get("contract_type") == "put":
                    rows_p.append(row)

            calls = pd.DataFrame(rows_c) if rows_c else None
            puts = pd.DataFrame(rows_p) if rows_p else None

            # Polygon greeks are empty outside market hours or on certain plan tiers.
            # Fall back to yfinance (which always computes IV from prices) in that case.
            has_iv = (
                calls is not None and not calls.empty
                and calls["impliedVolatility"].notna().any()
            )
            if not has_iv:
                return await self._yf_chain_fallback(symbol)

            return {
                "expiries": expiries,
                "chosen_expiry": chosen,
                "spot": None,
                "calls": calls,
                "puts": puts,
                "atm_iv": None,         # computed by OptionsAgent after spot is known
                "chain_liquidity_hint": "unknown",
                "implied_move_1d_pct": None,
                "source": self.SOURCE,
            }
        except ProviderError:
            raise
        except Exception:
            return await self._yf_chain_fallback(symbol)

    async def _yf_chain_fallback(self, symbol: str) -> dict[str, Any]:
        """Use yfinance for option chain when Polygon greeks are unavailable."""
        try:
            from app.providers.yfinance_provider import YFinanceProvider
            chain = await YFinanceProvider().get_option_chain(symbol)
            chain["source"] = f"{self.SOURCE}+yfinance_chain"
            return chain
        except Exception:
            return self._empty_chain()

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

    async def aclose(self) -> None:
        await self._client.aclose()
