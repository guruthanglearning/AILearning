"""Claude LLM service for stock analysis verdicts and decision aids enrichment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from app.schemas.agents import (
        DecisionAids,
        FundamentalsOutput,
        InstrumentRecommendation,
        MarketDataOutput,
        OptionsGuidance,
        OptionsOutput,
        RiskProOutput,
        SentimentMLOutput,
        TechnicalsOutput,
    )

log = structlog.get_logger(__name__)


class ClaudeServiceError(RuntimeError):
    """Raised when the Claude decision engine fails and analysis cannot continue."""

_SYSTEM_PROMPT = """\
You are an expert stock market analyst and options strategist with deep knowledge of \
technical analysis, fundamental analysis, and options pricing theory.

You receive structured output from 7 specialized analysis agents (market data, fundamentals, \
technicals, financials, options, risk, and sentiment) and synthesize them into an evidence-based \
trading recommendation.

Your tasks:
1. Determine the best trading vehicle: direct stock ownership ("stock"), options structures \
("options"), no trade ("no_trade"), or insufficient data ("insufficient_data")
2. Write a concise confidence note (1-2 sentences) citing the specific data points that drove \
your decision
3. If recommending options, specify the strategy family and actionable strike guidance
4. Write a one-sentence summary headline for the stock vs options decision
5. Answer 4 key pre-trade questions a trader must consider before sizing a position

Decision rules:
- "options" is appropriate when: IV is elevated vs HV (sell premium), earnings are imminent \
(defined-risk structures), or there is directional conviction but IV is not extreme (debit plays)
- "stock" is appropriate when: trend is clear and confirmed, IV is normal, fundamentals support \
the thesis and options structures would overcomplicate it
- "no_trade" when: signals are clearly conflicting, risk/reward is unfavorable, or conditions \
are deteriorating without a clear catalyst
- "insufficient_data" only when critical price or trend data is genuinely missing

