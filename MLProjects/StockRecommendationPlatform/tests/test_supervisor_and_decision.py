
from app.schemas.agents import (
    AgentStatus,
    DataProvenance,
    FinancialsOutput,
    FundamentalsOutput,
    InstrumentRecommendation,
    MarketDataOutput,
    OptionsOutput,
    RiskProOutput,
    SentimentMLOutput,
    TechnicalsOutput,
)
from app.supervisor import Supervisor, _agent_summary, _fmt_cap


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


# ---------------------------------------------------------------------------
# _fmt_cap
# ---------------------------------------------------------------------------


def test_fmt_cap_none():
    assert _fmt_cap(None) == "n/a"


def test_fmt_cap_trillion():
    assert _fmt_cap(2.5e12) == "$2.50T"


def test_fmt_cap_billion():
    assert _fmt_cap(5.0e9) == "$5.0B"


def test_fmt_cap_million():
    assert _fmt_cap(800e6) == "$800M"


# ---------------------------------------------------------------------------
# _agent_summary
# ---------------------------------------------------------------------------


def test_agent_summary_financials_no_summary():
    fin = FinancialsOutput(agent_name="FinancialsAgent", status=AgentStatus.complete, provenance=_prov())
    head, det = _agent_summary(fin)
    assert head == "Financials fetched"
    assert det is None


def test_agent_summary_financials_with_summary():
    fin = FinancialsOutput(
        agent_name="FinancialsAgent", status=AgentStatus.complete, provenance=_prov(),
        summary="Annual revenue $394B\nGross margin 43%",
    )
    head, det = _agent_summary(fin)
    assert head == "Annual revenue $394B"
    assert "Gross margin" in (det or "")


def test_agent_summary_options_with_expiry():
    opt = OptionsOutput(
        agent_name="OptionsAgent", status=AgentStatus.complete, provenance=_prov(),
        atm_iv=0.25, implied_move_1d_pct=1.5, chain_liquidity_hint="adequate",
        nearest_expiry="2025-06-20",
    )
    head, det = _agent_summary(opt)
    assert "IV" in head
    assert "2025-06-20" in (det or "")


def test_agent_summary_options_no_iv():
    opt = OptionsOutput(
        agent_name="OptionsAgent", status=AgentStatus.complete, provenance=_prov(),
        atm_iv=None,
    )
    head, det = _agent_summary(opt)
    assert "IV n/a" in head


def test_agent_summary_riskpro_upcoming_earnings_no_days():
    risk = RiskProOutput(
        agent_name="RiskProWorkflowAgent", status=AgentStatus.complete, provenance=_prov(),
        has_upcoming_earnings=True, earnings_days_away=None,
    )
    head, det = _agent_summary(risk)
    assert "upcoming" in head.lower()


def test_agent_summary_sentiment_with_headlines():
    sent = SentimentMLOutput(
        agent_name="SentimentMLAgent", status=AgentStatus.complete, provenance=_prov(),
        sentiment_score=0.72, forecast_signal="Bullish", top_headlines=["AAPL beats Q3"],
    )
    head, det = _agent_summary(sent)
    assert "Bullish" in head
    assert det == "AAPL beats Q3"


def test_agent_summary_sentiment_no_headlines_uses_note():
    sent = SentimentMLOutput(
        agent_name="SentimentMLAgent", status=AgentStatus.complete, provenance=_prov(),
        sentiment_score=-0.2, forecast_signal="Bearish", top_headlines=[],
        confidence_note="No news found",
    )
    head, det = _agent_summary(sent)
    assert "Bearish" in head
    assert det == "No news found"


def test_agent_summary_sentiment_no_score():
    sent = SentimentMLOutput(
        agent_name="SentimentMLAgent", status=AgentStatus.complete, provenance=_prov(),
        forecast_signal="Neutral", top_headlines=[],
    )
    head, det = _agent_summary(sent)
    assert head == "Neutral"


# ---------------------------------------------------------------------------
# _fundamentals_snapshot
# ---------------------------------------------------------------------------


def test_fundamentals_snapshot_returns_none_when_failed():
    f = FundamentalsOutput(
        agent_name="FundamentalsAgent", status=AgentStatus.failed, provenance=_prov()
    )
    assert Supervisor._fundamentals_snapshot(f) is None


def test_fundamentals_snapshot_returns_data_when_complete():
    f = FundamentalsOutput(
        agent_name="FundamentalsAgent", status=AgentStatus.complete, provenance=_prov(),
        sector="Technology", pe_ratio=28.5, forward_pe=26.0, revenue_growth=0.08,
        market_cap=3e12,
    )
    snap = Supervisor._fundamentals_snapshot(f)
    assert snap is not None
    assert snap.sector == "Technology"
    assert snap.pe_ratio == 28.5


# ---------------------------------------------------------------------------
# _merge — additional branches
# ---------------------------------------------------------------------------


def test_merge_options_degraded_stock_with_degraded_note():
    """options data missing + stock_vs_options_score < -0.2 → stock with 'degraded' in note."""
    s = Supervisor()
    m = MarketDataOutput(agent_name="m", status=AgentStatus.complete, provenance=_prov(), last_price=50.0)
    tech = TechnicalsOutput(agent_name="t", status=AgentStatus.complete, provenance=_prov(), trend_hint="neutral")
    opt = OptionsOutput(agent_name="o", status=AgentStatus.failed, provenance=_prov())
    risk = RiskProOutput(agent_name="r", status=AgentStatus.complete, provenance=_prov())
    v, og, note = s._merge(m, tech, opt, risk, -0.5)
    assert v == InstrumentRecommendation.stock
    assert og is None
    assert "degraded" in note.lower()


def test_merge_balanced_regime_score_negative_returns_options():
    """Balanced regime (no iv_rich, no directional clarity): score < 0 → options."""
    s = Supervisor()
    m = MarketDataOutput(agent_name="m", status=AgentStatus.complete, provenance=_prov(), last_price=50.0)
    tech = TechnicalsOutput(agent_name="t", status=AgentStatus.complete, provenance=_prov(), trend_hint="neutral")
    opt = OptionsOutput(agent_name="o", status=AgentStatus.complete, provenance=_prov(), atm_iv=0.20)
    risk = RiskProOutput(agent_name="r", status=AgentStatus.complete, provenance=_prov(), has_upcoming_earnings=False)
    v, og, note = s._merge(m, tech, opt, risk, -0.1)
    assert v == InstrumentRecommendation.options
    assert og is not None


def test_merge_balanced_regime_score_positive_returns_stock():
    """Balanced regime (no iv_rich, no directional clarity): score >= 0 → stock."""
    s = Supervisor()
    m = MarketDataOutput(agent_name="m", status=AgentStatus.complete, provenance=_prov(), last_price=50.0)
    tech = TechnicalsOutput(agent_name="t", status=AgentStatus.complete, provenance=_prov(), trend_hint="neutral")
    opt = OptionsOutput(agent_name="o", status=AgentStatus.complete, provenance=_prov(), atm_iv=0.20)
    risk = RiskProOutput(agent_name="r", status=AgentStatus.complete, provenance=_prov(), has_upcoming_earnings=False)
    v, og, note = s._merge(m, tech, opt, risk, 0.1)
    assert v == InstrumentRecommendation.stock
