"use client";

import { useState } from "react";

import type {
  FundamentalsSnapshot,
  SupervisorVerdict,
  TechnicalsSnapshot,
} from "@/types/api";

interface Props {
  verdict: SupervisorVerdict;
  symbol: string;
}

// ─── Timing verdict derivation ────────────────────────────────────────────────

interface TimingVerdict {
  label: string;
  badgeClass: string;
  tier: "bullish" | "mixed-bullish" | "neutral" | "bearish" | "no-data";
  summary: string;
  bullishCount: number;
  bearishCount: number;
}

function deriveTimingVerdict(verdict: SupervisorVerdict): TimingVerdict {
  const rec = verdict.instrument_recommendation;
  if (rec === "insufficient_data") {
    return {
      label: "Insufficient Data",
      badgeClass: "bg-gray-700/80 text-gray-400",
      tier: "no-data",
      summary: "Not enough data to make a confident timing call.",
      bullishCount: 0,
      bearishCount: 0,
    };
  }
  if (rec === "no_trade") {
    return {
      label: "Hold Off",
      badgeClass: "bg-red-900/60 text-red-300",
      tier: "bearish",
      summary: "Analysis signals this is not the right time to enter a position.",
      bullishCount: 0,
      bearishCount: 1,
    };
  }

  let bull = 0;
  let bear = 0;
  const t = verdict.technicals;

  if (t) {
    const rsi = t.rsi_14 ?? 50;
    if (rsi >= 30 && rsi <= 65) bull++;
    else if (rsi > 70) bear++;

    if (t.macd_6_13 != null && t.macd_6_13_signal != null) {
      if (t.macd_6_13 > t.macd_6_13_signal) bull++;
      else bear++;
      if (t.macd_6_13_hist != null) {
        if (t.macd_6_13_hist > 0) bull++;
        else bear++;
      }
    }

    const trend = (t.trend_hint ?? "").toLowerCase();
    if (trend.includes("bull") || trend.includes("uptrend") || trend.includes("up")) bull++;
    else if (trend.includes("bear") || trend.includes("downtrend") || trend.includes("down")) bear++;

    if (t.obv_slope != null) {
      if (t.obv_slope > 0) bull++;
      else bear++;
    }
  }

  const sentiment = verdict.sentiment_score ?? 0;
  if (sentiment >= 0.2) bull++;
  else if (sentiment <= -0.2) bear++;

  const checklist = verdict.decision_aids?.checklist ?? [];
  checklist.forEach((c) => {
    if (c.state === "pass") bull += c.weight ?? 1;
    else if (c.state === "fail") bear += c.weight ?? 1;
  });

  const total = bull + bear;
  const ratio = total > 0 ? bull / total : 0.5;

  if (ratio >= 0.68)
    return {
      label: "Good Entry",
      badgeClass: "bg-green-900/60 text-green-300",
      tier: "bullish",
      summary:
        "Multiple signals are aligned — technical momentum, sentiment, and fundamentals support entry.",
      bullishCount: bull,
      bearishCount: bear,
    };
  if (ratio >= 0.54)
    return {
      label: "Cautious Entry",
      badgeClass: "bg-yellow-900/60 text-yellow-300",
      tier: "mixed-bullish",
      summary:
        "Mostly positive but some risk factors present — consider sizing down or waiting for confirmation.",
      bullishCount: bull,
      bearishCount: bear,
    };
  if (ratio >= 0.44)
    return {
      label: "Mixed Signals",
      badgeClass: "bg-gray-600/80 text-gray-300",
      tier: "neutral",
      summary:
        "Conflicting signals across indicators — a clearer setup is needed before committing capital.",
      bullishCount: bull,
      bearishCount: bear,
    };
  return {
    label: "Risky Entry",
    badgeClass: "bg-red-900/60 text-red-300",
    tier: "bearish",
    summary:
      "Signals lean negative — elevated risk of an adverse move. Wait for conditions to improve.",
    bullishCount: bull,
    bearishCount: bear,
  };
}

// ─── Signal bar ───────────────────────────────────────────────────────────────

function SignalBar({ bull, bear }: { bull: number; bear: number }) {
  const total = bull + bear;
  if (total === 0) return null;
  const bullPct = Math.round((bull / total) * 100);
  return (
    <div className="flex items-center gap-2 text-xs text-gray-500">
      <span className="w-14 text-right text-green-400">{bullPct}% bull</span>
      <div className="flex-1 h-1.5 rounded-full bg-gray-800 overflow-hidden">
        <div
          className="h-full bg-green-500/70 rounded-full"
          style={{ width: `${bullPct}%` }}
        />
      </div>
      <span className="w-14 text-red-400">{100 - bullPct}% bear</span>
    </div>
  );
}

