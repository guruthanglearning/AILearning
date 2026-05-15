from types import SimpleNamespace

from app.schemas.agents import (
    AgentStatus,
    DataProvenance,
    InstrumentRecommendation,
    MarketDataOutput,
    OptionsOutput,
    RiskProOutput,
    TechnicalsOutput,
)
from app.supervisor import Supervisor


def _prov():
    return DataProvenance(source="test")


def test_merge_insufficient_when_market_fails():
    s = Supervisor()
    m = MarketDataOutput(
        agent_name="m",
        status=AgentStatus.failed,
        provenance=_prov(),
        error_message="x",
    )
    tech = TechnicalsOutput(
        agent_name="t", status=AgentStatus.complete, provenance=_prov(), trend_hint="bullish"
    )
    opt = OptionsOutput(agent_name="o", status=AgentStatus.complete, provenance=_prov(), atm_iv=0.4)
    risk = RiskProOutput(agent_name="r", status=AgentStatus.complete, provenance=_prov())
    v, og, note = s._merge(m, tech, opt, risk, 0.0)
    assert v == InstrumentRecommendation.insufficient_data
    assert og is None


def test_merge_options_on_earnings_mixed():
    s = Supervisor()
    m = MarketDataOutput(
        agent_name="m",
        status=AgentStatus.complete,
        provenance=_prov(),
        last_price=50.0,
    )
    tech = TechnicalsOutput(
        agent_name="t", status=AgentStatus.complete, provenance=_prov(), trend_hint="mixed"
    )
    opt = OptionsOutput(agent_name="o", status=AgentStatus.complete, provenance=_prov(), atm_iv=0.3)
    risk = RiskProOutput(
        agent_name="r",
        status=AgentStatus.complete,
        provenance=_prov(),
        has_upcoming_earnings=True,
    )
    v, og, note = s._merge(m, tech, opt, risk, 0.0)
    assert v == InstrumentRecommendation.options
    assert og is not None
    assert "earnings" in note.lower()


async def test_decision_aids_score_monkeypatch(monkeypatch):
    from app.decision_support import build_decision_aids
    from app.providers.yfinance_provider import YFinanceProvider

    async def _mock_hv(symbol, provider):
        return 0.2

    monkeypatch.setattr("app.decision_support._hv_20d", _mock_hv)

    tech = TechnicalsOutput(
        agent_name="t", status=AgentStatus.complete, provenance=_prov(), trend_hint="bullish"
    )
    opt = OptionsOutput(
        agent_name="o",
        status=AgentStatus.complete,
        provenance=_prov(),
        atm_iv=0.5,
        chain_liquidity_hint="adequate",
    )
    risk = RiskProOutput(
        agent_name="r", status=AgentStatus.complete, provenance=_prov(), has_upcoming_earnings=False
    )
    provider = YFinanceProvider()
    aids = await build_decision_aids(
        "TEST", 100.0, tech, opt, risk, 100_000, 1.0, provider=provider, ml_forecast_signal="Buy"
    )
    assert -1.0 <= aids.stock_vs_options_score <= 1.0
    assert aids.volatility is not None
    assert any(p.play_id == "long_stock" for p in aids.instrument_plays)
    assert aids.comparison_matrix.get("breakeven_thinking")
