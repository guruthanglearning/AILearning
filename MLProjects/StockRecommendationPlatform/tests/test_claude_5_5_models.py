"""Tests for the Claude Sonnet 5.5 / Opus 5.5 models: registry, request shape,
refusal fallbacks, and pricing of fallback-only models."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.services.claude_service as claude_service
from app.main import app
from app.services.claude_service import (
    CLAUDE_MODELS,
    DEFAULT_MODEL,
    _call_anthropic_verdict,
    _compute_cost_breakdown,
    _price_usage,
    get_claude_verdict,
    get_session_usage,
)
from tests.test_cost_breakdown import _minimal_agent_outputs

_FAKE_INP = {
    "instrument_recommendation": "stock",
    "confidence_note": "note",
    "summary_headline": "headline",
    "q1_thesis_answer": "a1",
    "q2_invalidation_answer": "a2",
    "q3_max_loss_answer": "a3",
    "q4_assignment_answer": "a4",
}


# ── Registry ─────────────────────────────────────────────────────────────────


def test_default_model_is_sonnet_5_5():
    assert DEFAULT_MODEL == "claude-sonnet-5-5"
    assert DEFAULT_MODEL in CLAUDE_MODELS


@pytest.mark.parametrize(
    ("model_id", "input_price", "output_price"),
    [("claude-sonnet-5-5", 2.0, 10.0), ("claude-opus-5-5", 4.0, 20.0)],
)
def test_claude_models_endpoint_lists_5_5_models(model_id, input_price, output_price):
    with TestClient(app) as client:
        resp = client.get("/v1/claude/models")
    assert resp.status_code == 200
    cfg = resp.json()["models"][model_id]
    assert cfg["input_price_per_m"] == input_price
    assert cfg["output_price_per_m"] == output_price
    assert cfg["supports_thinking"] is True
    assert cfg["provider"] == "anthropic"


def test_opus_5_5_cache_read_is_priced_at_5_percent():
    cfg = CLAUDE_MODELS["claude-opus-5-5"]
    input_cost, _ = _price_usage(cfg, "claude-opus-5-5", 0, 0, 0, 1_000_000)
    assert input_cost == pytest.approx(0.20)  # $0.20/MTok cache read


def test_sonnet_5_5_cache_read_is_priced_at_10_percent():
    cfg = CLAUDE_MODELS["claude-sonnet-5-5"]
    input_cost, _ = _price_usage(cfg, "claude-sonnet-5-5", 0, 0, 0, 1_000_000)
    assert input_cost == pytest.approx(0.20)  # $0.20/MTok cache read


# ── Request shape sent to the Anthropic SDK ──────────────────────────────────


class _FakeMessages:
    def __init__(self, sink: dict, kind: str):
        self._sink = sink
        self._kind = kind

    async def create(self, **kwargs):
        self._sink["kind"] = self._kind
        self._sink["kwargs"] = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(type="tool_use", input=dict(_FAKE_INP))],
            model=kwargs["model"],
            stop_reason="tool_use",
            usage=SimpleNamespace(
                input_tokens=100,
                output_tokens=50,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            ),
        )


@pytest.fixture
def captured(monkeypatch):
    import anthropic

    from app.config import settings

    sink: dict = {}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            self.messages = _FakeMessages(sink, "messages")
            self.beta = SimpleNamespace(messages=_FakeMessages(sink, "beta"))

    monkeypatch.setattr(anthropic, "AsyncAnthropic", _FakeClient)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    return sink


async def _call(model_id: str) -> None:
    await _call_anthropic_verdict(model_id, CLAUDE_MODELS[model_id], "prompt")


@pytest.mark.asyncio
async def test_opus_5_5_request_uses_default_fallback_and_high_effort(captured):
    await _call("claude-opus-5-5")
    kw = captured["kwargs"]
    assert captured["kind"] == "beta"
    assert kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["extra_body"] == {"fallbacks": "default"}
    assert kw["output_config"] == {"effort": "high"}
    assert kw["thinking"] == {"type": "adaptive"}
    assert kw["tool_choice"] == {"type": "auto"}  # forced tool_choice is a 400 on 5.5
    assert kw["max_tokens"] == 16000


@pytest.mark.asyncio
async def test_sonnet_5_5_request_uses_default_fallback_without_effort_override(captured):
    await _call("claude-sonnet-5-5")
    kw = captured["kwargs"]
    assert captured["kind"] == "beta"
    assert kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["extra_body"] == {"fallbacks": "default"}
    assert "output_config" not in kw
    assert kw["thinking"] == {"type": "adaptive"}
    assert kw["tool_choice"] == {"type": "auto"}


@pytest.mark.parametrize("model_id", ["claude-fable-5", "claude-fable-5-1"])
@pytest.mark.asyncio
async def test_fable_request_keeps_array_fallback_to_opus_4_8(captured, model_id):
    await _call(model_id)
    kw = captured["kwargs"]
    assert captured["kind"] == "beta"
    assert kw["betas"] == ["server-side-fallback-2026-06-01"]
    assert kw["extra_body"] == {"fallbacks": [{"model": "claude-opus-4-8"}]}


@pytest.mark.parametrize("model_id", ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"])
@pytest.mark.asyncio
async def test_older_models_have_no_fallback(captured, model_id):
    await _call(model_id)
    kw = captured["kwargs"]
    assert captured["kind"] == "messages"
    assert "betas" not in kw
    assert "extra_body" not in kw
    assert "output_config" not in kw


# ── Billing when a fallback is served by a model outside the picker ──────────


@pytest.mark.asyncio
async def test_opus_5_5_fallback_to_opus_5_is_billed_at_opus_5(monkeypatch):
    claude_service._session_usage.clear()

    async def _fake(chosen_model, model_cfg, user_msg):
        return dict(_FAKE_INP), 1000, 500, "claude-opus-5", 0, 0

    monkeypatch.setattr(claude_service, "_call_anthropic_verdict", _fake)

    m, f, tech, opt, risk, sent, decision_aids = _minimal_agent_outputs()
    verdict = await get_claude_verdict(
        "AAPL", m, f, tech, opt, risk, sent, decision_aids, model="claude-opus-5-5"
    )

    usage = get_session_usage()["models_used"]
    assert "claude-opus-5" in usage
    assert "claude-opus-5-5" not in usage
    # Opus 5: $5/MTok in, $25/MTok out
    assert usage["claude-opus-5"]["estimated_cost_usd"] == round(1000 * 5 / 1e6 + 500 * 25 / 1e6, 4)

    breakdown = verdict.cost_breakdown
    assert breakdown["selected_model"] == "claude-opus-5"
    selected = [e for e in breakdown["estimates"] if e["is_selected"]]
    assert len(selected) == 1
    assert selected[0]["model"] == "claude-opus-5"
    assert selected[0]["label"] == "Opus 5 (fallback)"

    claude_service._session_usage.clear()


@pytest.mark.asyncio
async def test_unknown_served_model_is_billed_at_requested_model(monkeypatch):
    claude_service._session_usage.clear()

    async def _fake(chosen_model, model_cfg, user_msg):
        return dict(_FAKE_INP), 1000, 500, "claude-some-future-model", 0, 0

    monkeypatch.setattr(claude_service, "_call_anthropic_verdict", _fake)

    m, f, tech, opt, risk, sent, decision_aids = _minimal_agent_outputs()
    verdict = await get_claude_verdict(
        "AAPL", m, f, tech, opt, risk, sent, decision_aids, model="claude-sonnet-5-5"
    )

    assert "claude-sonnet-5-5" in get_session_usage()["models_used"]
    assert verdict.cost_breakdown["selected_model"] == "claude-sonnet-5-5"

    claude_service._session_usage.clear()


def test_cost_breakdown_without_fallback_has_no_fallback_rows():
    result = _compute_cost_breakdown("claude-sonnet-5-5", input_tokens=1000, output_tokens=500)
    models = [e["model"] for e in result["estimates"]]
    assert "claude-opus-5" not in models
    assert "claude-sonnet-5" not in models
    assert [e["model"] for e in result["estimates"] if e["is_selected"]] == ["claude-sonnet-5-5"]
