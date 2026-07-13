"use client";

import { useEffect, useState } from "react";

import { getMarketQuotes } from "@/lib/api";
import { MARKET_GRID_SYMBOLS_KEY } from "@/components/market/MarketGrid";
import type { MarketQuoteRow } from "@/types/api";

const DEFAULT_SYMBOLS = [
  "NVDA", "MSFT", "AAPL", "GOOG", "AMZN", "META", "AVGO", "TSM", "TSLA", "BRK-B",
  "ORCL", "LLY", "V", "SPY", "NFLX", "PLTR", "COST", "ASML", "AMD", "NVO",
  "CRM", "MU", "NOW", "BLK", "ARM", "ADBE", "PANW", "VUG", "GLD", "CRWV",
  "DXCM", "JBL", "QS", "TQQQ",
];

interface EarningsEntry {
  symbol: string;
  date: string;       // "YYYY/MM/DD" from API
  daysAway: number;   // negative = past
  marketCap: number | null;
}

function parseDateStr(s: string): Date | null {
  const m = s.match(/^(\d{4})\/(\d{2})\/(\d{2})$/);
  if (!m) return null;
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
}

function formatDate(s: string): string {
  const d = parseDateStr(s);
  if (!d) return s;
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" });
}

function daysFromToday(s: string): number {
  const d = parseDateStr(s);
  if (!d) return 0;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - today.getTime()) / 86_400_000);
}

function fmtCap(v: number | null): string {
  if (v == null) return "";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(1)}T`;
  if (v >= 1e9)  return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6)  return `$${(v / 1e6).toFixed(0)}M`;
  return `$${v.toLocaleString()}`;
}

function DaysChip({ days }: { days: number }) {
  if (days < -7)
    return <span className="text-xs text-gray-600 bg-gray-800 px-2 py-0.5 rounded-full">{Math.abs(days)}d ago</span>;
  if (days < 0)
    return <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">{Math.abs(days)}d ago</span>;
  if (days === 0)
    return <span className="text-xs text-amber-300 bg-amber-900/40 border border-amber-700/50 px-2 py-0.5 rounded-full font-semibold">Today</span>;
  if (days === 1)
    return <span className="text-xs text-orange-300 bg-orange-900/40 border border-orange-700/50 px-2 py-0.5 rounded-full font-semibold">Tomorrow</span>;
  if (days <= 7)
    return <span className="text-xs text-yellow-300 bg-yellow-900/30 border border-yellow-700/40 px-2 py-0.5 rounded-full">In {days}d</span>;
  if (days <= 30)
    return <span className="text-xs text-blue-300 bg-blue-900/30 border border-blue-700/40 px-2 py-0.5 rounded-full">In {days}d</span>;
  return <span className="text-xs text-gray-400 bg-gray-800/60 px-2 py-0.5 rounded-full">In {days}d</span>;
}

export function EarningsCalendar() {
  const [entries, setEntries]     = useState<EarningsEntry[]>([]);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [showPast, setShowPast]   = useState(false);
  const [symbols, setSymbols]     = useState<string[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(MARKET_GRID_SYMBOLS_KEY);
      const syms = stored ? JSON.parse(stored) : DEFAULT_SYMBOLS;
      setSymbols(syms.filter((s: string) => !s.startsWith("^")));
    } catch {
      setSymbols(DEFAULT_SYMBOLS);
    }
  }, []);

  useEffect(() => {
    if (!symbols.length) return;
    setLoading(true);
    setError(null);

    const chunks: string[][] = [];
    for (let i = 0; i < symbols.length; i += 40) chunks.push(symbols.slice(i, i + 40));

    Promise.all(chunks.map((chunk) => getMarketQuotes(chunk)))
      .then((results) => {
        const all: MarketQuoteRow[] = results.flat();
        const parsed: EarningsEntry[] = all
          .filter((r): r is MarketQuoteRow & { earnings_date: string } => !!r.earnings_date)
          .map((r) => ({
            symbol: r.symbol,
            date: r.earnings_date!,
            daysAway: daysFromToday(r.earnings_date!),
            marketCap: r.market_cap ?? null,
          }))
          .sort((a, b) => a.daysAway - b.daysAway);
        setEntries(parsed);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [symbols]);

  const visible  = showPast ? entries : entries.filter((e) => e.daysAway >= -7);
  const upcoming = visible.filter((e) => e.daysAway >= 0);
  const recent   = visible.filter((e) => e.daysAway < 0);

  // Group upcoming by date string for calendar-like view
  const byDate = new Map<string, EarningsEntry[]>();
  for (const e of upcoming) {
    const k = e.date;
    if (!byDate.has(k)) byDate.set(k, []);
    byDate.get(k)!.push(e);
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-3">
        <p className="text-xs text-gray-500">
          Showing earnings dates for {symbols.length} tracked symbols. Data via Yahoo Finance.
        </p>
        <button
          type="button"
          onClick={() => setShowPast((v) => !v)}
          className="ml-auto text-xs px-2 py-1 bg-gray-800 border border-gray-700 text-gray-400 hover:text-white rounded transition-colors"
        >
          {showPast ? "Hide past" : "Show past 30 days"}
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="w-3 h-3 border border-gray-600 border-t-indigo-400 rounded-full animate-spin" />
          Loading earnings dates…
        </div>
      )}

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">{error}</p>
      )}

      {!loading && entries.length === 0 && !error && (
        <p className="text-xs text-gray-600">No earnings dates found for your tracked symbols.</p>
      )}

      {/* Upcoming earnings — grouped by date */}
      {upcoming.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-white">Upcoming Earnings</h2>
          {Array.from(byDate.entries()).map(([date, group]) => (
            <div key={date} className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-gray-300">{formatDate(date)}</span>
                <DaysChip days={group[0].daysAway} />
                <div className="flex-1 h-px bg-gray-800" />
                <span className="text-xs text-gray-600">{group.length} {group.length > 1 ? "companies" : "company"}</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                {group
                  .sort((a: EarningsEntry, b: EarningsEntry) => (b.marketCap ?? 0) - (a.marketCap ?? 0))
                  .map((e: EarningsEntry) => (
                  <div
                    key={e.symbol}
                    className={`rounded-lg border px-3 py-2.5 space-y-0.5 ${
                      e.daysAway === 0
                        ? "border-amber-700/60 bg-amber-950/30"
                        : e.daysAway === 1
                        ? "border-orange-700/50 bg-orange-950/20"
                        : e.daysAway <= 7
                        ? "border-yellow-800/40 bg-yellow-950/20"
                        : "border-gray-800 bg-gray-900/60"
                    }`}
                  >
                    <p className="text-sm font-bold text-indigo-400">{e.symbol}</p>
                    {e.marketCap && (
                      <p className="text-xs text-gray-500">{fmtCap(e.marketCap)}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Recent past */}
      {recent.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-500">Recent (Last 7 Days)</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {recent
              .sort((a, b) => b.daysAway - a.daysAway)
              .map((e) => (
              <div key={e.symbol}
                className="rounded-lg border border-gray-800/60 bg-gray-900/40 px-3 py-2.5 opacity-60 space-y-0.5">
                <p className="text-sm font-bold text-gray-400">{e.symbol}</p>
                <div className="flex items-center gap-1.5">
                  <DaysChip days={e.daysAway} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {upcoming.length === 0 && !loading && entries.length > 0 && (
        <p className="text-xs text-gray-600">No upcoming earnings dates found. Check back closer to earnings season.</p>
      )}
    </div>
  );
}
