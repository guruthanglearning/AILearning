"""
Tests for the three options robustness changes made in 2026-06:
  1. OptionsGuidance.coerce_str_to_list — Pydantic validator for profit_targets_scenario
     and rationale_codes that coerces a bare Claude string into a list.
  2. OptionsAgent concurrent-safety — reset_index(drop=True) + pd.to_numeric coercion
     guards against object-dtype strikes and NaN index labels under concurrent yfinance load.
  3. yfinance _run_sync semaphore — limits concurrent yfinance fetches to 3 to avoid
     Yahoo Finance rate-limiting when all 7 agents run in parallel.
"""
from __future__ import annotations

import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pandas as pd
import pytest

from app.agents.base import AgentContext
from app.agents.options import OptionsAgent
from app.providers.base import MarketDataProvider
from app.schemas.agents import AgentStatus, OptionsGuidance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_provider() -> MagicMock:
    return MagicMock(spec=MarketDataProvider)


def _ctx(symbol: str = "TSLA") -> AgentContext:
    return AgentContext(symbol=symbol, timeout_s=30.0, provider=_fake_provider())


def _chain(calls: pd.DataFrame, puts: pd.DataFrame, spot: float = 150.0) -> dict:
    return {
        "expiries": ["2026-07-18"],
        "chosen_expiry": "2026-07-18",
        "spot": spot,
        "calls": calls,
        "puts": puts,
        "source": "polygon+yfinance_chain",
    }


def _standard_df(spot: float = 150.0) -> pd.DataFrame:
    strikes = [140.0, 145.0, 150.0, 155.0, 160.0]
    return pd.DataFrame({
        "strike": strikes,
        "bid": [10.0, 7.0, 4.5, 2.0, 0.8],
        "ask": [10.5, 7.5, 5.0, 2.5, 1.2],
        "lastPrice": [10.2, 7.2, 4.8, 2.2, 1.0],
        "impliedVolatility": [0.35, 0.32, 0.30, 0.31, 0.34],
        "openInterest": [500, 1000, 2000, 1500, 800],
    })


def _object_dtype_df() -> pd.DataFrame:
    """Strikes as strings — happens when yfinance returns mixed-type rows."""
    df = _standard_df()
    df["strike"] = df["strike"].astype(str)
    return df


def _nan_strike_df() -> pd.DataFrame:
    """Some strikes are NaN — happens when yfinance merges incomplete chain rows."""
    df = _standard_df()
    df.loc[1, "strike"] = float("nan")
    df.loc[3, "strike"] = float("nan")
    return df


def _nonstandard_index_df() -> pd.DataFrame:
    """Non-sequential integer index — happens after DataFrame slicing/filtering."""
    df = _standard_df()
    df.index = [10, 20, 30, 40, 50]
    return df


# ---------------------------------------------------------------------------
# 1. OptionsGuidance.coerce_str_to_list validator
# ---------------------------------------------------------------------------

