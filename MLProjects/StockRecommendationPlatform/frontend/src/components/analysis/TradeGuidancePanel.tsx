"use client";

import { useEffect, useState } from "react";

import { getPriceHistory } from "@/lib/api";
import type { OptionsMetricRow, PriceBar, SupervisorVerdict, TechnicalsSnapshot } from "@/types/api";

// ── Option Play types ─────────────────────────────────────────────────────────

type OptionAction = "buy" | "sell" | "hold";
type OptionRight  = "call" | "put" | "neutral";

interface OptionPlay {
  action:            OptionAction;
  right:             OptionRight;
  strategy:          string;
  short_strike_desc: string;
  long_strike_desc:  string | null;
  dte_desc:          string;
  reasons:           string[];
  conviction:        "high" | "medium" | "low";
  caution:           string | null;
}

// ── Option Play computation ───────────────────────────────────────────────────

function roundStrike(p: number): number {
  return Math.round(p / 2.5) * 2.5;
}

function computeOptionPlay(verdict: SupervisorVerdict): OptionPlay | null {
  const tech = verdict.technicals;
  if (!tech) return null;

  const vol  = verdict.decision_aids?.volatility;
  const rows = verdict.decision_aids?.options_metrics_table ?? [];

  // Best spot price: underlying_at_analysis from summary row, fall back to SMA 20
  const spot =
    rows.find(r => r.template_id === "underlying_summary")?.underlying_at_analysis ??
    tech.sma_20;
  if (!spot) return null;

  const atm_iv   = vol?.atm_iv;                   // decimal e.g. 0.20
  const hv       = vol?.hv_20d_annualized;         // decimal e.g. 0.19
  const ivRatio  = atm_iv && hv && hv > 0 ? atm_iv / hv : null;
  const ivPctStr = atm_iv ? `${(atm_iv * 100).toFixed(0)}%` : null;
  const hvPctStr = hv     ? `${(hv * 100).toFixed(0)}%`     : null;

  const trend    = tech.trend_hint;
  const rsi14    = tech.rsi_14;
  const macdHist = tech.macd_6_13_hist;
  const atr14    = tech.atr_pct_14;

  let buyScore = 0, sellScore = 0, callScore = 0, putScore = 0;
  const reasons: string[] = [];

  // IV vs HV
  if (ivRatio !== null) {
    if (ivRatio > 1.15) {
      sellScore += 2;
      reasons.push(`IV ${ivPctStr} > HV ${hvPctStr} — premium elevated, favour selling`);
    } else if (ivRatio < 0.85) {
      buyScore += 2;
      reasons.push(`IV ${ivPctStr} < HV ${hvPctStr} — options priced below realised vol, favour buying`);
    } else {
      reasons.push(`IV ${ivPctStr} ≈ HV ${hvPctStr} — fairly priced; directional signal drives choice`);
    }
  } else if (atm_iv) {
    if (atm_iv > 0.35) { sellScore += 1; reasons.push(`ATM IV ${ivPctStr} elevated — premium selling viable`); }
    else                { buyScore  += 1; reasons.push(`ATM IV ${ivPctStr} — moderate, buying viable`); }
  }

  // Trend
  if (trend === "bullish") {
    callScore += 2;
    reasons.push("Bullish trend: SMA 20 > SMA 50 supports call / put spread");
  } else if (trend === "bearish") {
    putScore += 2;
    reasons.push("Bearish trend: SMA 20 < SMA 50 supports put / call spread short");
  }

  // RSI 14
  if (rsi14 != null) {
    if (rsi14 >= 75) {
      putScore += 1;
      reasons.push(`RSI 14 at ${rsi14.toFixed(0)} — overbought; limit new long delta, favour put or credit call spread`);
    } else if (rsi14 <= 30) {
      callScore += 1;
      reasons.push(`RSI 14 at ${rsi14.toFixed(0)} — oversold; call or bull put spread favoured`);
    }
  }

  // MACD histogram
  if (macdHist != null) {
    if (macdHist > 0) callScore += 1;
    else               putScore  += 1;
  }

  // ATR
  if (atr14 != null) {
    if (atr14 > 2.5) {
      sellScore += 1;
      reasons.push(`ATR 14 at ${atr14.toFixed(1)}% — high daily range; spreads reduce premium outlay`);
    } else if (atr14 < 1.5) {
      buyScore += 1;
    }
  }

  // ── Derive action and direction ──────────────────────────────────────────────
  const action: OptionAction =
    buyScore > sellScore ? "buy" : sellScore > buyScore ? "sell" : "buy";
  const right: OptionRight =
    callScore > putScore + 1 ? "call"
    : putScore > callScore + 1 ? "put"
    : "neutral";

  // ── Conviction ───────────────────────────────────────────────────────────────
  const totalScore = Math.max(buyScore, sellScore) + Math.max(callScore, putScore);
  const conviction: "high" | "medium" | "low" =
    totalScore >= 5 ? "high" : totalScore >= 3 ? "medium" : "low";

  // ── Strategy + strikes ───────────────────────────────────────────────────────
  let strategy          = "";
  let short_strike_desc = "";
  let long_strike_desc: string | null = null;
  let dte_desc          = "";
  let caution: string | null = null;

  const s = (p: number) => `$${roundStrike(p).toFixed(2)}`;

  if (action === "buy" && right === "call") {
    strategy          = "Long Call";
    short_strike_desc = `${s(spot)} – ${s(spot * 1.025)}  (ATM to 2.5% OTM)`;
    dte_desc          = "21 – 45 days";
    if (rsi14 && rsi14 >= 70)
      caution = "RSI overbought — consider a Debit Call Spread instead of naked long call to reduce premium risk";

  } else if (action === "buy" && right === "put") {
    strategy          = "Long Put";
    short_strike_desc = `${s(spot * 0.975)} – ${s(spot)}  (2.5% OTM to ATM)`;
    dte_desc          = "21 – 45 days";

  } else if (action === "buy" && right === "neutral") {
    strategy          = "Debit Call Spread  (wait for direction)";
    short_strike_desc = `Long ${s(spot)}  /  Short ${s(spot * 1.03)}  (ATM / 3% OTM)`;
    long_strike_desc  = `Or: Long Put ${s(spot)}  /  Short ${s(spot * 0.97)}`;
    dte_desc          = "21 – 45 days";
    caution           = "No clear directional bias — confirm trend before committing";

  } else if (action === "sell" && right === "call") {
    strategy          = "Credit Call Spread (Bear Call)";
    short_strike_desc = `Short ${s(spot * 1.03)}  (3% OTM)`;
    long_strike_desc  = `Long  ${s(spot * 1.055)}  (5.5% OTM) — capped loss`;
    dte_desc          = "7 – 21 days";

  } else if (action === "sell" && right === "put") {
    strategy          = "Credit Put Spread (Bull Put)";
    short_strike_desc = `Short ${s(spot * 0.97)}  (3% OTM)`;
    long_strike_desc  = `Long  ${s(spot * 0.945)}  (5.5% OTM) — capped loss`;
    dte_desc          = "7 – 21 days";

  } else {
    // sell + neutral → Iron Condor
    strategy          = "Iron Condor";
    short_strike_desc = `Short Put ${s(spot * 0.96)}  /  Short Call ${s(spot * 1.04)}`;
    long_strike_desc  = `Long Put  ${s(spot * 0.94)}  /  Long Call  ${s(spot * 1.06)}`;
    dte_desc          = "14 – 30 days";
  }

  return {
    action, right, strategy,
    short_strike_desc, long_strike_desc,
    dte_desc, reasons: reasons.slice(0, 4),
    conviction, caution,
  };
}

