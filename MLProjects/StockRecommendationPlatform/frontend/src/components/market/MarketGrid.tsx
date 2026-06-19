"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useMarketGridWs, type LivePriceUpdate } from "@/hooks/useMarketGridWs";
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

// ── Sort helpers ──────────────────────────────────────────────────────────────

type SortKey = keyof MarketQuoteRow;
type SortDir = "asc" | "desc";

function getValue(row: MarketQuoteRow, key: SortKey): string | number {
  const v = row[key];
  if (v == null) return key === "symbol" ? "" : -Infinity;
  return v as string | number;
}

function sortRows(rows: MarketQuoteRow[], key: SortKey, dir: SortDir): MarketQuoteRow[] {
  return [...rows].sort((a, b) => {
    const av = getValue(a, key);
    const bv = getValue(b, key);
    if (av === bv) return 0;
    const cmp = typeof av === "string" && typeof bv === "string"
      ? av.localeCompare(bv)
      : (av as number) < (bv as number) ? -1 : 1;
    return dir === "asc" ? cmp : -cmp;
  });
}

// ── Constants ─────────────────────────────────────────────────────────────────

const DEFAULT_SYMBOLS = [
  "NVDA", "MSFT", "AAPL", "GOOG", "AMZN", "META", "AVGO", "TSM", "TSLA", "BRK-B",
  "ORCL", "LLY", "V", "SPY", "NFLX", "PLTR", "COST", "ASML", "AMD", "NVO",
  "CRM", "MU", "NOW", "BLK", "ARM", "ADBE", "PANW", "VUG", "GLD", "CRWV",
  "DXCM", "JBL", "QS", "TQQQ", "^VIX", "^TYX", "^TNX", "^SPX", "^IXIC", "^DJI",
];

export const MARKET_GRID_SYMBOLS_KEY = "market_grid_symbols_v2";
const INTERVAL_KEY   = "market_grid_interval";
const HIDDEN_COLS_KEY = "market_grid_hidden_cols_v1";

const DELAY_LABEL =
  process.env.NEXT_PUBLIC_POLYGON_REALTIME === "true" ? "Real-time" : "15-min delay";

// ── Column definitions ────────────────────────────────────────────────────────

interface ColDef {
  key: SortKey;
  label: string;
  subLabel?: string;
  sticky?: boolean;
  required?: boolean;   // cannot be hidden
}

const COLUMNS: ColDef[] = [
  { key: "symbol",             label: "Symbol",                  sticky: true, required: true },
  { key: "pre_mkt_price",      label: "Open/Pre",  subLabel: "Price"    },
  { key: "pre_mkt_change",     label: "Open/Pre",  subLabel: "vs Prev"  },
  { key: "last_price",         label: "Last Price"                        },
  { key: "change",             label: "Change"                            },
  { key: "post_mkt_price",     label: "AH/Post",   subLabel: "Price"    },
  { key: "post_mkt_change",    label: "AH/Post",   subLabel: "vs Close" },
  { key: "earnings_date",      label: "Earnings Date"                     },
  { key: "market_cap",         label: "Market Cap"                        },
  { key: "div_payment_date",   label: "Div Payment", subLabel: "Date"   },
  { key: "exchange",           label: "Exchange"                          },
  { key: "week_52_high",       label: "52-Wk High"                        },
  { key: "week_52_low",        label: "52-Wk Low"                         },
  { key: "shares_outstanding", label: "Shares Out"                        },
];

// ── Live price cell ───────────────────────────────────────────────────────────

function LivePriceCell({ live, fallback }: { live: LivePriceUpdate | null; fallback: number | null }) {
  const [flashClass, setFlashClass] = useState("");
  const prevTsRef = useRef<number>(0);

  useEffect(() => {
    if (!live || live.ts === prevTsRef.current) return;
    prevTsRef.current = live.ts;
    if (live.prevPrice == null) return;
    const dir = live.price > live.prevPrice ? "up" : live.price < live.prevPrice ? "down" : "";
    if (!dir) return;
    setFlashClass(dir === "up" ? "bg-emerald-500/40 text-emerald-200" : "bg-red-500/40 text-red-200");
    const t = setTimeout(() => setFlashClass(""), 1500);
    return () => clearTimeout(t);
  }, [live]);

  const price = live?.price ?? fallback;
  return (
    <span className={`font-mono font-semibold transition-colors duration-700 rounded px-1 py-0.5 ${flashClass || "text-white"}`}>
      {fmtPrice(price)}
    </span>
  );
}

