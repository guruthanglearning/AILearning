"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { ScoreMeter } from "@/components/ui/ScoreMeter";
import { useAnalysisHistory } from "@/hooks/useAnalysis";
import type { AnalysisHistoryItem } from "@/types/api";

type BadgeVariant = "success" | "info" | "warning" | "neutral";

const REC_BADGE: Record<string, { label: string; variant: BadgeVariant }> = {
  stock: { label: "Stock", variant: "success" },
  options: { label: "Options", variant: "info" },
  no_trade: { label: "No Trade", variant: "warning" },
  insufficient_data: { label: "Insuff. Data", variant: "neutral" },
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function VerdictBadge({ rec }: { rec: string | null }) {
  if (!rec) return <span className="text-gray-500 text-xs">—</span>;
  const cfg = REC_BADGE[rec] ?? { label: rec, variant: "neutral" as BadgeVariant };
  return <Badge variant={cfg.variant} size="sm">{cfg.label}</Badge>;
}

function ScoreCell({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-500 text-xs">—</span>;
  return <ScoreMeter score={score} />;
}

function HistoryRow({ item }: { item: AnalysisHistoryItem }) {
  return (
    <tr className="border-t border-gray-800 hover:bg-gray-800/40 transition-colors">
      <td className="py-2 px-3 text-xs text-gray-400 whitespace-nowrap">
        {formatDate(item.started_at)}
      </td>
      <td className="py-2 px-3">
        <VerdictBadge rec={item.instrument_recommendation} />
      </td>
      <td className="py-2 px-3 text-xs text-gray-300 tabular-nums">
        {item.last_price != null ? `$${item.last_price.toFixed(2)}` : "—"}
      </td>
      <td className="py-2 px-3">
        <ScoreCell score={item.stock_vs_options_score} />
      </td>
      <td className="py-2 px-3">
        <span
          className={`text-xs font-medium ${
            item.status === "complete" ? "text-green-400" : "text-gray-400"
          }`}
        >
          {item.status}
        </span>
      </td>
    </tr>
  );
}

interface AnalysisHistoryProps {
  symbol: string;
}

export function AnalysisHistory({ symbol }: AnalysisHistoryProps) {
  const [open, setOpen] = useState(true);
  const { data: items, isLoading, error } = useAnalysisHistory(symbol);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-800/50 transition-colors"
      >
        <span className="text-sm font-medium text-gray-200">
          Analysis History
          <span className="ml-2 text-gray-500 font-mono text-xs">{symbol}</span>
        </span>
        <span className="text-gray-500 text-xs">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div>
          {isLoading && (
            <p className="px-4 py-4 text-xs text-gray-500">Loading history…</p>
          )}
          {error && (
            <p className="px-4 py-4 text-xs text-red-400">Failed to load history.</p>
          )}
          {!isLoading && !error && (!items || items.length === 0) && (
            <p className="px-4 py-4 text-xs text-gray-500">No history yet for {symbol}.</p>
          )}
          {!isLoading && !error && items && items.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[500px] text-sm">
                <thead>
                  <tr className="border-t border-gray-800">
                    <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Date</th>
                    <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Verdict</th>
                    <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Spot</th>
                    <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Score</th>
                    <th className="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <HistoryRow key={item.run_id} item={item} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
