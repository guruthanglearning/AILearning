from __future__ import annotations

import time

import numpy as np
import pandas as pd

from app.agents.base import AgentContext, BaseAgent
from app.schemas.agents import AgentStatus, OptionsOutput


def _mid(row: pd.Series) -> float:
    bid = float(row["bid"]) if "bid" in row.index and pd.notna(row["bid"]) else np.nan
    ask = float(row["ask"]) if "ask" in row.index and pd.notna(row["ask"]) else np.nan
    if pd.notna(bid) and pd.notna(ask) and bid > 0 and ask > 0:
        return (bid + ask) / 2
    lp = row["lastPrice"] if "lastPrice" in row.index else np.nan
    return float(lp) if pd.notna(lp) else 0.0


class OptionsAgent(BaseAgent[OptionsOutput]):
    name = "OptionsAgent"
    output_model = OptionsOutput

    async def run(self, ctx: AgentContext) -> OptionsOutput:
        t0 = time.perf_counter()
        try:
            chain_data = await ctx.provider.get_option_chain(ctx.symbol)
            source = chain_data.get("source", "provider")

            expiries = chain_data.get("expiries") or []
            chosen = chain_data.get("chosen_expiry")
            calls: pd.DataFrame | None = chain_data.get("calls")
            puts: pd.DataFrame | None = chain_data.get("puts")

            if not expiries or chosen is None:
                return OptionsOutput(
                    agent_name=self.name,
                    status=AgentStatus.degraded,
                    provenance=self._prov(source, t0),
                    error_message="No option chain from data source",
                    chain_liquidity_hint="unknown",
                    raw_artifact={},
                )

            # Get spot from quote if not already in chain data
            spot = chain_data.get("spot")
            if spot is None:
                quote = await ctx.provider.get_quote(ctx.symbol)
                spot = quote.get("last_price")

            if spot is None:
                return OptionsOutput(
                    agent_name=self.name,
                    status=AgentStatus.degraded,
                    provenance=self._prov(source, t0),
                    nearest_expiry=chosen,
                    error_message="No spot price",
                    raw_artifact={},
                )

            if calls is None or calls.empty or puts is None or puts.empty:
                return OptionsOutput(
                    agent_name=self.name,
                    status=AgentStatus.degraded,
                    provenance=self._prov(source, t0),
                    nearest_expiry=chosen,
                    error_message="Empty chain",
                    chain_liquidity_hint="unknown",
                    raw_artifact={},
                )

            calls = calls.copy()
            puts = puts.copy()
            calls["dist"] = (calls["strike"] - spot).abs()
            puts["dist"] = (puts["strike"] - spot).abs()
            atm_c = calls.loc[calls["dist"].idxmin()]
            atm_p = puts.loc[puts["dist"].idxmin()]

            iv_c = atm_c["impliedVolatility"] if "impliedVolatility" in atm_c.index else np.nan
            iv_p = atm_p["impliedVolatility"] if "impliedVolatility" in atm_p.index else np.nan
            iv_list = [float(x) for x in (iv_c, iv_p) if pd.notna(x) and float(x) > 0]
            atm_iv = sum(iv_list) / len(iv_list) if iv_list else None

            straddle = _mid(atm_c) + _mid(atm_p)
            imp_move = (straddle / spot * 100) if spot and straddle > 0 else None

            oi_c = int(atm_c["openInterest"]) if "openInterest" in atm_c.index and pd.notna(atm_c["openInterest"]) else 0
            oi_p = int(atm_p["openInterest"]) if "openInterest" in atm_p.index and pd.notna(atm_p["openInterest"]) else 0
            oi = oi_c + oi_p
            liq = "adequate" if oi > 500 else "thin" if oi > 0 else "unknown"

            return OptionsOutput(
                agent_name=self.name,
                status=AgentStatus.complete,
                provenance=self._prov(source, t0),
                atm_iv=atm_iv,
                nearest_expiry=chosen,
                chain_liquidity_hint=liq,
                implied_move_1d_pct=imp_move,
                raw_artifact={"atm_strike_c": float(atm_c["strike"]), "open_interest_sum": oi},
            )
        except Exception as e:
            return OptionsOutput(
                agent_name=self.name,
                status=AgentStatus.failed,
                provenance=self._prov("provider", t0),
                error_message=str(e),
                raw_artifact={},
            )
