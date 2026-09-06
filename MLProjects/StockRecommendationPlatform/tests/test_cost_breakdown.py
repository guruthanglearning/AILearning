"""Unit tests for the per-model cost comparison used by the Analysis tab."""

from __future__ import annotations

from app.services.claude_service import CLAUDE_MODELS, _compute_cost_breakdown


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
