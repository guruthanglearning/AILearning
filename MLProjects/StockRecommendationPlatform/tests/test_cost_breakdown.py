"""Unit tests for the per-model cost comparison used by the Analysis tab."""

from __future__ import annotations

import pytest

import app.services.claude_service as claude_service
from app.schemas.agents import (
    AgentStatus,
    DataProvenance,
    DecisionAids,
    FundamentalsOutput,
    InstrumentRecommendation,
    MarketDataOutput,
    OptionsOutput,
    RiskProOutput,
    SentimentMLOutput,
    TechnicalsOutput,
)
from app.services.claude_service import (
    CLAUDE_MODELS,
    _compute_cost_breakdown,
    _price_usage,
    get_claude_verdict,
    get_session_usage,
)


def _prov():
    return DataProvenance(source="test")


def test_compute_cost_breakdown_includes_every_model():
    result = _compute_cost_breakdown("claude-opus-4-8", input_tokens=1000, output_tokens=500)

    assert result["selected_model"] == "claude-opus-4-8"
    assert result["input_tokens"] == 1000
    assert result["output_tokens"] == 500
    assert {e["model"] for e in result["estimates"]} == set(CLAUDE_MODELS)


def test_compute_cost_breakdown_marks_selected_and_computes_price():
    result = _compute_cost_breakdown("claude-fable-5-1", input_tokens=1_000_000, output_tokens=1_000_000)

    selected = [e for e in result["estimates"] if e["is_selected"]]
    assert len(selected) == 1
    assert selected[0]["model"] == "claude-fable-5-1"
    # $10/MTok input + $50/MTok output at 1M tokens each
    assert selected[0]["cost_usd"] == 60.0


def test_compute_cost_breakdown_sorted_ascending_by_cost():
    result = _compute_cost_breakdown("claude-opus-4-8", input_tokens=1000, output_tokens=500)
    costs = [e["cost_usd"] for e in result["estimates"]]
    assert costs == sorted(costs)


def test_compute_cost_breakdown_keys_off_billed_model_not_requested_model():
    # Simulates a Fable 5.1 refusal that fell back to Opus 4.8 mid-call — the
    # breakdown must mark the model that was actually billed as selected,
    # not the one the user originally picked in the dropdown.
    result = _compute_cost_breakdown("claude-opus-4-8", input_tokens=1000, output_tokens=500)
    selected = [e for e in result["estimates"] if e["is_selected"]]
    assert len(selected) == 1
    assert selected[0]["model"] == "claude-opus-4-8"
    assert result["selected_model"] == "claude-opus-4-8"


def test_price_usage_charges_cache_write_and_read_at_distinct_rates():
    pricing_cfg = CLAUDE_MODELS["claude-opus-4-8"]  # $5/MTok input, $25/MTok output
    input_cost, output_cost = _price_usage(
        pricing_cfg,
        "claude-opus-4-8",
        input_tokens=0,
        output_tokens=0,
        cache_creation_tokens=1_000_000,
        cache_read_tokens=1_000_000,
    )
    # cache write: 1_000_000 * $5/MTok * 1.25 = $6.25
    # cache read (default 10%): 1_000_000 * $5/MTok * 0.10 = $0.50
    assert input_cost == 6.75
    assert output_cost == 0.0


def test_price_usage_fable_tier_gets_cheaper_cache_read_rate():
    pricing_cfg = CLAUDE_MODELS["claude-fable-5-1"]  # $10/MTok input
    input_cost, _ = _price_usage(
        pricing_cfg,
        "claude-fable-5-1",
        input_tokens=0,
        output_tokens=0,
        cache_creation_tokens=0,
        cache_read_tokens=1_000_000,
    )
    # Fable-tier cache reads are 2.5% of base input price, not the default 10%.
    assert input_cost == 0.25


def test_price_usage_non_anthropic_model_ignores_cache_multipliers():
    # gpt-4o-mini never goes through Anthropic-style prompt caching — cache
    # tokens should fold into the base input rate, not get Anthropic's
    # 1.25x write / 10% read multipliers applied.
    pricing_cfg = CLAUDE_MODELS["gpt-4o-mini"]  # $0.15/MTok input
    input_cost, _ = _price_usage(
        pricing_cfg,
        "gpt-4o-mini",
        input_tokens=0,
        output_tokens=0,
        cache_creation_tokens=500_000,
        cache_read_tokens=500_000,
    )
    # 1_000_000 tokens total * $0.15/MTok, no cache multiplier applied
    assert input_cost == 0.15


def _minimal_agent_outputs():
    m = MarketDataOutput(agent_name="m", status=AgentStatus.complete, provenance=_prov(), last_price=100.0)
    f = FundamentalsOutput(agent_name="f", status=AgentStatus.complete, provenance=_prov())
    tech = TechnicalsOutput(agent_name="t", status=AgentStatus.complete, provenance=_prov(), trend_hint="neutral")
    opt = OptionsOutput(agent_name="o", status=AgentStatus.complete, provenance=_prov(), atm_iv=0.2)
    risk = RiskProOutput(agent_name="r", status=AgentStatus.complete, provenance=_prov())
    sent = SentimentMLOutput(agent_name="s", status=AgentStatus.complete, provenance=_prov())
    decision_aids = DecisionAids(summary_headline="test", stock_vs_options_score=0.0)
    return m, f, tech, opt, risk, sent, decision_aids


@pytest.mark.asyncio
async def test_get_claude_verdict_attributes_fallback_to_served_model(monkeypatch):
    """When a Fable-tier request refuses and the server-side fallback re-serves it
    via Opus 4.8, session usage must land in the Opus 4.8 bucket at Opus 4.8's
    price — not under the originally-requested Fable model at Fable's price."""
    claude_service._session_usage.clear()

    fake_inp = {
        "instrument_recommendation": "stock",
        "confidence_note": "note",
        "summary_headline": "headline",
        "q1_thesis_answer": "a1",
        "q2_invalidation_answer": "a2",
        "q3_max_loss_answer": "a3",
        "q4_assignment_answer": "a4",
    }

    async def _fake_call_anthropic_verdict(chosen_model, model_cfg, user_msg):
        # served_model differs from chosen_model — simulates a refusal fallback
        return fake_inp, 1000, 500, "claude-opus-4-8", 0, 0

    monkeypatch.setattr(claude_service, "_call_anthropic_verdict", _fake_call_anthropic_verdict)

    m, f, tech, opt, risk, sent, decision_aids = _minimal_agent_outputs()
    verdict = await get_claude_verdict(
        "AAPL", m, f, tech, opt, risk, sent, decision_aids, model="claude-fable-5-1"
    )

    usage = get_session_usage()
    assert "claude-opus-4-8" in usage["models_used"]
    assert "claude-fable-5-1" not in usage["models_used"]

    opus_pricing = CLAUDE_MODELS["claude-opus-4-8"]
    expected_cost = round(
        1000 * opus_pricing["input_price_per_m"] / 1_000_000
        + 500 * opus_pricing["output_price_per_m"] / 1_000_000,
        4,
    )
    assert usage["models_used"]["claude-opus-4-8"]["estimated_cost_usd"] == expected_cost

    assert verdict.instrument_recommendation == InstrumentRecommendation.stock
    assert verdict.cost_breakdown["selected_model"] == "claude-opus-4-8"

    claude_service._session_usage.clear()
