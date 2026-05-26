"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { clearErrorLogs, getErrorLogs } from "@/lib/api";
import type { ErrorLogEntry } from "@/types/api";

const STATUS_COLOR: Record<string, string> = {
  degraded: "text-amber-400 bg-amber-900/30 border-amber-700/40",
  failed:   "text-red-400 bg-red-900/30 border-red-700/40",
  complete: "text-green-400 bg-green-900/30 border-green-700/40",
};

function statusBadge(s: string) {
  const cls = STATUS_COLOR[s] ?? "text-gray-400 bg-gray-800 border-gray-700";
  return (
    <span className={`inline-block px-1.5 py-0.5 text-xs rounded border ${cls}`}>
      {s}
    </span>
  );
}

function fmt(ts: string) {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

export default function LogsPage() {
  const [entries, setEntries]   = useState<ErrorLogEntry[]>([]);
  const [loading, setLoading]   = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [filterAgent, setFilterAgent] = useState("");
  const [filterSymbol, setFilterSymbol] = useState("");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getErrorLogs(200);
      setEntries(data);
      setLastRefresh(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load logs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (autoRefresh) {
      timerRef.current = setInterval(load, 10_000);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [autoRefresh, load]);

  async function handleClear() {
    setClearing(true);
    try {
      await clearErrorLogs();
      setEntries([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clear failed");
    } finally {
      setClearing(false);
    }
  }

  const filtered = entries.filter((e) => {
    if (filterAgent  && !e.agent.toLowerCase().includes(filterAgent.toLowerCase()))  return false;
    if (filterSymbol && !e.symbol.toLowerCase().includes(filterSymbol.toLowerCase())) return false;
    return true;
  });

  const agents  = Array.from(new Set(entries.map((e) => e.agent))).sort();
  const symbols = Array.from(new Set(entries.map((e) => e.symbol))).sort();

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="text-xl font-semibold text-white">Agent Error Logs</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            In-memory ring buffer — last 500 agent errors across all analysis runs (cleared on server restart)
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {lastRefresh && (
            <span className="text-xs text-gray-600">Updated {lastRefresh.toLocaleTimeString()}</span>
          )}
          <label className="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="accent-indigo-500"
            />
            Auto-refresh (10s)
          </label>
          <button
            onClick={load}
            disabled={loading}
            className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 rounded transition-colors disabled:opacity-50"
          >
            {loading ? "Loading…" : "↻ Refresh"}
          </button>
          <button
            onClick={handleClear}
            disabled={clearing || entries.length === 0}
            className="px-3 py-1.5 text-xs bg-red-900/40 hover:bg-red-800/50 text-red-400 border border-red-800/50 rounded transition-colors disabled:opacity-40"
          >
            {clearing ? "Clearing…" : "Clear all"}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="flex flex-wrap gap-3">
        {[
          { label: "Total errors", value: entries.length },
          { label: "Degraded", value: entries.filter((e) => e.status === "degraded").length, color: "text-amber-400" },
          { label: "Failed",   value: entries.filter((e) => e.status === "failed").length,   color: "text-red-400"   },
          { label: "Agents affected", value: Array.from(new Set(entries.map((e) => e.agent))).length },
          { label: "Symbols",  value: Array.from(new Set(entries.map((e) => e.symbol))).length },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-2 min-w-[110px]">
            <p className={`text-lg font-semibold ${color ?? "text-white"}`}>{value}</p>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Filter by agent</label>
          <select
            value={filterAgent}
            onChange={(e) => setFilterAgent(e.target.value)}
            className="bg-gray-900 border border-gray-700 text-sm text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All agents</option>
            {agents.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Filter by symbol</label>
          <select
            value={filterSymbol}
            onChange={(e) => setFilterSymbol(e.target.value)}
            className="bg-gray-900 border border-gray-700 text-sm text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All symbols</option>
            {symbols.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        {(filterAgent || filterSymbol) && (
          <button
            onClick={() => { setFilterAgent(""); setFilterSymbol(""); }}
            className="text-xs text-gray-500 hover:text-gray-300 mt-5"
          >
            ✕ Clear filters
          </button>
        )}
        <span className="text-xs text-gray-600 mt-5 ml-auto">
          Showing {filtered.length} of {entries.length}
        </span>
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">{error}</p>
      )}

      {/* Table */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-900 border-b border-gray-700">
              <tr>
                {["Timestamp", "Symbol", "Agent", "Status", "Error Message"].map((h) => (
                  <th key={h} className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-gray-950 divide-y divide-gray-800/50">
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-12 text-center text-xs text-gray-600">
                    {entries.length === 0
                      ? "No errors recorded yet. Run an analysis to populate this log."
                      : "No entries match the current filters."}
                  </td>
                </tr>
              )}
              {filtered.map((e, i) => (
                <tr key={i} className="hover:bg-gray-800/30 transition-colors">
                  <td className="px-3 py-2 text-xs text-gray-500 whitespace-nowrap font-mono">{fmt(e.ts)}</td>
                  <td className="px-3 py-2 text-xs font-bold text-indigo-400 whitespace-nowrap">{e.symbol}</td>
                  <td className="px-3 py-2 text-xs text-gray-300 whitespace-nowrap">{e.agent}</td>
                  <td className="px-3 py-2 text-xs whitespace-nowrap">{statusBadge(e.status)}</td>
                  <td className="px-3 py-2 text-xs text-gray-400 max-w-xl break-words">{e.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {loading && <div className="h-0.5 bg-indigo-600/70 animate-pulse" />}
      </div>

      <p className="text-xs text-gray-700 italic">
        Errors are held in the server&apos;s in-memory buffer and are lost on restart. The buffer holds the most recent 500 entries.
      </p>
    </div>
  );
}
