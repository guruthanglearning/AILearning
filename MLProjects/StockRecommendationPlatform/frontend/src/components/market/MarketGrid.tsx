"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getMarketQuotes } from "@/lib/api";
import type { MarketQuoteRow } from "@/types/api";

// ── Formatters ────────────────────────────────────────────────────────────────

function fmtPrice(v: number | null): string {
  if (v == null) return "--";
  return v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtChange(v: number | null): string {
  if (v == null) return "--";
  return (v >= 0 ? "+" : "") + v.toFixed(2);
}

function fmtCap(v: number | null): string {
  if (v == null) return "--";
  if (v >= 1e12) return `${(v / 1e12).toFixed(3)}T`;
  if (v >= 1e9)  return `${(v / 1e9).toFixed(3)}B`;
  if (v >= 1e6)  return `${(v / 1e6).toFixed(0)}M`;
  return v.toFixed(0);
}

function fmtShares(v: number | null): string {
  if (v == null) return "--";
  if (v >= 1e9) return `${(v / 1e9).toFixed(3)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(3)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return v.toFixed(0);
}

// ── Color helpers ─────────────────────────────────────────────────────────────

function chgColor(v: number | null): string {
  if (v == null) return "text-gray-400";
  return v > 0 ? "text-green-400" : v < 0 ? "text-red-400" : "text-gray-400";
}

// ── Default symbol list (matching screenshot) ─────────────────────────────────

const DEFAULT_SYMBOLS = [
  "NVDA", "MSFT", "AAPL", "GOOG", "AMZN", "META", "AVGO", "TSM", "TSLA", "BRK-B",
  "ORCL", "LLY", "V", "SPY", "NFLX", "PLTR", "COST", "ASML", "AMD", "NVO",
  "CRM", "MU", "NOW", "BLK", "ARM", "ADBE", "PANW", "VUG", "GLD", "CRWV",
  "DXCM", "JBL", "QS", "TQQQ", "^VIX", "^TYX", "^TNX", "^SPX", "^IXIC", "^DJI",
];

const STORAGE_KEY    = "market_grid_symbols_v2";
const INTERVAL_KEY   = "market_grid_interval";

// ── Row component ─────────────────────────────────────────────────────────────

const TH = "px-3 py-2 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider whitespace-nowrap select-none";
const TD = "px-3 py-2 text-xs whitespace-nowrap";

function Row({ row, onAnalyze }: { row: MarketQuoteRow; onAnalyze: (s: string) => void }) {
  return (
    <tr className="border-b border-gray-800/70 hover:bg-gray-800/30 transition-colors">
      {/* Symbol */}
      <td className={`${TD} font-bold sticky left-0 bg-gray-950 z-10`}>
        <button
          type="button"
          onClick={() => onAnalyze(row.symbol)}
          className="text-indigo-400 hover:text-indigo-200 transition-colors"
          title="Run analysis"
        >
          {row.symbol}
        </button>
      </td>
      {/* Pre-Mkt Price */}
      <td className={`${TD} font-mono text-gray-300`}>{fmtPrice(row.pre_mkt_price)}</td>
      {/* Pre-Mkt Change */}
      <td className={`${TD} font-mono font-semibold ${chgColor(row.pre_mkt_change)}`}>
        {fmtChange(row.pre_mkt_change)}
      </td>
      {/* Last Price */}
      <td className={`${TD} font-mono font-semibold text-white`}>{fmtPrice(row.last_price)}</td>
      {/* Change */}
      <td className={`${TD} font-mono font-semibold ${chgColor(row.change)}`}>
        {fmtChange(row.change)}
      </td>
      {/* Post-Mkt Price */}
      <td className={`${TD} font-mono text-gray-300`}>{fmtPrice(row.post_mkt_price)}</td>
      {/* Post-Mkt Change */}
      <td className={`${TD} font-mono ${chgColor(row.post_mkt_change)}`}>
        {fmtChange(row.post_mkt_change)}
      </td>
      {/* Earnings Date */}
      <td className={`${TD} text-gray-400`}>{row.earnings_date ?? "--"}</td>
      {/* Market Cap */}
      <td className={`${TD} text-gray-300`}>{fmtCap(row.market_cap)}</td>
      {/* Div Payment Date */}
      <td className={`${TD} text-gray-400`}>{row.div_payment_date ?? "--"}</td>
      {/* Exchange */}
      <td className={`${TD} text-gray-500`}>{row.exchange ?? "--"}</td>
      {/* 52-Wk High */}
      <td className={`${TD} font-mono text-gray-300`}>{fmtPrice(row.week_52_high)}</td>
      {/* 52-Wk Low */}
      <td className={`${TD} font-mono text-gray-300`}>{fmtPrice(row.week_52_low)}</td>
      {/* Shares Out */}
      <td className={`${TD} text-gray-300`}>{fmtShares(row.shares_outstanding)}</td>
    </tr>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

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

  const [rows, setRows]               = useState<MarketQuoteRow[]>([]);
  const [loading, setLoading]         = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError]             = useState<string | null>(null);
  const [countdown, setCountdown]     = useState(0);
  const [addInput, setAddInput]       = useState("");
  const [intervalInput, setIntervalInput] = useState(String(intervalSec));

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cdRef    = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { localStorage.setItem(STORAGE_KEY, JSON.stringify(symbols)); }, [symbols]);
  useEffect(() => { localStorage.setItem(INTERVAL_KEY, String(intervalSec)); }, [intervalSec]);

  const fetchQuotes = useCallback(async () => {
    if (!symbols.length) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getMarketQuotes(symbols);
      const bySymbol = new Map(data.map((r) => [r.symbol, r]));
      setRows(symbols.map((s) => bySymbol.get(s) ?? ({ symbol: s, fetched_at_utc: new Date().toISOString() } as MarketQuoteRow)));
      setLastUpdated(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fetch failed");
    } finally {
      setLoading(false);
    }
  }, [symbols]);

  // Auto-refresh
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (cdRef.current)    clearInterval(cdRef.current);

    fetchQuotes();
    setCountdown(intervalSec);

    timerRef.current = setInterval(() => { fetchQuotes(); setCountdown(intervalSec); }, intervalSec * 1000);
    cdRef.current    = setInterval(() => setCountdown((c) => Math.max(0, c - 1)), 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (cdRef.current)    clearInterval(cdRef.current);
    };
  }, [symbols, intervalSec, fetchQuotes]);

  function addSymbol() {
    const sym = addInput.trim().toUpperCase();
    if (!sym || symbols.includes(sym)) { setAddInput(""); return; }
    setSymbols((prev) => [...prev, sym]);
    setAddInput("");
  }

  function removeSymbol(sym: string) {
    setSymbols((prev) => prev.filter((s) => s !== sym));
    setRows((prev) => prev.filter((r) => r.symbol !== sym));
  }

  function applyInterval() {
    const v = parseInt(intervalInput, 10);
    if (!isNaN(v) && v >= 5 && v <= 300) setIntervalSec(v);
  }

  return (
    <div className="space-y-3">
      {/* ── Controls ── */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex gap-2 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Add Symbol</label>
            <input
              type="text"
              value={addInput}
              onChange={(e) => setAddInput(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && addSymbol()}
              placeholder="e.g. GOOG"
              maxLength={12}
              className="w-28 bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button type="button" onClick={addSymbol}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded transition-colors">
            Add
          </button>
        </div>

        <div className="flex gap-2 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Refresh (sec)</label>
            <input
              type="number" min={5} max={300}
              value={intervalInput}
              onChange={(e) => setIntervalInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && applyInterval()}
              className="w-20 bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button type="button" onClick={applyInterval}
            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors">
            Set
          </button>
        </div>

        <button type="button" onClick={() => { fetchQuotes(); setCountdown(intervalSec); }}
          disabled={loading}
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded border border-gray-700 transition-colors disabled:opacity-50">
          {loading ? "Refreshing…" : "↻ Refresh now"}
        </button>

        <div className="ml-auto text-right">
          {lastUpdated && (
            <p className="text-xs text-gray-500">Updated {lastUpdated.toLocaleTimeString()}</p>
          )}
          <p className={`text-xs font-mono ${countdown <= 3 ? "text-amber-500" : "text-gray-600"}`}>
            Next in {countdown}s
          </p>
        </div>
      </div>

      {/* ── Symbol chips ── */}
      {symbols.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {symbols.map((sym) => (
            <span key={sym}
              className="inline-flex items-center gap-1 bg-gray-800 border border-gray-700 text-xs text-gray-300 px-2 py-0.5 rounded">
              {sym}
              <button type="button" onClick={() => removeSymbol(sym)}
                className="text-gray-500 hover:text-red-400 transition-colors leading-none" title="Remove">
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">{error}</p>
      )}

      {/* ── Table ── */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-900 border-b border-gray-700">
              <tr>
                <th className={`${TH} sticky left-0 bg-gray-900 z-10`}>Symbol</th>
                <th className={TH}>Pre-Mkt<br/>Price</th>
                <th className={TH}>Pre-Mkt<br/>Change</th>
                <th className={TH}>Last Price</th>
                <th className={TH}>Change</th>
                <th className={TH}>Post-Mkt<br/>Price</th>
                <th className={TH}>Post-Mkt<br/>Change</th>
                <th className={TH}>Earnings Date</th>
                <th className={TH}>Market Cap</th>
                <th className={TH}>Div Payment<br/>Date</th>
                <th className={TH}>Exchange</th>
                <th className={TH}>52-Wk High</th>
                <th className={TH}>52-Wk Low</th>
                <th className={TH}>Shares Out</th>
              </tr>
            </thead>
            <tbody className="bg-gray-950 divide-y divide-gray-800/50">
              {rows.length === 0 && !loading && (
                <tr>
                  <td colSpan={14} className="px-3 py-10 text-center text-xs text-gray-600">
                    {symbols.length === 0 ? "Add symbols above to populate the grid." : "Loading…"}
                  </td>
                </tr>
              )}
              {rows.map((row) => (
                <Row key={row.symbol} row={row} onAnalyze={onAnalyze ?? (() => {})} />
              ))}
            </tbody>
          </table>
        </div>
        {loading && <div className="h-0.5 bg-indigo-600/70 animate-pulse" />}
      </div>

      <p className="text-xs text-gray-700 italic">
        Data via yfinance. Pre/post-market fields only available during those sessions. Not investment advice.
      </p>
    </div>
  );
}
