from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx
import pandas as pd

from app.providers.base import MarketDataProvider, ProviderError, _infer_market_state

_BASE = "https://api.polygon.io"

_PERIOD_DAYS = {
    "5d": 7,
    "3mo": 92,
    "6mo": 184,
    "1y": 366,
}


def _choose_expiry(expiries: list[str], target_dte: int = 35, min_dte: int = 7) -> str | None:
    """Return the expiry closest to target_dte that is at least min_dte days away."""
    today = date.today()
    best: str | None = None
    best_diff = float("inf")
    for exp in expiries:
        try:
            dte = (date.fromisoformat(exp) - today).days
            if dte < min_dte:
                continue
            diff = abs(dte - target_dte)
            if diff < best_diff:
                best_diff = diff
                best = exp
        except Exception:
            pass
    return best


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
        if r.status_code in (401, 403):
            raise ProviderError(f"Polygon API key invalid or unauthorised ({r.status_code})")
        if r.status_code == 429:
            raise ProviderError("Polygon rate limit exceeded (429)")
        r.raise_for_status()
        return r.json()

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        try:
            snap = await self._get(
                f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            )
            ticker  = snap.get("ticker") or {}
            day     = ticker.get("day") or {}
            prev    = ticker.get("prevDay") or {}
            last_t  = ticker.get("lastTrade") or {}

            # Current price: most-recent trade → day close
            last_price = last_t.get("p") or day.get("c")
            prev_close = prev.get("c")
            change_pct = ticker.get("todaysChangePerc")
            volume     = day.get("v")
            open_price = day.get("o")

            if last_price is None:
                return self._empty_quote()

            return {
                "last_price":     float(last_price),
                "previous_close": float(prev_close) if prev_close is not None else None,
                "day_change_pct": float(change_pct) if change_pct is not None else None,
                "volume":         int(volume) if volume is not None else None,
                "open_price":     float(open_price) if open_price is not None else None,
                "market_state":   _infer_market_state(),
                "source":         self.SOURCE,
            }
        except ProviderError:
            # Polygon snapshot requires a paid plan; fall back to yfinance for quotes
            return await self._yf_quote_fallback(symbol)
        except Exception:
            return self._empty_quote()

    async def _yf_quote_fallback(self, symbol: str) -> dict[str, Any]:
        """Fall back to yfinance when Polygon snapshot endpoint is unavailable."""
        try:
            from app.providers.yfinance_provider import YFinanceProvider
            data = await YFinanceProvider().get_quote(symbol)
            data["source"] = f"{self.SOURCE}+yfinance_quote"
            return data
        except Exception:
            return self._empty_quote()

    def _empty_quote(self) -> dict[str, Any]:
        return {
            "last_price": None, "previous_close": None,
            "day_change_pct": None, "volume": None,
            "open_price": None, "market_state": None,
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
            # Polygon aggs unavailable (bad/free-tier key); fall back to yfinance
            return await self._yf_price_history_fallback(symbol, period)
        except Exception:
            return pd.DataFrame()

    async def _yf_price_history_fallback(self, symbol: str, period: str) -> pd.DataFrame:
        """Fall back to yfinance for OHLCV history when Polygon aggs are unavailable."""
        try:
            from app.providers.yfinance_provider import YFinanceProvider
            return await YFinanceProvider().get_price_history(symbol, period)
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
            # Polygon snapshot requires a paid plan; fall back to yfinance
            return await self._yf_fundamentals_fallback(symbol)
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
            # Step 1: small sample to discover available expiries and underlying spot
            sample = await self._get(
                f"/v3/snapshot/options/{symbol}",
                limit=50,
                sort="expiration_date",
                order="asc",
            )
            all_contracts = sample.get("results") or []
            if not all_contracts:
                return await self._yf_chain_fallback(symbol)

            # Extract spot from underlying_asset field present on every contract
            spot: float | None = None
            ua = all_contracts[0].get("underlying_asset", {})
            if ua.get("price"):
                spot = float(ua["price"])

            # Collect available expiries and choose the one closest to 35 DTE (≥7 DTE)
            expiries = sorted({
                c["details"]["expiration_date"]
                for c in all_contracts
                if c.get("details", {}).get("expiration_date")
            })
            if not expiries:
                return await self._yf_chain_fallback(symbol)

            chosen = _choose_expiry(expiries, target_dte=35, min_dte=7) or expiries[0]

            # Step 2: fetch all contracts for the chosen expiry (up to 500 strikes)
            data = await self._get(
                f"/v3/snapshot/options/{symbol}",
                expiration_date=chosen,
                limit=500,
                sort="strike_price",
                order="asc",
            )
            contracts = data.get("results") or []
            if not contracts:
                return await self._yf_chain_fallback(symbol)

            # Build calls / puts DataFrames with correct Polygon field paths
            rows_c, rows_p = [], []
            for c in contracts:
                det = c.get("details", {})
                if det.get("expiration_date") != chosen:
                    continue
                strike = det.get("strike_price")
                if strike is None:
                    continue

                day = c.get("day", {})
                last_quote = c.get("last_quote", {})
                last_trade = c.get("last_trade", {})
                row = {
                    "strike": float(strike),
                    "bid": last_quote.get("bid"),
                    "ask": last_quote.get("ask"),
                    "lastPrice": (
                        last_trade.get("price")
                        or last_quote.get("midpoint")
                        or day.get("close")
                    ),
                    "impliedVolatility": c.get("implied_volatility"),  # contract-level, not in greeks
                    "openInterest": c.get("open_interest"),
                }
                contract_type = det.get("contract_type")
                if contract_type == "call":
                    rows_c.append(row)
                elif contract_type == "put":
                    rows_p.append(row)

            calls = pd.DataFrame(rows_c) if rows_c else None
            puts = pd.DataFrame(rows_p) if rows_p else None

            # Fall back to yfinance when Polygon IV is unavailable (free tier / after hours)
            has_iv = (
                calls is not None and not calls.empty
                and calls["impliedVolatility"].notna().any()
            )
            if not has_iv:
                return await self._yf_chain_fallback(symbol)

            return {
                "expiries": expiries,
                "chosen_expiry": chosen,
                "spot": spot,
                "calls": calls,
                "puts": puts,
                "atm_iv": None,
                "chain_liquidity_hint": "unknown",
                "implied_move_1d_pct": None,
                "source": self.SOURCE,
            }
        except ProviderError:
            return await self._yf_chain_fallback(symbol)
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
