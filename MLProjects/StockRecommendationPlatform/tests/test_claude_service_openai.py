"""Unit tests for the OpenAI provider adapter in app.services.claude_service.

These target `_call_openai_verdict` directly (bypassing the supervisor-level
`get_claude_verdict` mock used elsewhere) since that's the only way to exercise
this provider's response parsing, error handling, and usage-token accounting.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.config import settings as app_settings
from app.services.claude_service import (
    _VERDICT_TOOL,
    ClaudeServiceError,
    _call_openai_verdict,
)

VALID_ARGS = json.dumps(
    {
        "instrument_recommendation": "stock",
        "confidence_note": "Trend is bullish with confirming volume.",
        "summary_headline": "AAPL favors direct stock ownership.",
        "q1_thesis_answer": "Multi-month thesis, not speculative.",
        "q2_invalidation_answer": "Break below $300 support.",
        "q3_max_loss_answer": "Bounded via stop-loss at $295.",
        "q4_assignment_answer": "Acceptable given the trend.",
    }
)


def _tool_call(arguments: str, name: str = _VERDICT_TOOL["name"]):
    return SimpleNamespace(function=SimpleNamespace(name=name, arguments=arguments))


def _fake_response(tool_calls, prompt_tokens=100, completion_tokens=50, model="gpt-4o-mini-2026-01-01", finish_reason="tool_calls"):
    message = SimpleNamespace(tool_calls=tool_calls)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    usage = SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
    return SimpleNamespace(choices=[choice], usage=usage, model=model)


@pytest.fixture
def fake_openai_client(monkeypatch):
    """Patch openai.AsyncOpenAI so no real API call is made; return the mock `create`."""
    import openai

    calls = SimpleNamespace(return_value=None, kwargs=None)

    async def _create(**kwargs):
        calls.kwargs = kwargs
        return calls.return_value

    client_instance = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_create)))
    monkeypatch.setattr(openai, "AsyncOpenAI", lambda api_key=None: client_instance)
    monkeypatch.setattr(app_settings, "openai_api_key", "sk-test-key")
    return calls


@pytest.mark.asyncio
async def test_call_openai_verdict_success_and_usage_accounting(fake_openai_client):
    fake_openai_client.return_value = _fake_response(
        [_tool_call(VALID_ARGS)], prompt_tokens=123, completion_tokens=45, model="gpt-4o-mini-2026-01-01"
    )

    inp, input_tokens, output_tokens, served_model = await _call_openai_verdict("gpt-4o-mini", "irrelevant prompt")

    assert inp["instrument_recommendation"] == "stock"
    assert inp["summary_headline"] == "AAPL favors direct stock ownership."
    assert input_tokens == 123
    assert output_tokens == 45
    assert served_model == "gpt-4o-mini-2026-01-01"
    # Confirm the tool schema and model were actually forwarded to the API call.
    assert fake_openai_client.kwargs["model"] == "gpt-4o-mini"
    assert fake_openai_client.kwargs["tools"][0]["function"]["name"] == _VERDICT_TOOL["name"]


@pytest.mark.asyncio
async def test_call_openai_verdict_missing_api_key(monkeypatch):
    monkeypatch.setattr(app_settings, "openai_api_key", None)

    with pytest.raises(ClaudeServiceError, match="OPENAI_API_KEY is not configured"):
        await _call_openai_verdict("gpt-4o-mini", "prompt")


@pytest.mark.asyncio
async def test_call_openai_verdict_malformed_arguments(fake_openai_client):
    fake_openai_client.return_value = _fake_response([_tool_call("{not valid json")])

    with pytest.raises(ClaudeServiceError, match="malformed tool-call arguments"):
        await _call_openai_verdict("gpt-4o-mini", "prompt")


@pytest.mark.asyncio
async def test_call_openai_verdict_no_tool_call(fake_openai_client):
    fake_openai_client.return_value = _fake_response([], finish_reason="stop")

    with pytest.raises(ClaudeServiceError, match="no tool call"):
        await _call_openai_verdict("gpt-4o-mini", "prompt")


@pytest.mark.asyncio
async def test_call_openai_verdict_ignores_unrelated_tool_call(fake_openai_client):
    """Only the submit_analysis_verdict tool call should be matched, not an arbitrary one."""
    fake_openai_client.return_value = _fake_response([_tool_call("{}", name="some_other_function")])

    with pytest.raises(ClaudeServiceError, match="no tool call"):
        await _call_openai_verdict("gpt-4o-mini", "prompt")
