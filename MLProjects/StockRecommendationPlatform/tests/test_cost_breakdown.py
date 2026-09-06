"""Unit tests for the per-model cost comparison used by the Analysis tab."""

from __future__ import annotations

from app.services.claude_service import CLAUDE_MODELS, _compute_cost_breakdown, _price_usage


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
