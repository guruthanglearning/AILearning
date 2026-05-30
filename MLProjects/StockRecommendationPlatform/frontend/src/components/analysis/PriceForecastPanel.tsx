"use client";

import type { SupervisorVerdict } from "@/types/api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface SignalContrib {
  name: string;
  bias: number; // daily fraction, e.g. 0.003
  note: string;
}

interface ForecastPoint {
  days:      number;
  label:     string;
  price:     number;
  low:       number;
  high:      number;
  pctChange: number;
  direction: "up" | "down" | "flat";
}

interface ForecastResult {
  spot:          number;
  dailyBias:     number;
  sigmaDaily:    number;
  points:        ForecastPoint[];
  contributions: SignalContrib[];
  dataQuality:   "full" | "partial" | "insufficient";
}

// ── Model ─────────────────────────────────────────────────────────────────────

function extractSentimentScore(verdict: SupervisorVerdict): number | null {
  // Prefer the direct field; fall back to parsing the agent headline
  if (verdict.sentiment_score != null) return verdict.sentiment_score;
  const agent = verdict.agent_contributions.find(a =>
    a.agent_name.toLowerCase().includes("sentiment")
  );
  if (!agent) return null;
  const m = agent.headline.match(/([+-]?\d+\.\d+)/);
  return m ? parseFloat(m[1]) : null;
}

function computeForecast(verdict: SupervisorVerdict): ForecastResult | null {
  const tech = verdict.technicals;
  if (!tech) return null;

  // Spot price: prefer underlying_at_analysis from options summary, fall back to SMA 20
  const rows = verdict.decision_aids?.options_metrics_table ?? [];
  const spot =
    rows.find(r => r.template_id === "underlying_summary")?.underlying_at_analysis ??
    tech.sma_20;
  if (!spot || spot <= 0) return null;

  const sigmaDaily = (tech.atr_pct_14 ?? 1.5) / 100;
  const contribs: SignalContrib[] = [];
  let bias = 0;

  // 1. Trend (SMA 20 vs SMA 50)
  if (tech.trend_hint === "bullish") {
    bias += 0.003;
    contribs.push({ name: "Trend (Bullish)", bias: 0.003, note: "SMA 20 > SMA 50 → +0.30%/day" });
  } else if (tech.trend_hint === "bearish") {
    bias -= 0.003;
    contribs.push({ name: "Trend (Bearish)", bias: -0.003, note: "SMA 20 < SMA 50 → −0.30%/day" });
  }

  // 2. RSI 14 mean-reversion
  const rsi = tech.rsi_14;
  if (rsi != null) {
    if (rsi >= 70) {
      bias -= 0.002;
      contribs.push({ name: `RSI 14 = ${rsi.toFixed(0)}`, bias: -0.002, note: "Overbought → −0.20%/day mean reversion" });
    } else if (rsi <= 30) {
      bias += 0.002;
      contribs.push({ name: `RSI 14 = ${rsi.toFixed(0)}`, bias:  0.002, note: "Oversold → +0.20%/day mean reversion" });
    } else if (rsi >= 50) {
      bias += 0.001;
      contribs.push({ name: `RSI 14 = ${rsi.toFixed(0)}`, bias:  0.001, note: "Bullish momentum zone → +0.10%/day" });
    } else {
      bias -= 0.001;
      contribs.push({ name: `RSI 14 = ${rsi.toFixed(0)}`, bias: -0.001, note: "Bearish momentum zone → −0.10%/day" });
    }
  }

  // 3. MACD histogram
  const hist = tech.macd_6_13_hist;
  if (hist != null) {
    const b = hist > 0 ? 0.001 : -0.001;
    bias += b;
    contribs.push({
      name: `MACD Hist = ${hist.toFixed(3)}`,
      bias: b,
      note: hist > 0 ? "Bullish crossover → +0.10%/day" : "Bearish crossover → −0.10%/day",
    });
  }

  // 4. EMA 200 position
  if (tech.ema_200 != null && tech.sma_20 != null) {
    const b = tech.sma_20 > tech.ema_200 ? 0.001 : -0.001;
    bias += b;
    contribs.push({
      name: "EMA 200 Position",
      bias: b,
      note: tech.sma_20 > tech.ema_200 ? "Price above EMA 200 → +0.10%/day" : "Price below EMA 200 → −0.10%/day",
    });
  }

  // 5. SMA 20/50 cross
  if (tech.sma_20 != null && tech.sma_50 != null) {
    const b = tech.sma_20 > tech.sma_50 ? 0.001 : -0.001;
    bias += b;
    contribs.push({
      name: "SMA 20 / SMA 50 Cross",
      bias: b,
      note: tech.sma_20 > tech.sma_50 ? "Golden cross → +0.10%/day" : "Death cross → −0.10%/day",
    });
  }

  // 6. Sentiment ML score — clamped to ±0.002
  const sentScore = extractSentimentScore(verdict);
  if (sentScore != null) {
    const b = Math.max(-0.002, Math.min(0.002, sentScore * 0.002));
    bias += b;
    contribs.push({
      name: `Sentiment = ${sentScore.toFixed(3)}`,
      bias: b,
      note: `ML score scaled to ±0.20%/day → ${(b * 100).toFixed(3)}%/day`,
    });
  }

  // Build horizon forecasts
  const points: ForecastPoint[] = [1, 5, 10].map(days => {
    const price     = spot * Math.pow(1 + bias, days);
    const halfWidth = spot * sigmaDaily * Math.sqrt(days);
    const low       = Math.max(0.01, price - halfWidth);
    const high      = price + halfWidth;
    const pctChange = ((price - spot) / spot) * 100;
    const direction = pctChange >  0.05 ? "up"
                    : pctChange < -0.05 ? "down"
                    : "flat";
    const label = days === 1 ? "1 Day" : days === 5 ? "5 Days" : "10 Days";
    return { days, label, price, low, high, pctChange, direction };
  });

  const dataQuality: "full" | "partial" | "insufficient" =
    contribs.length >= 5 ? "full" : contribs.length >= 2 ? "partial" : "insufficient";

  return { spot, dailyBias: bias, sigmaDaily, points, contributions: contribs, dataQuality };
}