// ── Shared cell class ─────────────────────────────────────────────────────────

const TD = "px-3 py-2 text-xs whitespace-nowrap";

// ── Cell content renderer ─────────────────────────────────────────────────────

function CellContent({
  col,
  row,
  liveInfo,
  onAnalyze,
}: {
  col: ColDef;
  row: MarketQuoteRow;
  liveInfo: LivePriceUpdate | null;
  onAnalyze: (s: string) => void;
}) {
  switch (col.key) {
    case "symbol":
      return (
        <button
          type="button"
          onClick={() => onAnalyze(row.symbol)}
          className="text-indigo-400 hover:text-indigo-200 transition-colors font-bold"
          title="Run analysis"
        >
          {row.symbol}
        </button>
      );
    case "last_price":
      return (
        <span className="flex items-center gap-1">
          <LivePriceCell live={liveInfo} fallback={row.last_price} />
          {liveInfo && (
            <span
              className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0"
              title={`Live price · ${DELAY_LABEL}`}
            />
          )}
        </span>
      );
    case "pre_mkt_price":    return <span className="font-mono text-gray-300">{fmtPrice(row.pre_mkt_price)}</span>;
    case "pre_mkt_change":   return <span className={`font-mono font-semibold ${chgColor(row.pre_mkt_change)}`}>{fmtChange(row.pre_mkt_change)}</span>;
    case "change":           return <span className={`font-mono font-semibold ${chgColor(row.change)}`}>{fmtChange(row.change)}</span>;
    case "post_mkt_price":   return <span className="font-mono text-gray-300">{fmtPrice(row.post_mkt_price)}</span>;
    case "post_mkt_change":  return <span className={`font-mono ${chgColor(row.post_mkt_change)}`}>{fmtChange(row.post_mkt_change)}</span>;
    case "earnings_date":    return <span className="text-gray-400">{row.earnings_date ?? "--"}</span>;
    case "market_cap":       return <span className="text-gray-300">{fmtCap(row.market_cap)}</span>;
    case "div_payment_date": return <span className="text-gray-400">{row.div_payment_date ?? "--"}</span>;
    case "exchange":         return <span className="text-gray-500">{row.exchange ?? "--"}</span>;
    case "week_52_high":     return <span className="font-mono text-gray-300">{fmtPrice(row.week_52_high)}</span>;
    case "week_52_low":      return <span className="font-mono text-gray-300">{fmtPrice(row.week_52_low)}</span>;
    case "shares_outstanding": return <span className="text-gray-300">{fmtShares(row.shares_outstanding)}</span>;
    default:                 return null;
  }
}

// ── SortableHeader ────────────────────────────────────────────────────────────