// ── Signal types ──────────────────────────────────────────────────────────────

type Side = "stock" | "neutral" | "options";

interface IndicatorSignal {
  category: string;
  name: string;
  value: string;
  side: Side;
  note: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmt  = (v: number | null, d = 2) => v == null ? "—" : v.toFixed(d);
const fmtP = (v: number | null, d = 2) => v == null ? "—" : `${v.toFixed(d)}%`;
const fmtD = (v: number | null, d = 2, pre = "$") => v == null ? "—" : `${pre}${v.toFixed(d)}`;
const fmtObv = (v: number | null) => {
  if (v == null) return "—";
  const abs = Math.abs(v);
  const s = v < 0 ? "-" : "";
  if (abs >= 1e9) return `${s}${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${s}${(abs / 1e6).toFixed(2)}M`;
  return `${s}${(abs / 1e3).toFixed(1)}K`;
};

// ── Scoring rules (returns IndicatorSignal for each indicator) ────────────────

function evalEma20(t: TechnicalsSnapshot): IndicatorSignal {
  const ema = t.ema_20; const sma = t.sma_20;
  let side: Side = "neutral"; let note = "Insufficient data";
  if (ema != null && sma != null) {
    if (sma > ema) { side = "stock";   note = "Price above EMA 20 — short-term uptrend"; }
    else           { side = "options"; note = "Price below EMA 20 — short-term weakness"; }
  }
  return { category: "Moving Averages", name: "EMA 20", value: fmtD(ema), side, note };
}

function evalEma200(t: TechnicalsSnapshot): IndicatorSignal {
  const ema = t.ema_200; const sma = t.sma_20;
  let side: Side = "neutral"; let note = "Insufficient data";
  if (ema != null && sma != null) {
    if (sma > ema) { side = "stock";   note = "Price above EMA 200 — long-term bull market"; }
    else           { side = "options"; note = "Price below EMA 200 — long-term downtrend; use defined risk"; }
  }
  return { category: "Moving Averages", name: "EMA 200", value: fmtD(ema), side, note };
}

function evalDma20(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.sma_20; const s50 = t.sma_50;
  let side: Side = "neutral"; let note = "—";
  if (v != null && s50 != null) {
    if (v > s50) { side = "stock";   note = "DMA 20 above DMA 50 — short-term momentum bullish"; }
    else         { side = "options"; note = "DMA 20 below DMA 50 — momentum weakening"; }
  }
  return { category: "Moving Averages", name: "DMA 20 (SMA)", value: fmtD(v), side, note };
}

function evalDma50(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.sma_50; const s200 = t.sma_200;
  let side: Side = "neutral"; let note = "—";
  if (v != null && s200 != null) {
    if (v > s200) { side = "stock";   note = "DMA 50 above DMA 200 — medium-term trend intact"; }
    else          { side = "options"; note = "DMA 50 below DMA 200 — death cross — defined risk preferred"; }
  }
  return { category: "Moving Averages", name: "DMA 50 (SMA)", value: fmtD(v), side, note };
}

function evalDma200(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.sma_200; const spot = t.sma_20;
  let side: Side = "neutral"; let note = "—";
  if (v != null && spot != null) {
    if (spot > v) { side = "stock";   note = "Price above DMA 200 — secular uptrend"; }
    else          { side = "options"; note = "Price below DMA 200 — secular downtrend; hedge or sit out"; }
  }
  return { category: "Moving Averages", name: "DMA 200 (SMA)", value: fmtD(v), side, note };
}

function evalRsi7(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.rsi_7;
  let side: Side = "neutral"; let note = "—";
  if (v != null) {
    if (v >= 80)      { side = "options"; note = "Extreme overbought — wait or buy protective put"; }
    else if (v >= 70) { side = "options"; note = "Overbought short-term — use defined risk on entries"; }
    else if (v <= 20) { side = "stock";   note = "Extreme oversold short-term — aggressive stock entry"; }
    else if (v <= 30) { side = "stock";   note = "Oversold short-term — potential snap-back; stock entry"; }
    else              { side = "neutral"; note = "Neutral short-term momentum"; }
  }
  return { category: "RSI", name: "RSI 7", value: fmt(v, 1), side, note };
}

function evalRsi14(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.rsi_14;
  let side: Side = "neutral"; let note = "—";
  if (v != null) {
    if (v >= 70)      { side = "options"; note = "Overbought — limit new stock exposure; prefer spreads"; }
    else if (v >= 55) { side = "stock";   note = "Healthy bullish momentum — stock entry favored"; }
    else if (v <= 30) { side = "stock";   note = "Oversold — contrarian stock entry or call options"; }
    else if (v <= 45) { side = "options"; note = "Weakening momentum — options hedge or wait"; }
    else              { side = "neutral"; note = "Neutral — neither stock nor options strongly favored"; }
  }
  return { category: "RSI", name: "RSI 14", value: fmt(v, 1), side, note };
}

function evalRsi200(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.rsi_200;
  let side: Side = "neutral"; let note = "—";
  if (v != null) {
    if (v >= 60)      { side = "stock";   note = "Long-term bull regime — stock positions supported"; }
    else if (v <= 40) { side = "options"; note = "Long-term bear regime — defined risk only"; }
    else              { side = "neutral"; note = "Long-term neutral — both instruments viable"; }
  }
  return { category: "RSI", name: "RSI 200", value: fmt(v, 1), side, note };
}

function evalMacd(t: TechnicalsSnapshot): IndicatorSignal[] {
  const line = t.macd_6_13; const sig = t.macd_6_13_signal; const hist = t.macd_6_13_hist;
  const bullish = line != null && sig != null && line > sig;
  const cross: Side = hist != null ? (hist >= 0 ? "stock" : "options") : "neutral";
  const crossNote = hist != null
    ? (hist >= 0 ? "Bullish crossover — momentum building" : "Bearish crossover — momentum fading")
    : "Insufficient data";
  return [
    {
      category: "MACD (6/13/9)", name: "MACD 6 (fast line)",
      value: fmt(line, 4), side: bullish ? "stock" : "options",
      note: bullish ? "Fast EMA above slow — upward momentum" : "Fast EMA below slow — downward pressure",
    },
    {
      category: "MACD (6/13/9)", name: "MACD 13 (slow line)",
      value: fmt(sig, 4), side: cross,
      note: crossNote,
    },
  ];
}

function evalObv(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.obv;
  let side: Side = "neutral"; let note = "—";
  if (v != null) {
    if (v > 0) { side = "stock";   note = "Positive OBV — net buying pressure supports stock"; }
    else       { side = "options"; note = "Negative OBV — net selling pressure; hedge or wait"; }
  }
  return { category: "Volume", name: "OBV", value: fmtObv(v), side, note };
}

function evalAtr14(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.atr_pct_14;
  let side: Side = "neutral"; let note = "—";
  if (v != null) {
    if (v > 3)   { side = "options"; note = "High volatility — options premiums rich; prefer credit spreads"; }
    else if (v > 1.5) { side = "neutral"; note = "Moderate volatility — both stock and options viable"; }
    else         { side = "stock";   note = "Low volatility — cheap options but limited move; stock preferred"; }
  }
  return { category: "Volatility", name: "ATR % 14", value: fmtP(v), side, note };
}

function evalAtr50(t: TechnicalsSnapshot): IndicatorSignal {
  const v = t.atr_pct_50;
  let side: Side = "neutral"; let note = "—";
  if (v != null) {
    if (v > 3)        { side = "options"; note = "High sustained volatility — defined risk structures preferred"; }
    else if (v > 1.5) { side = "neutral"; note = "Moderate sustained volatility — options viable"; }
    else              { side = "stock";   note = "Low sustained volatility — stock position efficient"; }
  }
  return { category: "Volatility", name: "ATR % 50", value: fmtP(v), side, note };
}

function eval52w(t: TechnicalsSnapshot): IndicatorSignal[] {
  const spot = t.sma_20; // proxy
  const high = t.week_52_high; const low = t.week_52_low;
  const signals: IndicatorSignal[] = [];

  let highSide: Side = "neutral"; let highNote = "—";
  if (high != null && spot != null) {
    const pctFromHigh = ((high - spot) / high) * 100;
    if (pctFromHigh < 3)       { highSide = "stock";   highNote = `Within ${pctFromHigh.toFixed(1)}% of 52W high — breakout momentum; stock or call`; }
    else if (pctFromHigh < 10) { highSide = "neutral"; highNote = `${pctFromHigh.toFixed(1)}% below 52W high — potential resistance`; }
    else                       { highSide = "options"; highNote = `${pctFromHigh.toFixed(1)}% below 52W high — range-bound; options spreads`; }
  }
  signals.push({ category: "52-Week Range", name: "52W High", value: fmtD(high), side: highSide, note: highNote });

  let lowSide: Side = "neutral"; let lowNote = "—";
  if (low != null && spot != null) {
    const pctFromLow = ((spot - low) / low) * 100;
    if (pctFromLow < 5)        { lowSide = "options"; lowNote = `Only ${pctFromLow.toFixed(1)}% above 52W low — near support; defined risk`; }
    else if (pctFromLow > 30)  { lowSide = "stock";   lowNote = `${pctFromLow.toFixed(1)}% above 52W low — strong base; stock position solid`; }
    else                       { lowSide = "neutral"; lowNote = `${pctFromLow.toFixed(1)}% above 52W low — mid-range`; }
  }
  signals.push({ category: "52-Week Range", name: "52W Low", value: fmtD(low), side: lowSide, note: lowNote });
  return signals;
}

function evalOptionsRow(row: OptionsMetricRow): IndicatorSignal[] {
  const label = row.strategy_label;
  const signals: IndicatorSignal[] = [];

  if (row.trend_alignment) {
    const s: Side = row.trend_alignment.toLowerCase().startsWith("aligned") ? "options"
                  : row.trend_alignment.toLowerCase().startsWith("counter") ? "neutral"
                  : "neutral";
    signals.push({ category: "Options", name: `Trend Alignment (${label})`, value: row.trend_alignment, side: s, note: s === "options" ? "Options strategy aligned with price trend" : "Options strategy against trend — lower probability" });
  }
  if (row.theta_edge) {
    const pos = row.theta_edge.toLowerCase().startsWith("positive");
    signals.push({ category: "Options", name: `Theta Edge (${label})`, value: row.theta_edge.split("—")[0].trim(), side: pos ? "options" : "neutral", note: pos ? "Time decay works for you — options income strategy" : "Time decay works against you — stock may be simpler" });
  }
  if (row.gamma_risk) {
    const high = row.gamma_risk.toLowerCase().startsWith("high");
    signals.push({ category: "Options", name: `Gamma Risk (${label})`, value: row.gamma_risk.split("—")[0].trim(), side: high ? "options" : "neutral", note: high ? "High gamma near short strike — monitor closely" : "Long gamma — benefits from large moves" });
  }
  if (row.credit_quality && !row.credit_quality.startsWith("N/A")) {
    const good = row.credit_quality.startsWith("Good");
    const fair = row.credit_quality.startsWith("Fair");
    signals.push({ category: "Options", name: `Credit Quality (${label})`, value: row.credit_quality, side: good ? "options" : fair ? "neutral" : "stock", note: good ? "Good credit-to-width ratio — credit spread favored" : fair ? "Fair credit quality — viable with discipline" : "Poor credit quality — stock entry may be more efficient" });
  }
  if (row.liquidity) {
    const good = ["adequate", "good", "high"].some(k => row.liquidity!.toLowerCase().includes(k));
    const thin = row.liquidity.toLowerCase().includes("thin");
    signals.push({ category: "Options", name: `Liquidity (${label})`, value: row.liquidity, side: good ? "options" : thin ? "stock" : "neutral", note: good ? "Adequate chain liquidity — options viable" : thin ? "Thin chain — wide spreads; stock preferred" : "Unknown liquidity — verify on your broker" });
  }
  if (row.expected_move) {
    signals.push({ category: "Options", name: `Expected Move (${label})`, value: row.expected_move, side: "neutral", note: "Market-implied move; size positions accordingly" });
  }
  if (row.execution_quality) {
    signals.push({ category: "Options", name: `Execution Quality (${label})`, value: "Limit orders", side: "neutral", note: row.execution_quality });
  }
  if (row.risk_profile) {
    signals.push({ category: "Options", name: `Risk Profile (${label})`, value: row.risk_profile.slice(0, 30) + "…", side: "neutral", note: row.risk_profile });
  }
  if (row.rule_30pct) {
    signals.push({ category: "Options", name: `30% Rule (${label})`, value: row.rule_30pct.slice(0, 30) + "…", side: "options", note: row.rule_30pct });
  }
  if (row.rule_60pct) {
    signals.push({ category: "Options", name: `60% Rule (${label})`, value: row.rule_60pct.slice(0, 30) + "…", side: "options", note: row.rule_60pct });
  }
  return signals;
}

// ── Sector ETF ────────────────────────────────────────────────────────────────

const SECTOR_ETF: Record<string, string> = {
  "Technology":              "XLK",
  "Consumer Cyclical":       "XLY",
  "Consumer Defensive":      "XLP",
  "Consumer Staples":        "XLP",
  "Healthcare":              "XLV",
  "Health Care":             "XLV",
  "Financial Services":      "XLF",
  "Financials":              "XLF",
  "Energy":                  "XLE",
  "Utilities":               "XLU",
  "Real Estate":             "XLRE",
  "Basic Materials":         "XLB",
  "Materials":               "XLB",
  "Industrials":             "XLI",
  "Communication Services":  "XLC",
  "Telecommunications":      "XLC",
};

function computeEtfPerf(bars: PriceBar[]): { pctChange: number; trend: "bullish" | "bearish" | "flat" } | null {
  const closes = bars.map(b => b.close).filter((c): c is number => c != null);
  if (closes.length < 5) return null;
  const recent = closes.slice(-20);
  const first = recent[0], last = recent[recent.length - 1];
  const pctChange = ((last - first) / first) * 100;
  const trend = pctChange > 1 ? "bullish" : pctChange < -1 ? "bearish" : "flat";
  return { pctChange, trend };
}

function evalSectorEtf(
  etfTicker: string,
  etfPerf: { pctChange: number; trend: "bullish" | "bearish" | "flat" },
  stockTrend: string | null,
): IndicatorSignal[] {
  const sign = etfPerf.pctChange >= 0 ? "+" : "";
  const pctStr = `${etfTicker} ${sign}${etfPerf.pctChange.toFixed(1)}%`;

  const etfSide: Side =
    etfPerf.trend === "bullish" ? "stock" :
    etfPerf.trend === "bearish" ? "options" : "neutral";

  const etfNote =
    etfPerf.trend === "bullish" ? `${etfTicker} sector trending up over 20 days — broad sector tailwind` :
    etfPerf.trend === "bearish" ? `${etfTicker} sector trending down — sector headwind; prefer defined risk` :
    `${etfTicker} sector is flat — no strong macro tailwind or headwind`;

  let alignSide: Side = "neutral";
  let alignNote = "Insufficient trend data to compare stock vs sector";

  if (stockTrend === "bullish" && etfPerf.trend === "bullish") {
    alignSide = "stock";
    alignNote = `Stock trend aligns with bullish ${etfTicker} sector — tailwind confirms long thesis`;
  } else if (stockTrend === "bullish" && etfPerf.trend === "bearish") {
    alignSide = "neutral";
    alignNote = `Stock outperforming a declining ${etfTicker} sector — rotation play; monitor sustainability`;
  } else if (stockTrend === "bullish" && etfPerf.trend === "flat") {
    alignSide = "stock";
    alignNote = `Stock bullish in a flat ${etfTicker} sector — idiosyncratic strength favors stock`;
  } else if (stockTrend === "bearish" && etfPerf.trend === "bullish") {
    alignSide = "options";
    alignNote = `Stock lagging a strong ${etfTicker} sector — relative weakness; options hedge preferred`;
  } else if (stockTrend === "bearish" && etfPerf.trend === "bearish") {
    alignSide = "options";
    alignNote = `Stock and sector both declining — sector headwinds amplify downside; use defined risk`;
  } else if (stockTrend === "bearish") {
    alignSide = "options";
    alignNote = `Stock bearish vs flat ${etfTicker} sector — confirm before entry; options hedge viable`;
  }

  return [
    { category: "Sector ETF", name: `${etfTicker} 20-day Trend`, value: pctStr, side: etfSide, note: etfNote },
    { category: "Sector ETF", name: "Stock vs Sector", value: stockTrend ?? "—", side: alignSide, note: alignNote },
  ];
}

// ── Score aggregation ─────────────────────────────────────────────────────────

interface VerdictResult {
  verdict: string;
  color: string;
  pct: number;
  rationale: string;
  watchList?: string[];
}

function scoreToVerdict(
  stockCount: number,
  optionsCount: number,
  total: number,
  verdict: SupervisorVerdict,
): VerdictResult {
  const net = stockCount - optionsCount;
  const pct = total > 0 ? Math.round((stockCount / total) * 100) : 50;

  // Thresholds scaled for direction-only signal pool (~15–19 signals)
  if (net >= 4)  return { verdict: "Strong Stock Signal",   color: "text-green-400",  pct, rationale: "Majority of direction indicators favour a direct stock position. Momentum, trend, and volatility all support ownership." };
  if (net >= 2)  return { verdict: "Lean Stock",            color: "text-green-300",  pct, rationale: "More direction indicators favour stock than options. Stock entry is the primary choice; consider a small protective put if risk averse." };
  if (net <= -4) return { verdict: "Strong Options Signal", color: "text-indigo-400", pct, rationale: "Most direction indicators favour an options structure. High volatility, overbought conditions, or weak trend suggest defined-risk plays." };
  if (net <= -2) return { verdict: "Lean Options",          color: "text-indigo-300", pct, rationale: "More direction indicators favour options. Consider a credit spread or debit spread over outright stock for better risk control." };

  // ── Balanced zone: apply tie-breaker hierarchy ─────────────────────────────
  const tech      = verdict.technicals;
  const vol       = verdict.decision_aids?.volatility;
  const checklist = verdict.decision_aids?.checklist ?? [];

  let tieScore = 0;
  const reasons:   string[] = [];
  const watchList: string[] = [];

  // 1. Trend direction — highest weight
  const trend = tech?.trend_hint;
  if (trend === "bullish") {
    tieScore += 2;
    reasons.push("bullish technical trend (SMA 20 > SMA 50)");
  } else if (trend === "bearish") {
    tieScore -= 2;
    reasons.push("bearish technical trend (SMA 20 < SMA 50)");
  } else {
    watchList.push("Wait for SMA 20 to cross above SMA 50 before committing to a directional stock position");
  }

  // 2. IV vs realised vol — second most important
  const atm_iv = vol?.atm_iv;
  const hv     = vol?.hv_20d_annualized;
  const ivRatio = atm_iv && hv && hv > 0 ? atm_iv / hv : null;
  const regime  = vol?.regime;
  if (regime === "iv_rich" || (ivRatio && ivRatio > 1.2)) {
    tieScore -= 1.5;
    reasons.push(`IV elevated vs realised vol (ratio ${ivRatio ? (ivRatio * 100).toFixed(0) : "—"}%) — premium selling favoured`);
  } else if (regime === "iv_cheap" || (ivRatio && ivRatio < 0.85)) {
    tieScore += 1;
    reasons.push("IV below realised vol — options cheap; stock or long-premium structure viable");
  } else {
    watchList.push("Check IV rank vs 30-day average: above 50th percentile → favour credit spreads over stock");
  }

  // 3. Earnings risk — binary event raises options priority
  const hasEarnings = checklist.some(c => c.id === "earn" && c.state === "warn");
  if (hasEarnings) {
    tieScore -= 2;
    reasons.push("earnings event approaching — defined-risk options cap gap exposure");
    watchList.push("Size down before the earnings print; an options structure limits binary event risk");
  }

  // 4. RSI 14 momentum
  const rsi = tech?.rsi_14;
  if (rsi != null) {
    if (rsi >= 68)      { tieScore -= 1;    reasons.push(`RSI 14 at ${rsi.toFixed(0)} — overbought, favour options structures`); }
    else if (rsi >= 55) { tieScore += 1;    reasons.push(`RSI 14 at ${rsi.toFixed(0)} — healthy bullish momentum`); }
    else if (rsi <= 32) { tieScore += 0.5;  reasons.push(`RSI 14 at ${rsi.toFixed(0)} — oversold, potential snap-back entry`); }
    else if (rsi <= 45) { tieScore -= 0.5; }
    else watchList.push(`RSI 14 is ${rsi.toFixed(0)} — watch for a push above 55 to confirm bullish momentum before a full stock position`);
  }

  // 5. MACD histogram direction
  const macd = tech?.macd_6_13_hist;
  if (macd != null) {
    tieScore += macd > 0 ? 0.5 : -0.5;
    watchList.push(
      macd > 0
        ? "MACD histogram is positive — confirm it's expanding before adding size"
        : "MACD histogram is negative — wait for a crossover before entering a directional stock position",
    );
  }

  // 6. OBV volume confirmation
  const obv = tech?.obv;
  if (obv != null) {
    if (obv > 0) { tieScore += 0.5; reasons.push("positive OBV confirms net buying pressure"); }
    else         { tieScore -= 0.5; }
  }

  // ── Firm recommendation from tie-score ────────────────────────────────────
  if (tieScore >= 1.5) {
    return {
      verdict: "Lean Stock (Tie-Breaker Applied)",
      color:   "text-green-300",
      pct,
      rationale: `Indicators are near-balanced, but key tie-breakers favour stock: ${reasons.join("; ")}. Enter with a defined stop and 50–75% of normal size until confirmation.`,
      watchList: watchList.length > 0 ? watchList : undefined,
    };
  }

  if (tieScore <= -1.5) {
    return {
      verdict: "Lean Options (Tie-Breaker Applied)",
      color:   "text-indigo-300",
      pct,
      rationale: `Indicators are near-balanced, but key tie-breakers favour an options structure: ${reasons.join("; ")}. Use a credit spread or debit spread with a defined max loss.`,
      watchList: watchList.length > 0 ? watchList : undefined,
    };
  }

  // ── Genuinely borderline: give a slight-edge call + specific criteria ──────
  const slightStock = stockCount >= optionsCount;
  return {
    verdict: slightStock
      ? "Slight Lean Stock — Confirm Before Entering"
      : "Slight Lean Options — Confirm Before Entering",
    color: "text-amber-400",
    pct,
    rationale: slightStock
      ? `Indicators are closely split (${stockCount} stock vs ${optionsCount} options signals). Stock holds a slight edge but conviction is low — use 50% of normal size or substitute with a debit call spread to limit max loss.`
      : `Indicators are closely split (${optionsCount} options vs ${stockCount} stock signals). Options hold a slight edge — use a defined-risk structure (debit or credit spread) rather than outright stock.`,
    watchList: [
      ...watchList,
      "Require at least 2 of the following before entering: MACD histogram positive and expanding, RSI 14 > 55, SMA 20 crossed above SMA 50 in last 3 sessions",
      "Check the sector ETF trend — if it aligns with your thesis, conviction increases",
      "Verify OBV has trended up over the last 5 sessions to confirm accumulation",
      ...(regime !== "iv_rich" && regime !== "iv_cheap"
        ? ["Check IV rank vs 30-day average — above 50th percentile favours selling premium (credit spread) over buying stock"]
        : []),
    ],
  };
}

// ── OptionPlayCard ────────────────────────────────────────────────────────────

const ACTION_STYLE: Record<OptionAction, string> = {
  buy:  "bg-blue-900/40 text-blue-300 border-blue-700",
  sell: "bg-purple-900/40 text-purple-300 border-purple-700",
  hold: "bg-gray-800 text-gray-400 border-gray-700",
};
const RIGHT_STYLE: Record<OptionRight, string> = {
  call:    "bg-green-900/40 text-green-300 border-green-700",
  put:     "bg-red-900/40 text-red-300 border-red-700",
  neutral: "bg-amber-900/40 text-amber-300 border-amber-700",
};
const RIGHT_LABEL: Record<OptionRight, string> = {
  call: "Call", put: "Put", neutral: "Call or Put",
};
const CONVICTION_COLOR: Record<string, string> = {
  high: "text-green-400", medium: "text-amber-400", low: "text-gray-400",
};

function OptionPlayCard({ play }: { play: OptionPlay }) {
  return (
    <div className="bg-gray-900 border border-indigo-800/60 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">
          Options Play Recommendation
        </h3>
        <span className={`text-xs font-medium ${CONVICTION_COLOR[play.conviction]}`}>
          Conviction: {play.conviction.charAt(0).toUpperCase() + play.conviction.slice(1)}
        </span>
      </div>

      {/* Action + Direction badges */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className={`text-sm font-bold px-3 py-1 rounded border ${ACTION_STYLE[play.action]}`}>
          {play.action === "buy" ? "BUY Premium" : play.action === "sell" ? "SELL Premium" : "HOLD"}
        </span>
        <span className={`text-sm font-bold px-3 py-1 rounded border ${RIGHT_STYLE[play.right]}`}>
          {RIGHT_LABEL[play.right]}
        </span>
        <span className="text-sm font-semibold text-white">{play.strategy}</span>
      </div>

      {/* Strike zone + DTE */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="bg-gray-800/60 rounded-md p-3 space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Strike Zone</p>
          <p className="text-sm font-mono text-white">{play.short_strike_desc}</p>
          {play.long_strike_desc && (
            <p className="text-sm font-mono text-gray-400">{play.long_strike_desc}</p>
          )}
        </div>
        <div className="bg-gray-800/60 rounded-md p-3 space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Target DTE</p>
          <p className="text-sm font-mono text-white">{play.dte_desc}</p>
        </div>
      </div>

      {/* Rationale */}
      <div className="space-y-1">
        <p className="text-xs text-gray-500 uppercase tracking-wide">Why this play</p>
        <ul className="space-y-1">
          {play.reasons.map((r, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
              <span className="mt-0.5 text-indigo-400 shrink-0">•</span>
              {r}
            </li>
          ))}
        </ul>
      </div>

      {/* Caution */}
      {play.caution && (
        <div className="flex items-start gap-2 bg-amber-900/20 border border-amber-800/40 rounded px-3 py-2">
          <span className="text-amber-400 text-xs shrink-0 mt-0.5">⚠</span>
          <p className="text-xs text-amber-300">{play.caution}</p>
        </div>
      )}

      <p className="text-xs text-amber-700 italic">Hypothetical only — not investment advice. Verify strikes at your broker.</p>
    </div>
  );
}

// ── Render helpers ────────────────────────────────────────────────────────────

const SIDE_LABEL: Record<Side, string> = { stock: "Stock", options: "Options", neutral: "Neutral" };
const SIDE_BG:    Record<Side, string> = {
  stock:   "bg-green-900/40 text-green-300 border-green-700",
  options: "bg-indigo-900/40 text-indigo-300 border-indigo-700",
  neutral: "bg-gray-800 text-gray-400 border-gray-700",
};
const SIDE_DOT: Record<Side, string> = { stock: "bg-green-500", options: "bg-indigo-500", neutral: "bg-gray-500" };

function SignalBadge({ side }: { side: Side }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border ${SIDE_BG[side]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${SIDE_DOT[side]}`} />
      {SIDE_LABEL[side]}
    </span>
  );
}

function SignalRow({ sig }: { sig: IndicatorSignal }) {
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
      <td className="px-3 py-2 text-xs text-gray-400 whitespace-nowrap">{sig.name}</td>
      <td className="px-3 py-2 text-xs font-mono text-gray-200 whitespace-nowrap">{sig.value}</td>
      <td className="px-3 py-2"><SignalBadge side={sig.side} /></td>
      <td className="px-3 py-2 text-xs text-gray-500">{sig.note}</td>
    </tr>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function TradeGuidancePanel({ verdict }: { verdict: SupervisorVerdict }) {
  const tech = verdict.technicals;
  const rows = verdict.decision_aids?.options_metrics_table ?? [];
  const nonSummaryRows = rows.filter(r => r.template_id !== "underlying_summary");

  // Sector ETF: fetch price history for the mapped ETF ticker
  const sector    = verdict.fundamentals?.sector ?? null;
  const etfTicker = sector ? (SECTOR_ETF[sector] ?? null) : null;
  const [etfBars, setEtfBars] = useState<PriceBar[] | null>(null);

  useEffect(() => {
    if (!etfTicker) return;
    setEtfBars(null);
    getPriceHistory(etfTicker, "1mo")
      .then(r => setEtfBars(r.data))
      .catch(() => setEtfBars([]));
  }, [etfTicker]);

  if (!tech) return null;

  const optionPlay = computeOptionPlay(verdict);

  // Direction signals — counted in the stock vs options verdict.
  // These reflect directional bias (trend, momentum, volatility, sector context).
  const dirSignals: IndicatorSignal[] = [
    evalEma20(tech), evalEma200(tech),
    evalDma20(tech), evalDma50(tech), evalDma200(tech),
    evalRsi7(tech), evalRsi14(tech), evalRsi200(tech),
    ...evalMacd(tech),
    evalObv(tech),
    evalAtr14(tech), evalAtr50(tech),
    ...eval52w(tech),
  ];

  // Append sector ETF direction signals when data is ready
  const etfPerf = etfBars && etfBars.length > 0 ? computeEtfPerf(etfBars) : null;
  if (etfTicker && etfPerf) {
    dirSignals.push(...evalSectorEtf(etfTicker, etfPerf, tech.trend_hint));
  }

  // Options execution signals — informational only, NOT counted in verdict.
  // These describe how well a specific options strategy is positioned
  // (theta, gamma, credit quality, liquidity) — not whether options beats stock.
  const execSignals: IndicatorSignal[] = nonSummaryRows.flatMap(evalOptionsRow);

  // All signals for display (direction first, then execution)
  const allSignals = [...dirSignals, ...execSignals];

  const stockCount   = dirSignals.filter(s => s.side === "stock").length;
  const optionsCount = dirSignals.filter(s => s.side === "options").length;
  const neutralCount = dirSignals.filter(s => s.side === "neutral").length;
  const total = dirSignals.length;

  const { verdict: verdictLabel, color, rationale, watchList } = scoreToVerdict(stockCount, optionsCount, total, verdict);

  // Group by category for display
  const seen = new Set<string>();
  const categories = allSignals.map(s => s.category).filter(c => { if (seen.has(c)) return false; seen.add(c); return true; });

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-medium text-gray-400">Stock vs Options — Trade Guidance</h2>

      {/* Verdict card */}
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span className={`text-lg font-bold ${color}`}>{verdictLabel}</span>
          <span className="text-xs text-gray-500">{total} direction indicators scored</span>
        </div>

        {/* Score bar */}
        <div className="space-y-1">
          <div className="flex h-3 rounded-full overflow-hidden bg-gray-800">
            <div className="bg-green-600 transition-all" style={{ width: `${Math.round(stockCount/total*100)}%` }} title={`Stock: ${stockCount}`} />
            <div className="bg-gray-700 transition-all" style={{ width: `${Math.round(neutralCount/total*100)}%` }} title={`Neutral: ${neutralCount}`} />
            <div className="bg-indigo-600 transition-all" style={{ width: `${Math.round(optionsCount/total*100)}%` }} title={`Options: ${optionsCount}`} />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span className="text-green-400">Stock: {stockCount}</span>
            <span>Neutral: {neutralCount}</span>
            <span className="text-indigo-400">Options: {optionsCount}</span>
          </div>
        </div>

        <p className="text-xs text-gray-400 leading-relaxed">{rationale}</p>

        {watchList && watchList.length > 0 && (
          <div className="space-y-1.5 border-t border-gray-700 pt-3">
            <p className="text-xs font-semibold text-amber-400 uppercase tracking-wide">Before entering — confirm these signals:</p>
            <ul className="space-y-1">
              {watchList.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
                  <span className="text-amber-500 shrink-0 mt-0.5">→</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-xs text-amber-600 italic">Hypothetical analysis only — not investment advice.</p>
      </div>

      {/* Options Play Recommendation */}
      {optionPlay && <OptionPlayCard play={optionPlay} />}

      {/* Per-category signal tables */}
      {categories.map(cat => {
        const catSignals = allSignals.filter(s => s.category === cat);
        const isExecOnly = cat === "Options";
        return (
          <div key={cat} className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
            <div className="px-3 py-2 bg-gray-800/60 border-b border-gray-800 flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{cat}</span>
              {cat === "Sector ETF" && etfTicker && (
                <span className="text-xs text-gray-600 font-mono">({etfTicker})</span>
              )}
              {isExecOnly && (
                <span className="text-xs text-gray-500 bg-gray-800 border border-gray-700 px-2 py-0.5 rounded-full">
                  Execution quality — not counted in verdict
                </span>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="px-3 py-1.5 text-xs text-gray-600 font-medium w-44">Indicator</th>
                    <th className="px-3 py-1.5 text-xs text-gray-600 font-medium w-28">Value</th>
                    <th className="px-3 py-1.5 text-xs text-gray-600 font-medium w-24">Signal</th>
                    <th className="px-3 py-1.5 text-xs text-gray-600 font-medium">Analysis</th>
                  </tr>
                </thead>
                <tbody>
                  {catSignals.map((sig, i) => <SignalRow key={i} sig={sig} />)}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}

      {/* Sector ETF loading state — shown only while fetch is in-flight */}
      {etfTicker && etfBars === null && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="px-3 py-2 bg-gray-800/60 border-b border-gray-800 flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Sector ETF</span>
            <span className="text-xs text-gray-600 font-mono">({etfTicker})</span>
          </div>
          <p className="px-3 py-3 text-xs text-gray-500 italic">Loading {etfTicker} sector data…</p>
        </div>
      )}
    </div>
  );
}
