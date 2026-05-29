"use client";

import { useEffect, useState } from "react";

import { getPeers } from "@/lib/api";
import type { PeerRow } from "@/types/api";

function fmtCap(v: number | null): string {
  if (v == null) return "—";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9)  return `$${(v / 1e9).toFixed(1)}B`;
  return `$${(v / 1e6).toFixed(0)}M`;
}

function fmtRatio(v: number | null): string {
  return v != null ? `${v.toFixed(1)}×` : "—";
}

function fmtPct(v: number | null): string {
  if (v == null) return "—";
  const sign = v >= 0 ? "+" : "";
  return `${sign}${(v * 100).toFixed(1)}%`;
}

function pctColor(v: number | null): string {
  if (v == null) return "text-gray-400";
  return v >= 0 ? "text-green-400" : "text-red-400";
}

function PeerTableRow({ row, isTarget }: { row: PeerRow; isTarget: boolean }) {
  return (
    <tr className={`border-t border-gray-800 ${isTarget ? "bg-indigo-900/20" : "hover:bg-gray-800/30"} transition-colors`}>
      <td className="px-3 py-2 text-xs font-mono font-semibold text-white whitespace-nowrap">
        {row.symbol}
        {isTarget && <span className="ml-1 text-indigo-400 text-[10px]">★</span>}
      </td>
      <td className="px-3 py-2 text-xs text-gray-400 max-w-[140px] truncate" title={row.name ?? ""}>
        {row.name ?? "—"}
      </td>
      <td className="px-3 py-2 text-xs font-mono text-gray-200 text-right tabular-nums">
        {row.price != null ? `$${row.price.toFixed(2)}` : "—"}
      </td>
      <td className="px-3 py-2 text-xs font-mono text-right tabular-nums">
        <span className={pctColor(row.ytd_return)}>{fmtPct(row.ytd_return)}</span>
      </td>
      <td className="px-3 py-2 text-xs font-mono text-gray-300 text-right tabular-nums">
        {fmtCap(row.market_cap)}
      </td>
      <td className="px-3 py-2 text-xs font-mono text-gray-300 text-right tabular-nums">
        {fmtRatio(row.pe_ratio)}
      </td>
      <td className="px-3 py-2 text-xs font-mono text-gray-300 text-right tabular-nums">
        {fmtRatio(row.forward_pe)}
      </td>
    </tr>
  );
}

export function PeerComparisonTable({ symbol }: { symbol: string }) {
  const [sector, setSector] = useState<string | null>(null);
  const [peers, setPeers] = useState<PeerRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    getPeers(symbol)
      .then(r => { setSector(r.sector); setPeers(r.peers); })
      .catch(e => setError(e instanceof Error ? e.message : "Failed to load peers"))
      .finally(() => setLoading(false));
  }, [symbol]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <h2 className="text-sm font-medium text-gray-400">Sector Peer Comparison</h2>
        {sector && (
          <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{sector}</span>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
        {loading && (
          <p className="px-4 py-6 text-xs text-gray-500">Loading peer data…</p>
        )}
        {error && (
          <p className="px-4 py-6 text-xs text-red-400">{error}</p>
        )}
        {!loading && !error && peers.length === 0 && (
          <p className="px-4 py-6 text-xs text-gray-500">No peer data available for {symbol}.</p>
        )}
        {!loading && !error && peers.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-left">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-800/40">
                  <th className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">Symbol</th>
                  <th className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">Name</th>
                  <th className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide text-right">Price</th>
                  <th className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide text-right">YTD</th>
                  <th className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide text-right">Mkt Cap</th>
                  <th className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide text-right">P/E</th>
                  <th className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide text-right">Fwd P/E</th>
                </tr>
              </thead>
              <tbody>
                {peers.map(row => (
                  <PeerTableRow
                    key={row.symbol}
                    row={row}
                    isTarget={row.symbol.toUpperCase() === symbol.toUpperCase()}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