Write directly and specifically — cite actual numbers from the data. \
The user is a sophisticated retail trader who understands risk."""

_VERDICT_TOOL: dict[str, Any] = {
    "name": "submit_analysis_verdict",
    "description": "Submit the final trading analysis verdict, options guidance, and decision aids",
    "input_schema": {
        "type": "object",
        "properties": {
            "instrument_recommendation": {
                "type": "string",
                "enum": ["stock", "options", "no_trade", "insufficient_data"],
                "description": "The recommended trading vehicle based on all agent data",
            },
            "confidence_note": {
                "type": "string",
                "description": (
                    "1-2 sentences citing the specific data points (price level, trend, RSI, "
                    "IV level, earnings proximity, sentiment score, etc.) that drove this "
                    "recommendation"
                ),
            },
            "options_strategy_family": {
                "type": "string",
                "enum": [
                    "long_stock_or_long_diagonal",
                    "premium_selling_or_covered_call",
                    "debit_vertical_or_long_put_call",
                    "debit_spread_or_stock",
                ],
                "description": "Required when instrument_recommendation is 'options'",
            },
            "options_rationale_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Short snake_case codes explaining the options choice, e.g. "
                    "['iv_elevated', 'earnings_soon', 'directional_clarity']"
                ),
            },
            "options_strike_guidance": {
                "type": "string",
                "description": "Actionable strike and expiry guidance for the recommended options structure",
            },
            "options_max_loss_scenario": {
                "type": "string",
                "description": "How to calculate or bound max loss for the recommended options structure",
            },
            "options_profit_targets": {
                "type": "array",
                "items": {"type": "string"},
                "description": "1-3 profit management rules for the recommended options structure",
            },
            "summary_headline": {
                "type": "string",
                "description": (
                    "One sentence summarizing the stock vs options trade-off for this specific "
                    "setup (cite instrument and key driver)"
                ),
            },
            "q1_thesis_answer": {
                "type": "string",
                "description": (
                    "Answer to: Is this trade speculative or part of a multi-month thesis? "
                    "Ground your answer in the trend, fundamentals, and earnings data."
                ),
            },
            "q2_invalidation_answer": {
                "type": "string",
                "description": (
                    "Answer to: What invalidates the idea — price level, time, or vol event? "
                    "Cite specific price levels, dates, or conditions."
                ),
            },
            "q3_max_loss_answer": {
                "type": "string",
                "description": (
                    "Answer to: Can you state max loss in dollars before entering? "
                    "Reference the options structures or stock stop-loss scenarios in the data."
                ),
            },
            "q4_assignment_answer": {
                "type": "string",
                "description": (
                    "Answer to: If assigned on a short put / covered call, is that acceptable? "
                    "Consider the trend, current price, and earnings risk."
                ),
            },
        },
        "required": [
            "instrument_recommendation",
            "confidence_note",
            "summary_headline",
            "q1_thesis_answer",
            "q2_invalidation_answer",
            "q3_max_loss_answer",
            "q4_assignment_answer",
        ],
    },
}


@dataclass
class ClaudeVerdict:
    instrument_recommendation: InstrumentRecommendation
    confidence_note: str
    options_guidance: OptionsGuidance | None
    summary_headline: str
    user_answers: list[str] = field(default_factory=list)


def _fmt_agents_prompt(
    symbol: str,
    m: MarketDataOutput,
    f: FundamentalsOutput,
    tech: TechnicalsOutput,
    opt: OptionsOutput,
    risk: RiskProOutput,
    sent: SentimentMLOutput,
    decision_aids: DecisionAids,
) -> str:
    """Format all agent outputs into a structured human-readable prompt."""
    from app.schemas.agents import AgentStatus

    lines: list[str] = [f"=== STOCK ANALYSIS DATA: {symbol} ===", ""]

    # --- Market data ---
    price_str = f"${m.last_price:.2f}" if m.last_price else "unavailable"
    lines += ["MARKET DATA:", f"  Last price: {price_str}", ""]

    # --- Fundamentals ---
    if f.status == AgentStatus.complete:
        parts = []
        if f.company_name:
            parts.append(f"  Company: {f.company_name}")
        if f.sector:
            parts.append(f"  Sector: {f.sector}")
        if f.market_cap is not None:
            mc = f.market_cap
            mc_str = (
                f"${mc/1e12:.2f}T" if mc >= 1e12
                else f"${mc/1e9:.1f}B" if mc >= 1e9
                else f"${mc/1e6:.0f}M"
            )
            parts.append(f"  Market Cap: {mc_str}")
        if f.pe_ratio is not None:
            parts.append(f"  Trailing P/E: {f.pe_ratio:.1f}x")
        if f.forward_pe is not None:
            parts.append(f"  Forward P/E: {f.forward_pe:.1f}x")
        if f.revenue_growth is not None:
            parts.append(f"  Revenue Growth: {f.revenue_growth * 100:+.1f}%")
        lines += ["FUNDAMENTALS:"] + (parts if parts else ["  (no data)"]) + [""]
    else:
        lines += ["FUNDAMENTALS: agent failed or data unavailable", ""]

    # --- Technicals ---
    if tech.status == AgentStatus.complete:
        parts = []
        if tech.trend_hint:
            parts.append(f"  Trend: {tech.trend_hint}")
        if tech.rsi_14 is not None:
            interp = (
                "overbought" if tech.rsi_14 > 70
                else "oversold" if tech.rsi_14 < 30
                else "bullish zone" if tech.rsi_14 >= 50
                else "bearish zone"
            )
            parts.append(f"  RSI-14: {tech.rsi_14:.1f} ({interp})")
        if tech.macd_6_13 is not None and tech.macd_6_13_signal is not None:
            cross = "bullish" if tech.macd_6_13 > tech.macd_6_13_signal else "bearish"
            hist_str = f", hist {tech.macd_6_13_hist:+.4f}" if tech.macd_6_13_hist is not None else ""
            parts.append(f"  MACD (6/13): {cross} crossover{hist_str}")
        if tech.obv_slope is not None:
            direction = "accumulation (buying)" if tech.obv_slope > 0 else "distribution (selling)"
            parts.append(f"  OBV slope: {tech.obv_slope:+.4f} — {direction}")
        if tech.atr_pct_14 is not None:
            volatility_note = "high volatility" if tech.atr_pct_14 > 0.04 else "moderate volatility"
            parts.append(f"  ATR-14: {tech.atr_pct_14 * 100:.2f}% daily range ({volatility_note})")
        if tech.sma_20 is not None and tech.sma_50 is not None:
            rel = "above" if tech.sma_20 > tech.sma_50 else "below"
            parts.append(
                f"  SMA 20 (${tech.sma_20:.2f}) is {rel} SMA 50 (${tech.sma_50:.2f})"
                f" — short-term {'bullish' if tech.sma_20 > tech.sma_50 else 'bearish'}"
            )
        if tech.week_52_high is not None and tech.week_52_low is not None and m.last_price:
            rng = tech.week_52_high - tech.week_52_low
            pos = (m.last_price - tech.week_52_low) / rng * 100 if rng > 0 else 50
            parts.append(
                f"  52-week range: ${tech.week_52_low:.2f} – ${tech.week_52_high:.2f} "
                f"(price is at {pos:.0f}% of range)"
            )
        lines += ["TECHNICALS:"] + (parts if parts else ["  (no data)"]) + [""]
    else:
        lines += ["TECHNICALS: agent failed or data unavailable", ""]

    # --- Options ---
    if opt.status == AgentStatus.complete and opt.atm_iv is not None:
        parts = [f"  ATM IV: {opt.atm_iv * 100:.1f}%"]
        if opt.nearest_expiry:
            parts.append(f"  Nearest expiry: {opt.nearest_expiry}")
        lines += ["OPTIONS:"] + parts + [""]
    else:
        lines += ["OPTIONS: data unavailable or no options chain found", ""]

    # --- Risk / Earnings ---
    earnings_str = (
        f"YES — {risk.earnings_days_away} days away"
        if risk.has_upcoming_earnings and risk.earnings_days_away is not None
        else "YES (date unknown)" if risk.has_upcoming_earnings
        else "no"
    )
    lines += [
        "RISK FLAGS:",
        f"  Upcoming earnings: {earnings_str}",
        "",
    ]

    # --- Sentiment ---
    if sent.status == AgentStatus.complete:
        parts = []
        if sent.sentiment_score is not None:
            label = (
                "very positive" if sent.sentiment_score > 0.5
                else "positive" if sent.sentiment_score > 0.2
                else "very negative" if sent.sentiment_score < -0.5
                else "negative" if sent.sentiment_score < -0.2
                else "neutral"
            )
            parts.append(f"  Sentiment score: {sent.sentiment_score:+.3f} ({label})")
        if sent.forecast_signal:
            parts.append(f"  FinBERT forecast signal: {sent.forecast_signal}")
        if sent.top_headlines:
            parts.append(f"  Recent headlines: {'; '.join(sent.top_headlines[:3])}")
        lines += ["SENTIMENT:"] + (parts if parts else ["  (no data)"]) + [""]
    else:
        lines += ["SENTIMENT: agent failed or data unavailable", ""]

    # --- Quantitative decision aids ---
    score = decision_aids.stock_vs_options_score
    score_interp = (
        "strongly favors stock" if score > 0.5
        else "leans stock" if score > 0.15
        else "strongly favors options structures" if score < -0.5
        else "leans options" if score < -0.15
        else "balanced / no clear preference"
    )
    vol_regime = decision_aids.volatility.regime if decision_aids.volatility else "unknown"

    checklist_summary_parts: list[str] = []
    if decision_aids.checklist:
        passed = [c.label for c in decision_aids.checklist if c.state == "pass"]
        failed = [c.label for c in decision_aids.checklist if c.state == "fail"]
        warned = [c.label for c in decision_aids.checklist if c.state == "warn"]
        if passed:
            checklist_summary_parts.append(f"PASS: {', '.join(passed)}")
        if warned:
            checklist_summary_parts.append(f"WARN: {', '.join(warned)}")
        if failed:
            checklist_summary_parts.append(f"FAIL: {', '.join(failed)}")

    lines += [
        "QUANTITATIVE DECISION AIDS (pre-computed):",
        f"  Stock vs options score: {score:+.3f} ({score_interp})",
        f"  Volatility regime: {vol_regime}",
    ]
    if checklist_summary_parts:
        lines.append("  Checklist: " + " | ".join(checklist_summary_parts))
    lines.append("")

    return "\n".join(lines)


async def get_claude_verdict(
    symbol: str,
    m: MarketDataOutput,
    f: FundamentalsOutput,
    tech: TechnicalsOutput,
    opt: OptionsOutput,
    risk: RiskProOutput,
    sent: SentimentMLOutput,
    decision_aids: DecisionAids,
) -> ClaudeVerdict:
    """Call Claude to synthesize all agent outputs into a trading verdict.

    Raises ClaudeServiceError on any failure — no fallback is provided.
    """
    import traceback

    import anthropic

    from app.config import settings
    from app.schemas.agents import InstrumentRecommendation, OptionsGuidance

    api_key = (settings.anthropic_api_key or "").strip()
    if not api_key:
        raise ClaudeServiceError(
            "ANTHROPIC_API_KEY is not configured. "
            "Add your Anthropic API key to the .env file (ANTHROPIC_API_KEY=sk-ant-...) "
            "and restart the server to enable AI-powered analysis."
        )

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)

        user_msg = _fmt_agents_prompt(symbol, m, f, tech, opt, risk, sent, decision_aids)
        user_msg += (
            "\n\nBased on all agent data above, provide your trading analysis verdict. "
            "Be specific and cite actual numbers from the data."
        )

        response = await client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[_VERDICT_TOOL],
            tool_choice={"type": "tool", "name": "submit_analysis_verdict"},
            messages=[{"role": "user", "content": user_msg}],
        )

    except anthropic.AuthenticationError as exc:
        raise ClaudeServiceError(
            f"Anthropic API authentication failed — check that ANTHROPIC_API_KEY is correct. "
            f"Detail: {exc}"
        ) from exc
    except anthropic.RateLimitError as exc:
        raise ClaudeServiceError(
            f"Anthropic API rate limit reached — too many requests. "
            f"Wait a moment and retry. Detail: {exc}"
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise ClaudeServiceError(
            f"Could not connect to Anthropic API — check network connectivity. "
            f"Detail: {exc}"
        ) from exc
    except anthropic.APIStatusError as exc:
        raise ClaudeServiceError(
            f"Anthropic API returned status {exc.status_code}. Detail: {exc.message}"
        ) from exc
    except Exception as exc:
        tb = traceback.format_exc()
        raise ClaudeServiceError(
            f"Unexpected error calling Claude ({type(exc).__name__}): {exc}\n\n{tb}"
        ) from exc

    tool_block = next(
        (b for b in response.content if getattr(b, "type", None) == "tool_use"),
        None,
    )
    if tool_block is None:
        raise ClaudeServiceError(
            "Claude returned a response with no tool-use block — "
            "the model did not call submit_analysis_verdict as expected. "
            f"Response stop_reason: {response.stop_reason}"
        )

    inp: dict[str, Any] = tool_block.input  # type: ignore[attr-defined]
    rec_str: str = inp["instrument_recommendation"]

    options_guidance: OptionsGuidance | None = None
    if rec_str == "options" and inp.get("options_strategy_family"):
        options_guidance = OptionsGuidance(
            strategy_family=inp["options_strategy_family"],
            rationale_codes=inp.get("options_rationale_codes", []),
            strike_guidance=inp.get(
                "options_strike_guidance",
                "Use your broker chain to identify appropriate strikes.",
            ),
            max_loss_scenario=inp.get(
                "options_max_loss_scenario",
                "Define max loss before entry.",
            ),
            profit_targets_scenario=inp.get(
                "options_profit_targets",
                ["Take profits at 50% of max credit or target; exit before expiry."],
            ),
        )

    log.info(
        "claude_verdict_ok",
        symbol=symbol,
        recommendation=rec_str,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )

    return ClaudeVerdict(
        instrument_recommendation=InstrumentRecommendation(rec_str),
        confidence_note=inp["confidence_note"],
        options_guidance=options_guidance,
        summary_headline=inp["summary_headline"],
        user_answers=[
            inp["q1_thesis_answer"],
            inp["q2_invalidation_answer"],
            inp["q3_max_loss_answer"],
            inp["q4_assignment_answer"],
        ],
    )
