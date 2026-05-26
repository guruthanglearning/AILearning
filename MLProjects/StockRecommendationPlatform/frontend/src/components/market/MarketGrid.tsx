"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getMarketQuotes } from "@/lib/api";
import type { MarketQuoteRow } from "@/types/api";

// ── Formatters ────────────────────────────────────────────────────────────────

function fmtPrice(v: number | null): string {
  if (v == null) return "—";
  return `$${v.toFixed(2)}`;
}

function fmtChange(v: number | null): string {
  if (v == null) return "—";
  return (v >= 0 ? "+" : "") + v.toFixed(2);
}

function fmtPct(v: number | null): string {
  if (v == null) return "—";
  // yfinance returns decimal (0.012) or already percent (1.2) depending on field
  const pct = Math.abs(v) < 1 ? v * 100 : v;
  return (pct >= 0 ? "+" : "") + pct.toFixed(2) + "%";
}

function fmtLargePct(v: number | null): string {
  if (v == null) return "—";
  return (v >= 0 ? "+" : "") + v.toFixed(2) + "%";
}

function fmtCap(v: number | null): string {
  if (v == null) return "—";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${v.toFixed(0)}`;
}

function fmtShares(v: number | null): string {
  if (v == null) return "—";
  if (v >= 1e9) return `${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return v.toFixed(0);
}

function fmtVol(v: number | null): string {
  if (v == null) return "—";
  if (v >= 1e9) return `${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return v.toFixed(0);
}

// ── Color helpers ─────────────────────────────────────────────────────────────

function chgColor(v: number | null): string {
  if (v == null) return "text-gray-400";
  const n = Math.abs(v) < 1 ? v * 100 : v;
  return n > 0 ? "text-green-400" : n < 0 ? "text-red-400" : "text-gray-400";
}

function rawChgColor(v: number | null): string {
  if (v == null) return "text-gray-400";
  return v > 0 ? "text-green-400" : v < 0 ? "text-red-400" : "text-gray-400";
}

// ── Column definitions ────────────────────────────────────────────────────────

const TH = "px-3 py-2 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider whitespace-nowrap";
const TD = "px-3 py-2 text-xs whitespace-nowrap";

// ── Sub-components ────────────────────────────────────────────────────────────

function Row({ row, onAnalyze }: { row: MarketQuoteRow; onAnalyze: (sym: string) => void }) {
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
      {/* Symbol */}
      <td className={`${TD} font-semibold text-white sticky left-0 bg-gray-950 z-10`}>
        <button
          type="button"
          onClick={() => onAnalyze(row.symbol)}
          className="text-indigo-400 hover:text-indigo-200 font-bold transition-colors"
          title="Run analysis"
        >
          {row.symbol}
        </button>
      </td>
      {/* Pre Mkt % */}
      <td className={`${TD} ${chgColor(row.pre_mkt_change_pct)}`}>
        {fmtPct(row.pre_mkt_change_pct)}
      </td>
      {/* Pre Mkt Last Price */}
      <td className={`${TD} font-mono text-gray-300`}>
        {fmtPrice(row.pre_mkt_price)}
      </td>
      {/* Last Price */}
      <td className={`${TD} font-mono font-semibold text-white`}>
        {fmtPrice(row.last_price)}
      </td>
      {/* Change $ */}
      <td className={`${TD} font-mono ${rawChgColor(row.change)}`}>
        {fmtChange(row.change)}
      </td>
      {/* Post Mkt % */}
      <td className={`${TD} ${chgColor(row.post_mkt_change_pct)}`}>
        {fmtPct(row.post_mkt_change_pct)}
      </td>
      {/* Post Mkt Last Price */}
      <td className={`${TD} font-mono text-gray-300`}>
        {fmtPrice(row.post_mkt_price)}
      </td>
      {/* Avg Market Cap */}
      <td className={`${TD} text-gray-300`}>{fmtCap(row.market_cap)}</td>
      {/* Exchange */}
      <td className={`${TD} text-gray-500`}>{row.exchange ?? "—"}</td>
      {/* 52-Wk Hi */}
      <td className={`${TD} font-mono text-gray-300`}>{fmtPrice(row.week_52_high)}</td>
      {/* 52-Wk Lo */}
      <td className={`${TD} font-mono text-gray-300`}>{fmtPrice(row.week_52_low)}</td>
      {/* Shares Out */}
      <td className={`${TD} text-gray-300`}>{fmtShares(row.shares_outstanding)}</td>
      {/* Volume */}
      <td className={`${TD} text-gray-300`}>{fmtVol(row.volume)}</td>
      {/* % Chg */}
      <td className={`${TD} font-mono ${rawChgColor(row.change_pct)}`}>
        {fmtLargePct(row.change_pct)}
      </td>
    </tr>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

const DEFAULT_SYMBOLS = ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "JPM", "V", "MA"];
const STORAGE_KEY = "market_grid_symbols";
const INTERVAL_KEY = "market_grid_interval";

interface MarketGridProps {
  onAnalyze?: (symbol: string) => void;
}

export function MarketGrid({ onAnalyze }: MarketGridProps) {
  const [symbols, setSymbols] = useState<string[]>(() => {
    if (typeof window === "undefined") return DEFAULT_SYMBOLS;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : DEFAULT_SYMBOLS;
    } catch {
      return DEFAULT_SYMBOLS;
    }
  });

  const [intervalSec, setIntervalSec] = useState<number>(() => {
    if (typeof window === "undefined") return 10;
    return Number(localStorage.getItem(INTERVAL_KEY) ?? "10");
  });

  const [rows, setRows] = useState<MarketQuoteRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);

  const [addInput, setAddInput] = useState("");
  const [intervalInput, setIntervalInput] = useState(String(intervalSec));

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cdRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Persist symbols
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(symbols));
  }, [symbols]);

  // Persist interval
  useEffect(() => {
    localStorage.setItem(INTERVAL_KEY, String(intervalSec));
  }, [intervalSec]);

  const fetchQuotes = useCallback(async () => {
    if (!symbols.length) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getMarketQuotes(symbols);
      // Preserve symbol order
      const bySymbol = new Map(data.map((r) => [r.symbol, r]));
      setRows(symbols.map((s) => bySymbol.get(s) ?? { symbol: s, fetched_at_utc: new Date().toISOString() } as MarketQuoteRow));
      setLastUpdated(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fetch failed");
    } finally {
      setLoading(false);
    }
  }, [symbols]);

  // Auto-refresh timer
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (cdRef.current) clearInterval(cdRef.current);

    fetchQuotes();
    setCountdown(intervalSec);

    timerRef.current = setInterval(() => {
      fetchQuotes();
      setCountdown(intervalSec);
    }, intervalSec * 1000);

    cdRef.current = setInterval(() => {
      setCountdown((c) => Math.max(0, c - 1));
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (cdRef.current) clearInterval(cdRef.current);
    };
  }, [symbols, intervalSec, fetchQuotes]);

  function addSymbol() {
    const sym = addInput.trim().toUpperCase();
    if (!sym) return;
    if (symbols.includes(sym)) {
      setAddInput("");
      return;
    }
    setSymbols((prev) => [...prev, sym]);
    setAddInput("");
  }

  function removeSymbol(sym: string) {
    setSymbols((prev) => prev.filter((s) => s !== sym));
    setRows((prev) => prev.filter((r) => r.symbol !== sym));
  }

  function applyInterval() {
    const v = parseInt(intervalInput, 10);
    if (isNaN(v) || v < 5 || v > 300) return;
    setIntervalSec(v);
  }

  return (
    <div className="space-y-4">
      {/* ── Controls bar ── */}
      <div className="flex flex-wrap gap-3 items-end">
        {/* Add symbol */}
        <div className="flex gap-2 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Add Symbol</label>
            <input
              type="text"
              value={addInput}
              onChange={(e) => setAddInput(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && addSymbol()}
              placeholder="e.g. GOOG"
              maxLength={10}
              className="w-28 bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            type="button"
            onClick={addSymbol}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded transition-colors"
          >
            Add
          </button>
        </div>

        {/* Refresh interval */}
        <div className="flex gap-2 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Refresh (sec)</label>
            <input
              type="number"
              min={5}
              max={300}
              value={intervalInput}
              onChange={(e) => setIntervalInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && applyInterval()}
              className="w-20 bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            type="button"
            onClick={applyInterval}
            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors"
          >
            Set
          </button>
        </div>

        {/* Manual refresh */}
        <button
          type="button"
          onClick={() => { fetchQuotes(); setCountdown(intervalSec); }}
          disabled={loading}
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded border border-gray-700 transition-colors disabled:opacity-50"
        >
          {loading ? "Refreshing…" : "↻ Refresh now"}
        </button>

        {/* Status */}
        <div className="ml-auto text-right">
          {lastUpdated && (
            <p className="text-xs text-gray-500">
              Updated {lastUpdated.toLocaleTimeString()}
            </p>
          )}
          <p className={`text-xs font-mono ${countdown <= 3 ? "text-amber-500" : "text-gray-600"}`}>
            Next in {countdown}s
          </p>
        </div>
      </div>

      {/* ── Active symbol chips ── */}
      {symbols.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {symbols.map((sym) => (
            <span
              key={sym}
              className="inline-flex items-center gap-1 bg-gray-800 border border-gray-700 text-xs text-gray-300 px-2 py-0.5 rounded"
            >
              {sym}
              <button
                type="button"
                onClick={() => removeSymbol(sym)}
                className="text-gray-500 hover:text-red-400 transition-colors leading-none"
                title="Remove"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
          {error}
        </p>
      )}

      {/* ── Grid ── */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-900 border-b border-gray-700">
              <tr>
                <th className={`${TH} sticky left-0 bg-gray-900 z-10`}>Symbol</th>
                <th className={TH}>Pre Mkt</th>
                <th className={TH}>Pre Mkt Last Price</th>
                <th className={TH}>Last Price</th>
                <th className={TH}>Change</th>
                <th className={TH}>Post Mkt</th>
                <th className={TH}>Post Mkt Last Price</th>
                <th className={TH}>Avg Market Cap</th>
                <th className={TH}>Exchange</th>
                <th className={TH}>52-Wk Hi</th>
                <th className={TH}>52-Wk Lo</th>
                <th className={TH}>Shares Out</th>
                <th className={TH}>Volume</th>
                <th className={TH}>% Chg</th>
              </tr>
            </thead>
            <tbody className="bg-gray-950 divide-y divide-gray-800/60">
              {rows.length === 0 && !loading && (
                <tr>
                  <td colSpan={14} className="px-3 py-8 text-center text-xs text-gray-600">
                    {symbols.length === 0
                      ? "Add symbols above to populate the grid."
                      : "Loading…"}
                  </td>
                </tr>
              )}
              {rows.map((row) => (
                <Row
                  key={row.symbol}
                  row={row}
                  onAnalyze={onAnalyze ?? (() => {})}
                />
              ))}
            </tbody>
          </table>
        </div>

        {/* Loading overlay bar */}
        {loading && (
          <div className="h-0.5 bg-indigo-600/60 animate-pulse" />
        )}
      </div>

      <p className="text-xs text-gray-700 italic">
        Data sourced from yfinance. Pre/post-market data only available during those sessions.
        Not investment advice.
      </p>
    </div>
  );
}