class TestOptionsGuidanceCoerceValidator:

    def test_profit_targets_coerces_string_to_single_item_list(self):
        og = OptionsGuidance(profit_targets_scenario="Take profit at 50% of max spread.")
        assert og.profit_targets_scenario == ["Take profit at 50% of max spread."]

    def test_profit_targets_accepts_valid_list(self):
        items = ["Take profit at 50%.", "Close at 60%."]
        og = OptionsGuidance(profit_targets_scenario=items)
        assert og.profit_targets_scenario == items

    def test_profit_targets_empty_string_gives_empty_list(self):
        og = OptionsGuidance(profit_targets_scenario="")
        assert og.profit_targets_scenario == []

    def test_profit_targets_whitespace_only_string_gives_empty_list(self):
        og = OptionsGuidance(profit_targets_scenario="   ")
        assert og.profit_targets_scenario == []

    def test_profit_targets_none_gives_empty_list(self):
        og = OptionsGuidance(profit_targets_scenario=None)
        assert og.profit_targets_scenario == []

    def test_profit_targets_default_is_empty_list(self):
        og = OptionsGuidance()
        assert og.profit_targets_scenario == []

    def test_rationale_codes_coerces_string_to_single_item_list(self):
        og = OptionsGuidance(rationale_codes="iv_elevated")
        assert og.rationale_codes == ["iv_elevated"]

    def test_rationale_codes_accepts_valid_list(self):
        codes = ["iv_elevated", "earnings_window"]
        og = OptionsGuidance(rationale_codes=codes)
        assert og.rationale_codes == codes

    def test_rationale_codes_empty_string_gives_empty_list(self):
        og = OptionsGuidance(rationale_codes="")
        assert og.rationale_codes == []

    def test_rationale_codes_none_gives_empty_list(self):
        og = OptionsGuidance(rationale_codes=None)
        assert og.rationale_codes == []

    def test_rationale_codes_default_is_empty_list(self):
        og = OptionsGuidance()
        assert og.rationale_codes == []

    def test_both_fields_coerced_simultaneously(self):
        og = OptionsGuidance(
            profit_targets_scenario="Scale out at first target.",
            rationale_codes="directional_bearish",
        )
        assert og.profit_targets_scenario == ["Scale out at first target."]
        assert og.rationale_codes == ["directional_bearish"]


# ---------------------------------------------------------------------------
# 2. OptionsAgent concurrent-safety — object dtype, NaN strikes, bad index
# ---------------------------------------------------------------------------

class TestOptionsAgentConcurrentSafety:

    @pytest.mark.asyncio
    async def test_object_dtype_strikes_complete(self):
        """Regression: strikes returned as strings should be coerced to float."""
        prov = _fake_provider()
        prov.get_option_chain = AsyncMock(
            return_value=_chain(_object_dtype_df(), _object_dtype_df())
        )
        result = await OptionsAgent().run(AgentContext(symbol="TSLA", timeout_s=30.0, provider=prov))
        assert result.status == AgentStatus.complete
        assert result.atm_iv is not None

    @pytest.mark.asyncio
    async def test_object_dtype_strikes_correct_atm_selected(self):
        """ATM strike should be the one closest to spot=150, not garbled by str comparison."""
        prov = _fake_provider()
        prov.get_option_chain = AsyncMock(
            return_value=_chain(_object_dtype_df(), _object_dtype_df(), spot=150.0)
        )
        result = await OptionsAgent().run(AgentContext(symbol="TSLA", timeout_s=30.0, provider=prov))
        assert result.status == AgentStatus.complete
        assert result.raw_artifact.get("atm_strike_c") == pytest.approx(150.0)

    @pytest.mark.asyncio
    async def test_nan_strikes_are_dropped_and_agent_completes(self):
        """NaN strikes should be silently dropped; remaining valid strikes suffice."""
        prov = _fake_provider()
        prov.get_option_chain = AsyncMock(
            return_value=_chain(_nan_strike_df(), _nan_strike_df(), spot=150.0)
        )
        result = await OptionsAgent().run(AgentContext(symbol="TSLA", timeout_s=30.0, provider=prov))
        assert result.status == AgentStatus.complete

    @pytest.mark.asyncio
    async def test_all_nan_strikes_degrades(self):
        """If every strike is NaN after coercion, agent should degrade gracefully."""
        all_nan = pd.DataFrame({
            "strike": [float("nan")] * 3,
            "bid": [1.0] * 3,
            "ask": [1.5] * 3,
            "lastPrice": [1.2] * 3,
            "impliedVolatility": [0.30] * 3,
            "openInterest": [100] * 3,
        })
        prov = _fake_provider()
        prov.get_option_chain = AsyncMock(
            return_value=_chain(all_nan, all_nan, spot=150.0)
        )
        result = await OptionsAgent().run(AgentContext(symbol="TSLA", timeout_s=30.0, provider=prov))
        assert result.status == AgentStatus.degraded

    @pytest.mark.asyncio
    async def test_nonstandard_index_does_not_crash_idxmin(self):
        """Non-sequential index (e.g. [10,20,30,40,50]) must not cause idxmin() errors."""
        prov = _fake_provider()
        prov.get_option_chain = AsyncMock(
            return_value=_chain(_nonstandard_index_df(), _nonstandard_index_df(), spot=150.0)
        )
        result = await OptionsAgent().run(AgentContext(symbol="TSLA", timeout_s=30.0, provider=prov))
        assert result.status == AgentStatus.complete

    @pytest.mark.asyncio
    async def test_mixed_type_strikes_after_concat(self):
        """Simulate a DataFrame where some strikes are int and some float after concatenation."""
        calls = _standard_df()
        calls["strike"] = calls["strike"].astype(object)
        calls.loc[0, "strike"] = 140   # int
        calls.loc[2, "strike"] = 150.0  # float
        calls.loc[4, "strike"] = "160"  # string

        prov = _fake_provider()
        prov.get_option_chain = AsyncMock(
            return_value=_chain(calls, _standard_df(), spot=150.0)
        )
        result = await OptionsAgent().run(AgentContext(symbol="TSLA", timeout_s=30.0, provider=prov))
        assert result.status == AgentStatus.complete

    @pytest.mark.asyncio
    async def test_concurrent_agents_all_complete(self):
        """Run 7 OptionsAgent instances simultaneously — all should complete without NaN errors."""
        def _make_provider():
            prov = _fake_provider()
            prov.get_option_chain = AsyncMock(
                return_value=_chain(_standard_df(), _standard_df(), spot=150.0)
            )
            return prov

        agents = [OptionsAgent() for _ in range(7)]
        ctxs = [AgentContext(symbol="TSLA", timeout_s=30.0, provider=_make_provider()) for _ in range(7)]

        results = await asyncio.gather(*[a.run(c) for a, c in zip(agents, ctxs)])

        assert all(r.status == AgentStatus.complete for r in results)


