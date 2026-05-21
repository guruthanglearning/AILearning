"use client";

import type { OptionsMetricRow, SupervisorVerdict, TechnicalsSnapshot } from "@/types/api";

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
    signals.push({ category: "Options", name: "Liquidity", value: row.liquidity, side: good ? "options" : thin ? "stock" : "neutral", note: good ? "Adequate chain liquidity — options viable" : thin ? "Thin chain — wide spreads; stock preferred" : "Unknown liquidity — verify on your broker" });
  }
  if (row.expected_move) {
    signals.push({ category: "Options", name: "Expected Move", value: row.expected_move, side: "neutral", note: "Market-implied move; size positions accordingly" });
  }
  if (row.execution_quality) {
    signals.push({ category: "Options", name: "Execution Quality", value: "Limit orders", side: "neutral", note: row.execution_quality });
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

// ── Score aggregation ─────────────────────────────────────────────────────────

function scoreToVerdict(stockCount: number, optionsCount: number, total: number): {
  verdict: string; color: string; pct: number; rationale: string;
} {
  const net = stockCount - optionsCount;
  const pct = total > 0 ? Math.round((stockCount / total) * 100) : 50;
  if (net >= 6)       return { verdict: "Strong Stock Signal", color: "text-green-400", pct, rationale: "Majority of indicators favour a direct stock position. Momentum, trend, and volatility all support ownership." };
  if (net >= 3)       return { verdict: "Lean Stock", color: "text-green-300", pct, rationale: "More indicators favour stock than options. Stock entry is the primary choice; consider a small protective put if risk averse." };
  if (net <= -6)      return { verdict: "Strong Options Signal", color: "text-indigo-400", pct, rationale: "Most indicators favour an options structure. High volatility, overbought conditions, or weak trend suggest defined-risk plays." };
  if (net <= -3)      return { verdict: "Lean Options", color: "text-indigo-300", pct, rationale: "More indicators favour options. Consider a credit spread or debit spread over outright stock for better risk control." };
  return { verdict: "Mixed — Further Analysis Needed", color: "text-amber-400", pct: 50, rationale: "Indicators are split. Wait for a clearer signal, reduce position size, or use a smaller defined-risk options structure." };
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

  if (!tech) return null;

  // Build all signals
  const signals: IndicatorSignal[] = [
    evalEma20(tech), evalEma200(tech),
    evalDma20(tech), evalDma50(tech), evalDma200(tech),
    evalRsi7(tech), evalRsi14(tech), evalRsi200(tech),
    ...evalMacd(tech),
    evalObv(tech),
    evalAtr14(tech), evalAtr50(tech),
    ...eval52w(tech),
    ...nonSummaryRows.flatMap(evalOptionsRow),
  ];

  const stockCount   = signals.filter(s => s.side === "stock").length;
  const optionsCount = signals.filter(s => s.side === "options").length;
  const neutralCount = signals.filter(s => s.side === "neutral").length;
  const total = signals.length;

  const { verdict: verdictLabel, color, rationale } = scoreToVerdict(stockCount, optionsCount, total);

  // Group by category
  const seen = new Set<string>();
  const categories = signals.map(s => s.category).filter(c => { if (seen.has(c)) return false; seen.add(c); return true; });

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-medium text-gray-400">Stock vs Options — Trade Guidance</h2>

      {/* Verdict card */}
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className={`text-lg font-bold ${color}`}>{verdictLabel}</span>
          <span className="text-xs text-gray-500">{total} indicators evaluated</span>
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
        <p className="text-xs text-amber-600 italic">Hypothetical analysis only — not investment advice.</p>
      </div>

      {/* Per-category signal tables */}
      {categories.map(cat => {
        const catSignals = signals.filter(s => s.category === cat);
        return (
          <div key={cat} className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
            <div className="px-3 py-2 bg-gray-800/60 border-b border-gray-800">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{cat}</span>
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
    </div>
  );
}