// ─── Section: Bottom line ─────────────────────────────────────────────────────

function BottomLine({
  timing,
  verdict,
  symbol,
}: {
  timing: TimingVerdict;
  verdict: SupervisorVerdict;
  symbol: string;
}) {
  const recLabel: Record<string, string> = {
    stock: "Direct Stock",
    options: "Options Play",
    no_trade: "No Trade",
    insufficient_data: "Insufficient Data",
  };
  return (
    <div className="rounded-md bg-gray-800/60 border border-gray-700/50 p-3 space-y-2">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Bottom Line — {symbol}</p>
      <p className="text-sm text-gray-100">{timing.summary}</p>
      <div className="flex flex-wrap gap-3 text-xs pt-1">
        <span className="text-gray-500">
          Instrument:{" "}
          <span className="text-gray-200 font-medium">
            {recLabel[verdict.instrument_recommendation] ?? verdict.instrument_recommendation}
          </span>
        </span>
        {verdict.confidence_note && (
          <span className="text-gray-500">
            Confidence: <span className="text-gray-200">{verdict.confidence_note}</span>
          </span>
        )}
        {verdict.has_upcoming_earnings && verdict.earnings_days_away != null && (
          <span className="text-amber-400/90">
            ⚠ Earnings in {verdict.earnings_days_away}d — elevated risk
          </span>
        )}
      </div>
      <SignalBar bull={timing.bullishCount} bear={timing.bearishCount} />
    </div>
  );
}

// ─── Section: Technicals ─────────────────────────────────────────────────────

function rsiColor(rsi: number): string {
  if (rsi > 70) return "text-red-400";
  if (rsi < 30) return "text-amber-400";
  if (rsi >= 50) return "text-green-400";
  return "text-gray-400";
}

