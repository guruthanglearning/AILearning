"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { ScoreMeter } from "@/components/ui/ScoreMeter";
import { useAnalysisHistory } from "@/hooks/useAnalysis";
import type { AnalysisHistoryItem } from "@/types/api";

type BadgeVariant = "success" | "info" | "warning" | "neutral";

const REC_BADGE: Record<string, { label: string; variant: BadgeVariant }> = {
  stock:             { label: "Stock",         variant: "success" },
  options:           { label: "Options",        variant: "info"    },
  no_trade:          { label: "No Trade",       variant: "warning" },
  insufficient_data: { label: "Insuff. Data",   variant: "neutral" },
};

function formatDateTime(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    time: d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" }),
  };
}

function VerdictBadge({ rec }: { rec: string | null }) {
  if (!rec) return <span className="text-gray-500 text-xs">—</span>;
  const cfg = REC_BADGE[rec] ?? { label: rec, variant: "neutral" as BadgeVariant };
  return <Badge variant={cfg.variant} size="sm">{cfg.label}</Badge>;
}

// ── Consistency summary ───────────────────────────────────────────────────────

interface ConsistencyInfo {
  label: string;
  sublabel: string;
  color: string;
  bg: string;
  border: string;
}

function consistencyInfo(items: AnalysisHistoryItem[]): ConsistencyInfo | null {
  const completed = items.filter(i => i.status === "complete" && i.instrument_recommendation);
  if (completed.length < 2) return null;

  const counts: Record<string, number> = {};
  for (const it of completed) {
    const r = it.instrument_recommendation!;
    counts[r] = (counts[r] ?? 0) + 1;
  }

  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  const topRec   = top[0];
  const topCount = top[1];
  const total    = completed.length;
  const pct      = Math.round((topCount / total) * 100);

  // Last 3 runs all the same?
  const last3 = completed.slice(0, 3);
  const last3Same = last3.length >= 2 && last3.every(i => i.instrument_recommendation === last3[0].instrument_recommendation);

  const label = REC_BADGE[topRec]?.label ?? topRec;

  if (pct === 100) {
    return {
      label: `Consistent — ${label} across all ${total} runs`,
      sublabel: "Recommendation has not changed. Strong signal.",
      color: "text-green-300", bg: "bg-green-900/20", border: "border-green-800/40",
    };
  }
  if (pct >= 70 && last3Same) {
    return {
      label: `Leaning ${label} (${topCount}/${total} runs)`,
      sublabel: "Recent runs agree. Weaker runs may reflect intraday vol — check dates.",
      color: "text-amber-300", bg: "bg-amber-900/20", border: "border-amber-800/40",
    };
  }
  return {
    label: `Mixed signals (${topCount}/${total} runs favour ${label})`,
    sublabel: "Recommendation has been inconsistent. Wait for clarity before sizing up.",
    color: "text-red-300", bg: "bg-red-900/20", border: "border-red-800/40",
  };
}

// ── Table row ─────────────────────────────────────────────────────────────────

function PriceDelta({ current, previous }: { current: number | null; previous: number | null }) {
  if (current == null || previous == null) return <span className="text-gray-600">—</span>;
  const delta = current - previous;
  const pct   = (delta / previous) * 100;
  const sign  = delta >= 0 ? "+" : "";
  const color = delta > 0 ? "text-green-400" : delta < 0 ? "text-red-400" : "text-gray-400";
  return (
    <span className={`text-xs font-mono ${color}`}>
      {sign}{pct.toFixed(1)}%
    </span>
  );
}

function HistoryRow({ item, prevItem }: { item: AnalysisHistoryItem; prevItem: AnalysisHistoryItem | null }) {
  const { date, time } = formatDateTime(item.started_at);
  return (
    <tr className="border-t border-gray-800 hover:bg-gray-800/30 transition-colors">
      <td className="py-2 px-3 whitespace-nowrap">
        <p className="text-xs text-gray-300">{date}</p>
        <p className="text-xs text-gray-600">{time}</p>
      </td>
      <td className="py-2 px-3">
        <VerdictBadge rec={item.instrument_recommendation} />
      </td>
      <td className="py-2 px-3 text-xs font-mono text-gray-300 whitespace-nowrap">
        {item.last_price != null ? `$${item.last_price.toFixed(2)}` : "—"}
      </td>
      <td className="py-2 px-3">
        <PriceDelta current={item.last_price} previous={prevItem?.last_price ?? null} />
      </td>
      <td className="py-2 px-3 min-w-[100px]">
        {item.stock_vs_options_score != null
          ? <ScoreMeter score={item.stock_vs_options_score} />
          : <span className="text-gray-600 text-xs">—</span>}
      </td>
      <td className="py-2 px-3 max-w-[220px]">
        <p className="text-xs text-gray-500 truncate" title={item.confidence_note ?? ""}>
          {item.confidence_note ?? "—"}
        </p>
      </td>
    </tr>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function AnalysisHistory({ symbol }: { symbol: string }) {
  const [open, setOpen] = useState(true);
  const { data: items, isLoading, error } = useAnalysisHistory(symbol);

  const consistency = items && items.length >= 2 ? consistencyInfo(items) : null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-200">Analysis History</span>
          <span className="text-gray-500 font-mono text-xs">{symbol}</span>
          {items && items.length > 0 && (
            <span className="text-xs text-gray-600">{items.length} run{items.length !== 1 ? "s" : ""}</span>
          )}
        </div>
        <span className="text-gray-500 text-xs">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div>
          {isLoading && <p className="px-4 py-4 text-xs text-gray-500">Loading history…</p>}
          {error    && <p className="px-4 py-4 text-xs text-red-400">Failed to load history.</p>}

          {!isLoading && !error && (!items || items.length === 0) && (
            <p className="px-4 py-4 text-xs text-gray-500">No history yet for {symbol}. Run an analysis to start tracking.</p>
          )}

          {!isLoading && !error && items && items.length > 0 && (
            <>
              {/* Consistency banner */}
              {consistency && (
                <div className={`mx-4 mb-3 mt-1 rounded-lg border px-4 py-2.5 ${consistency.bg} ${consistency.border}`}>
                  <p className={`text-xs font-semibold ${consistency.color}`}>{consistency.label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{consistency.sublabel}</p>
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full min-w-[620px] text-sm">
                  <thead>
                    <tr className="border-t border-gray-800">
                      <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Date / Time</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Verdict</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Spot</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Δ vs Prev</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Score</th>
                      <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item, idx) => (
                      <HistoryRow
                        key={item.run_id}
                        item={item}
                        prevItem={items[idx + 1] ?? null}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