function SortArrow({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="ml-1 text-gray-700">↕</span>;
  return <span className="ml-1 text-indigo-400">{dir === "asc" ? "↑" : "↓"}</span>;
}

function Th({ col, sortKey, sortDir, onSort }: {
  col: ColDef; sortKey: SortKey; sortDir: SortDir; onSort: (k: SortKey) => void;
}) {
  const active = sortKey === col.key;
  return (
    <th
      onClick={() => onSort(col.key)}
      className={[
        "px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap",
        "select-none cursor-pointer transition-colors",
        active ? "text-indigo-300 bg-gray-800/60" : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/30",
        col.sticky ? "sticky left-0 bg-gray-900 z-10" : "",
      ].join(" ")}
    >
      {col.subLabel ? <span>{col.label}<br />{col.subLabel}</span> : col.label}
      <SortArrow active={active} dir={sortDir} />
    </th>
  );
}

// ── Row ───────────────────────────────────────────────────────────────────────

function Row({
  row,
  onAnalyze,
  liveInfo,
  visibleCols,
}: {
  row: MarketQuoteRow;
  onAnalyze: (s: string) => void;
  liveInfo?: LivePriceUpdate | null;
  visibleCols: ColDef[];
}) {
  return (
    <tr className="border-b border-gray-800/70 hover:bg-gray-800/30 transition-colors">
      {visibleCols.map((col) => (
        <td
          key={col.key}
          className={`${TD}${col.sticky ? " sticky left-0 bg-gray-950 z-10" : ""}`}
        >
          <CellContent col={col} row={row} liveInfo={liveInfo ?? null} onAnalyze={onAnalyze} />
        </td>
      ))}
    </tr>
  );
}

// ── CSV export ────────────────────────────────────────────────────────────────

function exportCsv(rows: MarketQuoteRow[], cols: ColDef[]): void {
  const header = cols.map((c) => c.subLabel ? `${c.label} ${c.subLabel}` : c.label).join(",");
  const body = rows.map((row) =>
    cols.map((col) => {
      const v = row[col.key as keyof MarketQuoteRow];
      if (v == null) return "";
      const s = String(v);
      return s.includes(",") || s.includes('"') || s.includes("\n")
        ? `"${s.replace(/"/g, '""')}"`
        : s;
    }).join(",")
  );
  const csv = [header, ...body].join("\r\n");
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `market-grid-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Column picker dropdown ────────────────────────────────────────────────────

function ColumnPicker({
  hiddenCols,
  onToggle,
  onReset,
}: {
  hiddenCols: Set<SortKey>;
  onToggle: (key: SortKey) => void;
  onReset: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  const hiddenCount = hiddenCols.size;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`px-3 py-1.5 text-sm rounded border transition-colors ${
          hiddenCount > 0
            ? "bg-indigo-900/30 border-indigo-700/50 text-indigo-300"
            : "bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700"
        }`}
      >
        Columns
        {hiddenCount > 0 && (
          <span className="ml-1.5 text-xs bg-indigo-600 text-white px-1.5 py-0.5 rounded-full">
            {hiddenCount} hidden
          </span>
        )}
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg p-3 z-20 w-52 shadow-xl">
          <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-800">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Columns</span>
            {hiddenCount > 0 && (
              <button type="button" onClick={onReset}
                className="text-xs text-indigo-400 hover:text-indigo-200 transition-colors">
                Show all
              </button>
            )}
          </div>
          {COLUMNS.filter((c) => !c.required).map((col) => (
            <label
              key={col.key}
              className="flex items-center gap-2.5 py-1.5 cursor-pointer text-xs text-gray-300 hover:text-white select-none"
            >
              <input
                type="checkbox"
                checked={!hiddenCols.has(col.key)}
                onChange={() => onToggle(col.key)}
                className="w-3.5 h-3.5 rounded border-gray-600 bg-gray-800 accent-indigo-500"
              />
              {col.label}{col.subLabel ? ` (${col.subLabel})` : ""}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

interface MarketGridProps {
  onAnalyze?: (symbol: string) => void;
}

export function MarketGrid({ onAnalyze }: MarketGridProps) {
  const [symbols, setSymbols] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(MARKET_GRID_SYMBOLS_KEY);
      return stored ? JSON.parse(stored) : DEFAULT_SYMBOLS;
    } catch { return DEFAULT_SYMBOLS; }
  });

  const [intervalSec, setIntervalSec] = useState<number>(() => {
    return Number(localStorage.getItem(INTERVAL_KEY) ?? "10");
  });

  const [hiddenCols, setHiddenCols] = useState<Set<SortKey>>(() => {
    try {
      const stored = localStorage.getItem(HIDDEN_COLS_KEY);
      return stored ? new Set(JSON.parse(stored) as SortKey[]) : new Set<SortKey>();
    } catch { return new Set<SortKey>(); }
  });

  const [rows, setRows]               = useState<MarketQuoteRow[]>([]);
  const [loading, setLoading]         = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError]             = useState<string | null>(null);
  const [countdown, setCountdown]     = useState(0);
  const [addInput, setAddInput]       = useState("");
  const [intervalInput, setIntervalInput] = useState(String(intervalSec));
  const [sortKey, setSortKey]         = useState<SortKey>("market_cap");
  const [sortDir, setSortDir]         = useState<SortDir>("desc");

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cdRef    = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { localStorage.setItem(MARKET_GRID_SYMBOLS_KEY, JSON.stringify(symbols)); }, [symbols]);
  useEffect(() => { localStorage.setItem(INTERVAL_KEY, String(intervalSec)); }, [intervalSec]);
  useEffect(() => {
    localStorage.setItem(HIDDEN_COLS_KEY, JSON.stringify(Array.from(hiddenCols)));
  }, [hiddenCols]);

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

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => d === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      const numericCols: SortKey[] = [
        "last_price", "change", "pre_mkt_price", "pre_mkt_change",
        "post_mkt_price", "post_mkt_change", "market_cap",
        "week_52_high", "week_52_low", "shares_outstanding",
      ];
      setSortDir(numericCols.includes(key) ? "desc" : "asc");
    }
  }

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

  function toggleCol(key: SortKey) {
    setHiddenCols((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  }

  const { livePrices, connected: wsConnected } = useMarketGridWs(symbols);
  const sortedRows  = sortRows(rows, sortKey, sortDir);
  const visibleCols = COLUMNS.filter((c) => !hiddenCols.has(c.key));

  return (
    <div className="space-y-3">
      {/* ── Controls ── */}
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
              maxLength={12}
              className="w-28 bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button type="button" onClick={addSymbol}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded transition-colors">
            Add
          </button>
        </div>

        {/* Refresh interval */}
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

        {/* Refresh now */}
        <button type="button" onClick={() => { fetchQuotes(); setCountdown(intervalSec); }}
          disabled={loading}
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded border border-gray-700 transition-colors disabled:opacity-50">
          {loading ? "Refreshing…" : "↻ Refresh now"}
        </button>

        {/* CSV export */}
        <button type="button" onClick={() => exportCsv(sortedRows, visibleCols)}
          disabled={sortedRows.length === 0}
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded border border-gray-700 transition-colors disabled:opacity-40"
          title="Download current view as CSV">
          ↓ CSV
        </button>

        {/* Column picker */}
        <ColumnPicker
          hiddenCols={hiddenCols}
          onToggle={toggleCol}
          onReset={() => setHiddenCols(new Set())}
        />

        {/* Active sort indicator */}
        {sortKey !== "market_cap" && (
          <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1.5 rounded border border-gray-700">
            Sorted by <span className="text-indigo-400">
              {COLUMNS.find((c) => c.key === sortKey)?.label}
            </span> {sortDir === "asc" ? "↑" : "↓"}
            <button
              type="button"
              onClick={() => { setSortKey("market_cap"); setSortDir("desc"); }}
              className="ml-2 text-gray-600 hover:text-red-400 transition-colors"
              title="Reset sort"
            >
              ✕
            </button>
          </span>
        )}

        {/* WebSocket / delay status */}
        <span
          className={`flex items-center gap-1.5 text-xs px-2 py-1.5 rounded border ${
            wsConnected
              ? "text-emerald-400 border-emerald-800/50 bg-emerald-950/30"
              : "text-gray-600 border-gray-800 bg-gray-900"
          }`}
          title={
            wsConnected
              ? `Live WebSocket connected · Polygon ${DELAY_LABEL}`
              : "Live price feed disconnected"
          }
        >
          <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? "bg-emerald-400 animate-pulse" : "bg-gray-700"}`} />
          {wsConnected ? `Live · ${DELAY_LABEL}` : "Offline"}
        </span>

        {/* Timers */}
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
                {visibleCols.map((col) => (
                  <Th key={col.key} col={col} sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
                ))}
              </tr>
            </thead>
            <tbody className="bg-gray-950 divide-y divide-gray-800/50">
              {sortedRows.length === 0 && !loading && (
                <tr>
                  <td colSpan={visibleCols.length} className="px-3 py-10 text-center text-xs text-gray-600">
                    {symbols.length === 0 ? "Add symbols above to populate the grid." : "Loading…"}
                  </td>
                </tr>
              )}
              {sortedRows.map((row) => (
                <Row
                  key={row.symbol}
                  row={row}
                  onAnalyze={onAnalyze ?? (() => {})}
                  liveInfo={livePrices[row.symbol]}
                  visibleCols={visibleCols}
                />
              ))}
            </tbody>
          </table>
        </div>
        {loading && <div className="h-0.5 bg-indigo-600/70 animate-pulse" />}
      </div>

      <p className="text-xs text-gray-700 italic">
        Snapshot prices via Polygon.io ({DELAY_LABEL}) · Live ticks via Polygon WebSocket ({DELAY_LABEL}) ·
        Pre/post-market via Yahoo Finance (near real-time during those sessions) · Not investment advice.
      </p>
    </div>
  );
}