function TechnicalsSection({ t }: { t: TechnicalsSnapshot }) {
  const rsi = t.rsi_14;
  const macdBull =
    t.macd_6_13 != null && t.macd_6_13_signal != null
      ? t.macd_6_13 > t.macd_6_13_signal
      : null;
  const macdHist = t.macd_6_13_hist;
  const accumulating = t.obv_slope != null ? t.obv_slope > 0 : null;

  const rows: [string, string, string][] = [];

  if (t.trend_hint) rows.push(["Trend", t.trend_hint, "text-gray-200"]);

  if (rsi != null)
    rows.push([
      "RSI-14",
      `${rsi.toFixed(1)}${rsi > 70 ? " — Overbought" : rsi < 30 ? " — Oversold" : rsi >= 50 ? " — Bullish zone" : " — Bearish zone"}`,
      rsiColor(rsi),
    ]);

  if (macdBull != null)
    rows.push([
      "MACD (6/13)",
      macdBull
        ? `Bullish crossover${macdHist != null ? ` (hist ${macdHist > 0 ? "+" : ""}${macdHist!.toFixed(3)})` : ""}`
        : `Bearish crossover${macdHist != null ? ` (hist ${macdHist!.toFixed(3)})` : ""}`,
      macdBull ? "text-green-400" : "text-red-400",
    ]);

  if (accumulating != null)
    rows.push([
      "OBV",
      accumulating ? "Accumulation (buying pressure)" : "Distribution (selling pressure)",
      accumulating ? "text-green-400" : "text-red-400",
    ]);

  if (t.atr_pct_14 != null)
    rows.push([
      "ATR-14",
      `${(t.atr_pct_14 * 100).toFixed(2)}% daily range`,
      t.atr_pct_14 > 0.04 ? "text-amber-400" : "text-gray-300",
    ]);

  if (t.sma_20 != null && t.sma_50 != null)
    rows.push([
      "SMA 20 / 50",
      t.sma_20 > t.sma_50 ? "20 > 50 — short-term bullish" : "20 < 50 — short-term bearish",
      t.sma_20 > t.sma_50 ? "text-green-400" : "text-red-400",
    ]);

  if (rows.length === 0) return null;

  return (
    <div>
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Technical Momentum
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
        {rows.map(([label, value, cls]) => (
          <div key={label} className="flex justify-between text-xs gap-2">
            <span className="text-gray-500 shrink-0">{label}</span>
            <span className={`${cls} text-right`}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Section: Fundamentals ───────────────────────────────────────────────────

function FundamentalsSection({ f }: { f: FundamentalsSnapshot }) {
  const rows: [string, string, string][] = [];

  if (f.company_name) rows.push(["Company", f.company_name, "text-gray-200"]);
  if (f.sector) rows.push(["Sector", f.sector, "text-gray-300"]);

  if (f.pe_ratio != null)
    rows.push([
      "Trailing P/E",
      f.pe_ratio.toFixed(1),
      f.pe_ratio < 15 ? "text-green-400" : f.pe_ratio > 35 ? "text-red-400" : "text-gray-300",
    ]);

  if (f.forward_pe != null)
    rows.push([
      "Forward P/E",
      f.forward_pe.toFixed(1),
      f.forward_pe < 15 ? "text-green-400" : f.forward_pe > 30 ? "text-red-400" : "text-gray-300",
    ]);

  if (f.revenue_growth != null) {
    const pct = (f.revenue_growth * 100).toFixed(1);
    rows.push([
      "Revenue Growth",
      `${f.revenue_growth > 0 ? "+" : ""}${pct}%`,
      f.revenue_growth > 0.1 ? "text-green-400" : f.revenue_growth < 0 ? "text-red-400" : "text-gray-300",
    ]);
  }

  if (f.market_cap != null) {
    const mc =
      f.market_cap >= 1e12
        ? `$${(f.market_cap / 1e12).toFixed(2)}T`
        : f.market_cap >= 1e9
        ? `$${(f.market_cap / 1e9).toFixed(1)}B`
        : `$${(f.market_cap / 1e6).toFixed(0)}M`;
    rows.push(["Market Cap", mc, "text-gray-300"]);
  }

  if (rows.length === 0) return null;

  return (
    <div>
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Fundamentals
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
        {rows.map(([label, value, cls]) => (
          <div key={label} className="flex justify-between text-xs gap-2">
            <span className="text-gray-500 shrink-0">{label}</span>
            <span className={`${cls} text-right`}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Section: Sentiment ──────────────────────────────────────────────────────

function SentimentSection({ verdict }: { verdict: SupervisorVerdict }) {
  const score = verdict.sentiment_score;
  const forecast = verdict.sentiment_forecast;
  if (score == null && !forecast) return null;

  const pct = score != null ? Math.round(((score + 1) / 2) * 100) : 50;
  const label =
    score == null ? "Neutral" : score > 0.5 ? "Very Positive" : score > 0.2 ? "Positive" : score < -0.5 ? "Very Negative" : score < -0.2 ? "Negative" : "Neutral";
  const barColor =
    score == null || Math.abs(score) < 0.2
      ? "bg-gray-500"
      : score > 0
      ? "bg-green-500/70"
      : "bg-red-500/70";

  return (
    <div>
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        Market Sentiment
      </p>
      {score != null && (
        <div className="flex items-center gap-2 text-xs mb-1.5">
          <span className="text-gray-500 w-16 shrink-0">Score</span>
          <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
          </div>
          <span
            className={
              score > 0.2 ? "text-green-400" : score < -0.2 ? "text-red-400" : "text-gray-400"
            }
          >
            {label} ({score > 0 ? "+" : ""}
            {score.toFixed(2)})
          </span>
        </div>
      )}
      {forecast && <p className="text-xs text-gray-400">{forecast}</p>}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export function DeepPositionAnalysisPanel({ verdict, symbol }: Props) {
  const [open, setOpen] = useState(false);
  const timing = deriveTimingVerdict(verdict);

  const hasTechnicals = !!verdict.technicals;
  const hasFundamentals = !!verdict.fundamentals;
  const hasSentiment = verdict.sentiment_score != null || !!verdict.sentiment_forecast;

  return (
    <div className="rounded-lg border border-gray-800 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-900 hover:bg-gray-800/70 transition-colors text-left"
        aria-expanded={open}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-sm font-semibold text-gray-100 shrink-0">
            Deep Position Analysis
          </span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${timing.badgeClass}`}>
            {timing.label}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600 shrink-0 ml-3">
          <span className="hidden sm:inline">Is it the right time to take a position?</span>
          <span>{open ? "▲" : "▼"}</span>
        </div>
      </button>

      {open && (
        <div className="bg-gray-900/50 border-t border-gray-800 p-4 space-y-5">
          <BottomLine timing={timing} verdict={verdict} symbol={symbol} />

          <div className="border-t border-gray-800/60" />

          {hasTechnicals && <TechnicalsSection t={verdict.technicals!} />}
          {hasFundamentals && <FundamentalsSection f={verdict.fundamentals!} />}
          {hasSentiment && <SentimentSection verdict={verdict} />}
        </div>
      )}
    </div>
  );
}