# ---------------------------------------------------------------------------
# 3. yfinance _run_sync semaphore — at most 3 concurrent fetches
# ---------------------------------------------------------------------------

class TestYFinanceSemaphore:

    def test_get_semaphore_returns_semaphore_with_limit_3(self):
        import app.providers.yfinance_provider as mod
        sem = mod._get_semaphore()
        assert isinstance(sem, asyncio.Semaphore)
        assert sem._value == 3

    def test_get_semaphore_returns_same_instance(self):
        import app.providers.yfinance_provider as mod
        assert mod._get_semaphore() is mod._get_semaphore()

    @pytest.mark.asyncio
    async def test_run_sync_limits_to_3_concurrent(self):
        """No more than 3 blocking calls should execute simultaneously."""
        import app.providers.yfinance_provider as mod

        # Fresh semaphore for test isolation
        original = mod._YF_SEMAPHORE
        mod._YF_SEMAPHORE = asyncio.Semaphore(3)

        active_count = [0]
        max_active = [0]
        lock = threading.Lock()

        def slow_fn():
            with lock:
                active_count[0] += 1
                max_active[0] = max(max_active[0], active_count[0])
            import time
            time.sleep(0.05)
            with lock:
                active_count[0] -= 1
            return "done"

        tasks = [mod._run_sync(slow_fn) for _ in range(6)]
        results = await asyncio.gather(*tasks)

        mod._YF_SEMAPHORE = original

        assert all(r == "done" for r in results)
        assert max_active[0] <= 3

    @pytest.mark.asyncio
    async def test_run_sync_passes_args_to_fn(self):
        """Arguments must be forwarded correctly to the wrapped function."""
        import app.providers.yfinance_provider as mod

        def add(a, b):
            return a + b

        result = await mod._run_sync(add, 3, 4)
        assert result == 7

    @pytest.mark.asyncio
    async def test_run_sync_propagates_exceptions(self):
        """Exceptions raised inside the sync function must propagate to the caller."""
        import app.providers.yfinance_provider as mod

        def boom():
            raise ValueError("provider exploded")

        with pytest.raises(ValueError, match="provider exploded"):
            await mod._run_sync(boom)