// ── UI ────────────────────────────────────────────────────────────────────────

const DIR_STYLE: Record<string, string> = {
  up:   "text-green-400",
  down: "text-red-400",
  flat: "text-gray-400",
};
const DIR_ARROW: Record<string, string> = { up: "↑", down: "↓", flat: "→" };
const DIR_BORDER: Record<string, string> = {
  up:   "bg-green-900/20 border-green-800/60",
  down: "bg-red-900/20 border-red-800/60",
  flat: "bg-gray-900 border-gray-700",
};

const biasColor = (b: number) =>
  b > 0 ? "text-green-400" : b < 0 ? "text-red-400" : "text-gray-400";

function ForecastCard({ point }: { point: ForecastPoint }) {
  return (
    <div className={`rounded-lg border p-4 space-y-3 ${DIR_BORDER[point.direction]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          {point.label}
        </span>
        <span className={`text-2xl font-bold leading-none ${DIR_STYLE[point.direction]}`}>
          {DIR_ARROW[point.direction]}
        </span>
      </div>

      <div>
        <p className={`text-2xl font-bold font-mono ${DIR_STYLE[point.direction]}`}>
          ${point.price.toFixed(2)}
        </p>
        <p className={`text-sm font-medium mt-0.5 ${DIR_STYLE[point.direction]}`}>
          {point.pctChange >= 0 ? "+" : ""}{point.pctChange.toFixed(2)}%
        </p>
      </div>

      <div className="bg-black/20 rounded p-2 space-y-0.5">
        <p className="text-xs text-gray-500">
          Range (±{Math.sqrt(point.days).toFixed(1)}× ATR)
        </p>
        <p className="text-xs font-mono text-gray-300">
          ${point.low.toFixed(2)} – ${point.high.toFixed(2)}
        </p>
      </div>
    </div>
  );
}

export function PriceForecastPanel({ verdict }: { verdict: SupervisorVerdict }) {
  const forecast = computeForecast(verdict);
  if (!forecast) return null;

  const { spot, dailyBias, sigmaDaily, points, contributions, dataQuality } = forecast;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-sm font-medium text-gray-400">Price Forecast</h2>
        {dataQuality !== "full" && (
          <span className="text-xs text-amber-500 bg-amber-900/20 border border-amber-800/40 px-2 py-0.5 rounded">
            {dataQuality === "partial" ? "Partial signals — lower confidence" : "Insufficient signals"}
          </span>
        )}
      </div>

      {/* Prominent model disclaimer */}
      <div className="flex items-start gap-2 bg-amber-900/20 border border-amber-700/50 rounded-lg px-4 py-3">
        <span className="text-amber-400 font-bold shrink-0 mt-0.5">⚠</span>
        <p className="text-xs text-amber-300 leading-relaxed">
          <strong>Illustration only — do not use for trade entries, exits, or stops.</strong>{" "}
          Price projections use fixed momentum coefficients that are not statistically calibrated.
          The dollar targets shown are directional bias visualisations, not predictions.
          Actual prices can differ significantly within the confidence range.
        </p>
      </div>

      {/* Summary bar */}
      <div className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 flex flex-wrap gap-6 items-center">
        <div>
          <p className="text-xs text-gray-500">Base Price</p>
          <p className="text-lg font-bold font-mono text-white">${spot.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Net Daily Bias</p>
          <p className={`text-lg font-bold font-mono ${biasColor(dailyBias)}`}>
            {dailyBias >= 0 ? "+" : ""}{(dailyBias * 100).toFixed(3)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Daily Vol (ATR)</p>
          <p className="text-lg font-bold font-mono text-white">
            {(sigmaDaily * 100).toFixed(2)}%
          </p>
        </div>
        <p className="text-xs text-gray-600 ml-auto self-end italic">
          Rules-based momentum model
        </p>
      </div>

      {/* 3 forecast cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {points.map(p => <ForecastCard key={p.days} point={p} />)}
      </div>

      {/* Signal breakdown table */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <div className="px-3 py-2 bg-gray-800/60 border-b border-gray-800">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Signal Breakdown
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="px-3 py-1.5 text-xs text-gray-600 font-medium">Signal</th>
                <th className="px-3 py-1.5 text-xs text-gray-600 font-medium w-24">Daily Bias</th>
                <th className="px-3 py-1.5 text-xs text-gray-600 font-medium">Explanation</th>
              </tr>
            </thead>
            <tbody>
              {contributions.map((c, i) => (
                <tr key={i} className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
                  <td className="px-3 py-2 text-xs text-gray-300 whitespace-nowrap">{c.name}</td>
                  <td className={`px-3 py-2 text-xs font-mono whitespace-nowrap ${biasColor(c.bias)}`}>
                    {c.bias >= 0 ? "+" : ""}{(c.bias * 100).toFixed(3)}%
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-500">{c.note}</td>
                </tr>
              ))}
              <tr className="border-t border-gray-700 bg-gray-800/40">
                <td className="px-3 py-2 text-xs font-semibold text-gray-300">Total</td>
                <td className={`px-3 py-2 text-xs font-bold font-mono ${biasColor(dailyBias)}`}>
                  {dailyBias >= 0 ? "+" : ""}{(dailyBias * 100).toFixed(3)}%
                </td>
                <td className="px-3 py-2 text-xs text-gray-600">Compounded over forecast horizon</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-xs text-amber-700 italic">
        Statistical model only — not investment advice. Forecasts compound daily bias with ATR-scaled random walk envelope. Actual prices can differ significantly.
      </p>
    </div>
  );
}
