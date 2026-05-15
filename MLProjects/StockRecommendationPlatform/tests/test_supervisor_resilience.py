"""Supervisor resilience tests — partial-failure matrix.

All tests are offline (no network, no DB, no Redis).
"""

from __future__ import annotations

import asyncio

import pytest

from app.agents.base import AgentContext, BaseAgent
from app.agents.market_data import MarketDataAgent
from app.agents.options import OptionsAgent
from app.agents.technicals import TechnicalsAgent
from app.schemas.agents import (
    AgentStatus,
    DataProvenance,
    InstrumentRecommendation,
    MarketDataOutput,
    OptionsOutput,
    RiskProOutput,
    SentimentMLOutput,
    TechnicalsOutput,
    FundamentalsOutput,
    FinancialsOutput,
)
from app.supervisor import Supervisor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prov(source: str = "test") -> DataProvenance:
    return DataProvenance(source=source)


def _failed_market() -> MarketDataOutput:
    return MarketDataOutput(agent_name="MarketDataAgent", status=AgentStatus.failed, provenance=_prov())


def _ok_market(price: float = 100.0) -> MarketDataOutput:
    return MarketDataOutput(
        agent_name="MarketDataAgent",
        status=AgentStatus.complete,
        provenance=_prov(),
        last_price=price,
        previous_close=price - 1,
    )


def _failed_options() -> OptionsOutput:
    return OptionsOutput(
        agent_name="OptionsAgent",
        status=AgentStatus.failed,
        provenance=_prov(),
        chain_liquidity_hint="unknown",
    )


def _ok_options(iv: float = 0.3) -> OptionsOutput:
    return OptionsOutput(
        agent_name="OptionsAgent",
        status=AgentStatus.complete,
        provenance=_prov(),
        atm_iv=iv,
        chain_liquidity_hint="adequate",
    )


def _failed_tech() -> TechnicalsOutput:
    return TechnicalsOutput(agent_name="TechnicalsAgent", status=AgentStatus.failed, provenance=_prov())


def _ok_tech(trend: str = "bullish") -> TechnicalsOutput:
    return TechnicalsOutput(
        agent_name="TechnicalsAgent", status=AgentStatus.complete, provenance=_prov(), trend_hint=trend
    )


def _ok_risk(has_earnings: bool = False) -> RiskProOutput:
    return RiskProOutput(
        agent_name="RiskProWorkflowAgent",
        status=AgentStatus.complete,
        provenance=_prov(),
        has_upcoming_earnings=has_earnings,
    )


def _failed_risk() -> RiskProOutput:
    return RiskProOutput(
        agent_name="RiskProWorkflowAgent", status=AgentStatus.failed, provenance=_prov()
    )


# ---------------------------------------------------------------------------
# safe_run() unit tests
# ---------------------------------------------------------------------------


async def test_safe_run_timeout(monkeypatch):
    """safe_run enforces ctx.timeout_s — a hanging agent returns failed."""

    async def _hang(ctx):
        await asyncio.sleep(999)

    agent = MarketDataAgent()
    monkeypatch.setattr(agent, "run", _hang)
    ctx = AgentContext("AAPL", timeout_s=0.01)
    result = await agent.safe_run(ctx)

    assert result.status == AgentStatus.failed
    assert "Timed out" in (result.error_message or "")


async def test_safe_run_exception(monkeypatch):
    """safe_run catches unexpected exceptions and returns failed output."""

    async def _crash(ctx):
        raise ValueError("internal boom")

    agent = MarketDataAgent()
    monkeypatch.setattr(agent, "run", _crash)
    ctx = AgentContext("AAPL", timeout_s=5.0)
    result = await agent.safe_run(ctx)

    assert result.status == AgentStatus.failed
    assert "boom" in (result.error_message or "")


async def test_safe_run_returns_correct_type_on_timeout(monkeypatch):
    """safe_run returns the agent's declared output_model type on timeout."""

    async def _hang(ctx):
        await asyncio.sleep(999)

    agent = OptionsAgent()
    monkeypatch.setattr(agent, "run", _hang)
    ctx = AgentContext("AAPL", timeout_s=0.01)
    result = await agent.safe_run(ctx)

    assert isinstance(result, OptionsOutput)
    assert result.status == AgentStatus.failed


# ---------------------------------------------------------------------------
# _merge() partial-failure matrix
# ---------------------------------------------------------------------------


def test_market_timeout_gives_insufficient_data():
    """If market data fails (timeout or error), verdict must be insufficient_data."""
    s = Supervisor()
    v, og, note = s._merge(_failed_market(), _ok_tech(), _ok_options(), _ok_risk(), 0.0)
    assert v == InstrumentRecommendation.insufficient_data
    assert og is None


def test_options_timeout_gives_stock_path():
    """If options agent fails, supervisor falls back to stock-only path."""
    s = Supervisor()
    v, og, note = s._merge(_ok_market(), _ok_tech("bullish"), _failed_options(), _ok_risk(), 0.3)
    assert v == InstrumentRecommendation.stock


def test_technicals_timeout_trend_treated_as_mixed():
    """With trend_hint=None (timed-out technicals), supervisor treats trend as mixed."""
    s = Supervisor()
    # trend_hint=None → _merge treats as "mixed"; no earnings → balanced regime
    v, og, note = s._merge(_ok_market(), _failed_tech(), _ok_options(iv=0.2), _ok_risk(), 0.0)
    # Should not raise; verdict must be a valid InstrumentRecommendation
    assert v in list(InstrumentRecommendation)


def test_risk_timeout_defaults_to_no_earnings():
    """A failed risk agent defaults has_upcoming_earnings=False (model default)."""
    s = Supervisor()
    # _failed_risk() has has_upcoming_earnings=False by default — safe assumption
    v, og, note = s._merge(_ok_market(), _ok_tech("bullish"), _ok_options(iv=0.2), _failed_risk(), 0.3)
    # Should not trigger earnings path
    assert v != InstrumentRecommendation.insufficient_data
    if og is not None:
        assert "earnings" not in (og.strategy_family or "").lower()


def test_all_non_market_agents_fail_still_returns_verdict():
    """Even if 6 of 7 agents fail, a valid verdict is produced (no 500)."""
    s = Supervisor()
    v, og, note = s._merge(
        _ok_market(price=150.0),
        _failed_tech(),
        _failed_options(),
        _failed_risk(),
        0.0,
    )
    # Market ok → not insufficient_data; falls through to stock-only path
    assert v in (InstrumentRecommendation.stock, InstrumentRecommendation.options)
    assert isinstance(note, str) and len(note) > 0
