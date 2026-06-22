"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getAllAnalysisHistory } from "@/lib/api";
import type { AnalysisHistoryItem } from "@/types/api";

const VERDICT_COLORS: Record<string, string> = {
  stock: "bg-emerald-900/60 text-emerald-400 border-emerald-800",
  options: "bg-indigo-900/60 text-indigo-400 border-indigo-800",
  no_trade: "bg-gray-800 text-gray-400 border-gray-700",
  insufficient_data: "bg-yellow-900/40 text-yellow-500 border-yellow-900",
};

function VerdictBadge({ verdict }: { verdict: string | null }) {
  if (!verdict) return <span className="text-gray-600">—</span>;
  const cls = VERDICT_COLORS[verdict] ?? "bg-gray-800 text-gray-400 border-gray-700";
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border ${cls}`}>
      {verdict.replace("_", " ")}
    </span>
  );
}

function fmtTime(s: string): string {
  const d = new Date(s);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
    " " +
    d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export default function HistoryPage() {
  const router = useRouter();
  const [items, setItems] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    getAllAnalysisHistory(100)
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load history"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter.trim()
    ? items.filter((i) => i.symbol.includes(filter.toUpperCase().trim()))
    : items;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-white">Analysis History</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Recent analysis runs across all symbols — most recent first.
        </p>
      </div>

      {/* filter */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value.toUpperCase())}
          placeholder="Filter by symbol…"
          className="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 w-48"
        />
        {filter && (
          <button
            onClick={() => setFilter("")}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Clear
          </button>
        )}
        <span className="text-xs text-gray-600 ml-auto">{filtered.length} run{filtered.length !== 1 ? "s" : ""}</span>
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 border border-red-900/50 rounded-md px-3 py-2">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-xs text-gray-600 py-8 text-center">Loading…</p>
      ) : filtered.length === 0 ? (
        <p className="text-xs text-gray-600 py-8 text-center">
          {filter ? `No runs found for "${filter}"` : "No analysis runs yet."}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-500 uppercase tracking-wider border-b border-gray-800">
                {["Symbol", "Time", "Verdict", "Score", "Confidence", "Price"].map((h) => (
                  <th key={h} className="text-left py-2 px-2 font-medium first:pl-0">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.run_id} className="border-b border-gray-800/60 hover:bg-gray-800/30">
                  <td className="py-2.5 px-2 pl-0 font-mono font-bold">
                    <button
                      onClick={() => router.push(`/?symbol=${item.symbol}`)}
                      className="text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      {item.symbol}
                    </button>
                  </td>
                  <td className="py-2.5 px-2 text-gray-400 whitespace-nowrap">{fmtTime(item.started_at)}</td>
                  <td className="py-2.5 px-2">
                    <VerdictBadge verdict={item.instrument_recommendation} />
                  </td>
                  <td className="py-2.5 px-2 font-mono text-gray-300">
                    {item.stock_vs_options_score != null
                      ? item.stock_vs_options_score.toFixed(2)
                      : "—"}
                  </td>
                  <td className="py-2.5 px-2 text-gray-400 max-w-xs truncate" title={item.confidence_note ?? ""}>
                    {item.confidence_note ?? "—"}
                  </td>
                  <td className="py-2.5 px-2 font-mono text-gray-300">
                    {item.last_price != null ? `$${item.last_price.toFixed(2)}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
