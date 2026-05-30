"use client";

import type { SupervisorVerdict } from "@/types/api";

function fmtPrice(v: number | null): string {
  if (v == null) return "—";
  return `$${v.toFixed(2)}`;
}

function fmtPct(v: number): string {
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}

interface ZoneRow {
  label: string;
  value: string;
  sub?: string;
  color: string;
  bg: string;
}

function ZoneCard({ label, value, sub, color, bg }: ZoneRow) {
  return (
    <div className={`rounded-lg border p-3 space-y-0.5 ${bg}`}>
      <p className="text-xs text-gray-500 uppercase tracking-wide font-medium">{label}</p>
      <p className={`text-lg font-bold font-mono ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500">{sub}</p>}
    </div>
  );
}

export function EntryExitCard({ verdict }: { verdict: SupervisorVerdict }) {
  const tech = verdict.technicals;
  if (!tech) return null;

  // Derive spot price
  const rows = verdict.decision_aids?.options_metrics_table ?? [];
  const spot =
    rows.find(r => r.template_id === "underlying_summary")?.underlying_at_analysis ??
    tech.sma_20;
  if (!spot || spot <= 0) return null;

  const atrAbs = spot * ((tech.atr_pct_14 ?? 1.5) / 100);
  const bullish = tech.trend_hint === "bullish";

  // Entry zone: near SMA 20 support (bullish) or SMA 20 resistance (bearish)
  const entryLow  = (tech.sma_20 ?? spot * 0.99) * 0.995;
  const entryHigh = (tech.sma_20 ?? spot * 1.01) * 1.005;

  // Stop loss: below SMA 50 or 2× ATR below spot
  const sma50Stop  = tech.sma_50 ? tech.sma_50 * 0.995 : null;
  const atrStop    = spot - 2 * atrAbs;
  const stopLoss   = bullish
    ? (sma50Stop != null ? Math.max(sma50Stop, atrStop) : atrStop)
    : (sma50Stop != null ? Math.min(sma50Stop, spot + 2 * atrAbs) : spot + 2 * atrAbs);

  // Targets: use 52w high as resistance reference
  const w52High = tech.week_52_high;
  const t1 = bullish
    ? (w52High ? Math.min(spot * 1.05, w52High) : spot * 1.05)
    : (w52High ? Math.min(spot * 0.95, w52High * 0.95) : spot * 0.95);
  const t2 = bullish
    ? (w52High ? Math.max(w52High, spot * 1.10) : spot * 1.10)
    : spot * 0.90;

  // R:R for bullish (long) scenario
  const risk   = Math.abs(spot - stopLoss);
  const reward = Math.abs(t1 - spot);
  const rr     = risk > 0 ? reward / risk : 0;
  const rrLabel = rr >= 2 ? `${rr.toFixed(1)}:1 — Favorable` : rr >= 1 ? `${rr.toFixed(1)}:1 — Acceptable` : `${rr.toFixed(1)}:1 — Tight`;
  const rrColor = rr >= 2 ? "text-green-400" : rr >= 1 ? "text-amber-400" : "text-red-400";

  const stopPct   = ((stopLoss - spot) / spot) * 100;
  const t1Pct     = ((t1 - spot) / spot) * 100;
  const t2Pct     = ((t2 - spot) / spot) * 100;

  const isExtended = spot > entryHigh * 1.015; // price is >1.5% above entry zone top

  const zones: ZoneRow[] = [
    {
      label: "Entry Zone",
      value: `${fmtPrice(entryLow)} – ${fmtPrice(entryHigh)}`,
      sub: bullish ? "Near SMA 20 support" : "Near SMA 20 resistance",
      color: "text-blue-300",
      bg: "bg-blue-900/20 border-blue-800/40",
    },
    {
      label: "Stop Loss",
      value: fmtPrice(stopLoss),
      sub: `${fmtPct(stopPct)} from spot · 2× ATR floor`,
      color: "text-red-400",
      bg: "bg-red-900/20 border-red-800/40",
    },
    {
      label: "Target 1",
      value: fmtPrice(t1),
      sub: fmtPct(t1Pct) + (w52High && bullish ? " · Near 52w high" : ""),
      color: "text-green-400",
      bg: "bg-green-900/20 border-green-800/40",
    },
    {
      label: "Target 2",
      value: fmtPrice(t2),
      sub: fmtPct(t2Pct) + " · Extended move",
      color: "text-emerald-300",
      bg: "bg-emerald-900/10 border-emerald-800/30",
    },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-medium text-gray-400">Entry / Exit Levels</h2>
          <span className="text-xs font-medium text-green-400 bg-green-900/30 border border-green-800/50 px-2 py-0.5 rounded-full">
            Stocks only
          </span>
        </div>
        <span className={`text-xs font-mono font-semibold ${rrColor}`}>
          R:R {rrLabel}
        </span>
      </div>

      <p className="text-xs text-gray-500 leading-relaxed">
        Levels derived from price-chart technicals (SMA, ATR, 52-week range) — relevant when trading the stock directly.
        For options positions, refer to the <span className="text-gray-400">Strike Zone</span> and <span className="text-gray-400">Options Play Recommendation</span> sections above.
      </p>

      {isExtended && (
        <div className="flex items-start gap-2 bg-amber-900/20 border border-amber-800/40 rounded-lg px-3 py-2">
          <span className="text-amber-400 text-xs shrink-0 mt-0.5">→</span>
          <p className="text-xs text-amber-300 leading-relaxed">
            Current price is extended above the entry zone. Either wait for a pullback to SMA 20, or if entering now,
            set your stop loss relative to current price (not the entry zone) and adjust R:R accordingly.
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {zones.map(z => <ZoneCard key={z.label} {...z} />)}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 flex flex-wrap gap-6 text-xs text-gray-500">
        <span>Spot: <span className="text-gray-200 font-mono">{fmtPrice(spot)}</span></span>
        <span>ATR (14d): <span className="text-gray-200 font-mono">{fmtPrice(atrAbs)} ({(tech.atr_pct_14 ?? 0).toFixed(2)}%)</span></span>
        {tech.week_52_high && <span>52w High: <span className="text-gray-200 font-mono">{fmtPrice(tech.week_52_high)}</span></span>}
        {tech.week_52_low  && <span>52w Low: <span className="text-gray-200 font-mono">{fmtPrice(tech.week_52_low)}</span></span>}
      </div>

      <p className="text-xs text-amber-700 italic">
        Levels derived from technical indicators only — not investment advice. Verify before trading.
      </p>
    </div>
  );
}
