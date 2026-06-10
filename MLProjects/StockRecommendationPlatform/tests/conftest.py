"""Shared pytest fixtures — mocks the Claude LLM service for all integration tests."""

from __future__ import annotations

import pytest

from app.schemas.agents import InstrumentRecommendation
from app.services.claude_service import ClaudeVerdict


def _build_claude_verdict(
    recommendation: InstrumentRecommendation,
    confidence_note: str,
) -> ClaudeVerdict:
    return ClaudeVerdict(
        instrument_recommendation=recommendation,
        confidence_note=confidence_note,
        options_guidance=None,
        summary_headline=f"{recommendation.value.title()} is the preferred vehicle for this setup.",
        user_answers=[
            "Assess thesis grade based on trend and fundamentals before sizing.",
            "Invalidation: decisive price break or earnings surprise.",
            "Define max loss via stop-loss or option premium before entering.",
            "Only sell short puts if assignment at the strike is acceptable.",
        ],
    )


@pytest.fixture(autouse=True)
def mock_claude_verdict(monkeypatch):
    """Replace get_claude_verdict with a rule-based mock so tests never hit the real API."""

    async def _mock(symbol, m, f, tech, opt, risk, sent, decision_aids, model=None):
        # Earnings imminent + trend not clearly bullish/bearish → options (defined risk)
        trend = getattr(tech, "trend_hint", None) or "mixed"
        if risk.has_upcoming_earnings and trend not in ("bullish", "bearish"):
            return _build_claude_verdict(
                InstrumentRecommendation.options,
                f"earnings within {risk.earnings_days_away or '?'} days with {trend} technicals "
                f"— defined-risk options reduce binary event exposure.",
            )

        # IV elevated → options (premium selling)
        atm_iv = getattr(opt, "atm_iv", None)
        if atm_iv is not None and atm_iv > 0.35:
            return _build_claude_verdict(
                InstrumentRecommendation.options,
                f"ATM IV at {atm_iv * 100:.1f}% is elevated vs historical norms "
                f"— premium-selling structures are capital-efficient here.",
            )

        # Default: directional stock play
        return _build_claude_verdict(
            InstrumentRecommendation.stock,
            f"Normal IV environment with {trend} trend — stock ownership is the direct "
            f"and cost-efficient vehicle for this setup.",
        )

    monkeypatch.setattr("app.supervisor.get_claude_verdict", _mock)
