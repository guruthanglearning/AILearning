"use client";

import { useState } from "react";

import { useMomentumSectors } from "@/hooks/useMomentumSectors";
import type { MomentumStockRow } from "@/types/api";

// ── Skeleton loading ──────────────────────────────────────────────────────────

// All Sectors: #, Symbol, Score, Company, Sector, Industry, Price, 52W High, 52W Low, 1M%, 3M%, 6M%, vs S&P, RSI, Day%
const SKELETON_ALL    = ["w-6","w-12","w-20","w-28","w-20","w-20","w-14","w-14","w-14","w-12","w-12","w-12","w-12","w-10","w-12"];
// Per-sector:   #, Symbol, Score, Company, Industry, Price, 52W High, 52W Low, 1M%, 3M%, 6M%, vs S&P, RSI, Day%
const SKELETON_SECTOR = ["w-6","w-12","w-20","w-28","w-20","w-14","w-14","w-14","w-12","w-12","w-12","w-12","w-10","w-12"];

function SkeletonRow({ showSector }: { showSector: boolean }) {
  const widths = showSector ? SKELETON_ALL : SKELETON_SECTOR;
  return (
    <tr className="border-b border-gray-800/70">
      {widths.map((w, i) => (
        <td key={i} className="px-3 py-3">
          <div className={`h-2.5 bg-gray-800 rounded animate-pulse ${w}`} />
        </td>
      ))}
    </tr>
  );
}

function SkeletonTabs() {
  const widths = [96, 88, 120, 108, 72, 80, 96, 128, 64, 80, 80, 72];
  return (
    <div className="flex flex-wrap gap-1.5">
      {widths.map((w, i) => (
        <div key={i} className="h-6 rounded-full bg-gray-800 animate-pulse" style={{ width: `${w}px` }} />
      ))}
    </div>
  );
}

// ── Formatters ────────────────────────────────────────────────────────────────

function fmtPrice(v: number | null): string {
  if (v == null) return "--";
  return v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtPct(v: number | null): string {
  if (v == null) return "--";
  return (v >= 0 ? "+" : "") + v.toFixed(2) + "%";
}

function fmtReturn(v: number | null): string {
  if (v == null) return "--";
  const pct = v * 100;
  return (pct >= 0 ? "+" : "") + pct.toFixed(1) + "%";
}

function pctColor(v: number | null): string {
  if (v == null) return "text-gray-500";
  return v > 0 ? "text-green-400" : v < 0 ? "text-red-400" : "text-gray-400";
}

// ── Score bar ─────────────────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-600 text-xs">--</span>;
  const pct = Math.max(0, Math.min(100, score));
  const color = pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";
  const label = pct >= 70 ? "text-green-300" : pct >= 40 ? "text-amber-300" : "text-red-300";
  return (
    <div className="flex items-center gap-2 min-w-[90px]">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-mono font-semibold w-8 text-right shrink-0 ${label}`}>
        {pct.toFixed(0)}
      </span>
    </div>
  );
}

// ── RSI badge ─────────────────────────────────────────────────────────────────

function RsiBadge({ rsi }: { rsi: number | null }) {
  if (rsi == null) return <span className="text-gray-600 text-xs">--</span>;
  let cls: string;
  let hint: string;
  if (rsi > 80)       { cls = "bg-red-900/60 text-red-300 border-red-700/50";     hint = "Overbought"; }
  else if (rsi > 70)  { cls = "bg-amber-900/60 text-amber-300 border-amber-700/50"; hint = "Watch"; }
  else if (rsi >= 50) { cls = "bg-green-900/60 text-green-300 border-green-700/50"; hint = "Strong trend"; }
  else if (rsi >= 40) { cls = "bg-gray-800 text-gray-400 border-gray-600";         hint = "Weakening"; }
  else                { cls = "bg-red-900/60 text-red-300 border-red-700/50";     hint = "Oversold"; }
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${cls}`} title={hint}>
      {rsi.toFixed(0)}
    </span>
  );
}

// ── Sort helpers ──────────────────────────────────────────────────────────────

type SortKey = keyof MomentumStockRow | "__rank__";
type SortDir = "asc" | "desc";

const NUMERIC_STOCK_COLS: (keyof MomentumStockRow)[] = [
  "pre_market","open_price","close_price","post_market",
  "momentum_score","day_change_pct","week_52_high","week_52_low",
  "return_1m","return_3m","return_6m","vs_spy_6m","rsi_14",
];

function getValue(row: MomentumStockRow, key: keyof MomentumStockRow): string | number {
  const v = row[key];
  if (v == null) return NUMERIC_STOCK_COLS.includes(key) ? -Infinity : "";
  return v as string | number;
}

function sortRows(rows: MomentumStockRow[], key: SortKey, dir: SortDir): MomentumStockRow[] {
  if (key === "__rank__") return dir === "asc" ? [...rows] : [...rows].reverse();
  const k = key as keyof MomentumStockRow;
  return [...rows].sort((a, b) => {
    const av = getValue(a, k);
    const bv = getValue(b, k);
    if (av === bv) return 0;
    const cmp = typeof av === "string" && typeof bv === "string"
      ? av.localeCompare(bv)
      : (av as number) < (bv as number) ? -1 : 1;
    return dir === "asc" ? cmp : -cmp;
  });
}

// ── Column definitions ────────────────────────────────────────────────────────

interface ColDef {
  key: SortKey;
  label: string;
  title: string;
  sticky?: boolean;
  numeric?: boolean;
}

const RANK_COL: ColDef = {
  key: "__rank__", label: "#", numeric: true,
  title: "Rank by composite momentum score (1 = strongest momentum)",
};

const BASE_COLS: ColDef[] = [
  { key: "symbol",         label: "Symbol",  sticky: true, title: "Click to run AI analysis on this stock" },
  { key: "momentum_score", label: "Score",   numeric: true,
    title: "Composite score 0–100. Combines how this stock's 1M/3M/6M returns rank against the other 110 stocks in our universe, plus SMA trend confirmation and 52-week high proximity." },
  { key: "company_name",   label: "Company", title: "Company name" },
];

const SECTOR_COL: ColDef = {
  key: "sector", label: "Sector",
  title: "GICS sector — tells you which part of the economy this company operates in",
};

const DETAIL_COLS: ColDef[] = [
  { key: "industry",       label: "Industry",  title: "Industry sub-group within the sector" },
  { key: "close_price",    label: "Price",     numeric: true, title: "Latest closing price (USD)" },
  { key: "week_52_high",   label: "52W High",  numeric: true, title: "Highest closing price over the past 52 weeks — proximity to this level signals strong momentum" },
  { key: "week_52_low",    label: "52W Low",   numeric: true, title: "Lowest closing price over the past 52 weeks — distance from this level shows recovery strength" },
  { key: "return_1m",      label: "1-Month",   numeric: true,
    title: "Price return over the past 1 month (~21 trading days). Shows recent momentum." },
  { key: "return_3m",      label: "3-Month",  numeric: true,
    title: "Price return over the past 3 months (~63 trading days). The core momentum signal." },
  { key: "return_6m",      label: "6-Month",  numeric: true,
    title: "Price return over the past 6 months (~126 trading days). The strongest predictor of continued momentum per academic research." },
  { key: "vs_spy_6m",      label: "vs S&P",   numeric: true,
    title: "6-month return minus the S&P 500 return over the same period. Positive means this stock beat the market (excess return / alpha)." },
  { key: "rsi_14",         label: "RSI",      numeric: true,
    title: "14-day Relative Strength Index. 50–70 = healthy uptrend (green). >80 = potentially overbought, momentum may stall (red). <30 = oversold (red)." },
  { key: "day_change_pct", label: "Today",    numeric: true, title: "Today's price change %" },
];

function getColumns(showSector: boolean): ColDef[] {
  return showSector
    ? [RANK_COL, ...BASE_COLS, SECTOR_COL, ...DETAIL_COLS]
    : [RANK_COL, ...BASE_COLS, ...DETAIL_COLS];
}

// ── Sortable header ───────────────────────────────────────────────────────────

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
      title={col.title}
      className={[
        "px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap",
        "select-none cursor-pointer transition-colors",
        active
          ? "text-indigo-300 bg-gray-800/60"
          : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/30",
        col.sticky ? "sticky left-0 bg-gray-900 z-10" : "",
      ].join(" ")}
    >
      {col.label}
      <SortArrow active={active} dir={sortDir} />
    </th>
  );
}

// ── Table row ─────────────────────────────────────────────────────────────────

const TD = "px-3 py-2 text-xs whitespace-nowrap";

const RANK_COLORS: Record<number, string> = {
  1: "text-yellow-400 font-bold",
  2: "text-gray-300 font-bold",
  3: "text-amber-600 font-bold",
};

function StockRow({ row, rank, showSector, onAnalyze }: {
  row: MomentumStockRow; rank: number; showSector: boolean; onAnalyze: (s: string) => void;
}) {
  return (
    <tr className="border-b border-gray-800/70 hover:bg-gray-800/30 transition-colors">
      {/* Rank */}
      <td className={`${TD} text-center ${RANK_COLORS[rank] ?? "text-gray-600"}`}>
        {rank}
      </td>
      {/* Symbol */}
      <td className={`${TD} font-bold sticky left-0 bg-gray-950 z-10`}>
        <button
          type="button"
          onClick={() => onAnalyze(row.symbol)}
          className="text-indigo-400 hover:text-indigo-200 transition-colors"
          title="Open AI analysis for this stock"
        >
          {row.symbol}
        </button>
      </td>
      {/* Score */}
      <td className={TD}>
        <ScoreBar score={row.momentum_score} />
      </td>
      {/* Company */}
      <td className={`${TD} text-gray-300 max-w-[160px] truncate`} title={row.company_name ?? ""}>
        {row.company_name ?? "--"}
      </td>
      {/* Sector (All Sectors only) */}
      {showSector && (
        <td className={`${TD} text-gray-400 max-w-[130px] truncate`} title={row.sector ?? ""}>
          {row.sector ?? "--"}
        </td>
      )}
      {/* Industry */}
      <td className={`${TD} text-gray-500 max-w-[130px] truncate`} title={row.industry ?? ""}>
        {row.industry ?? "--"}
      </td>
      {/* Price */}
      <td className={`${TD} font-mono font-semibold text-white`}>
        {fmtPrice(row.close_price)}
      </td>
      {/* 52-week range */}
      <td className={`${TD} font-mono text-gray-400`}>{fmtPrice(row.week_52_high)}</td>
      <td className={`${TD} font-mono text-gray-500`}>{fmtPrice(row.week_52_low)}</td>
      {/* Return columns */}
      <td className={`${TD} font-mono font-semibold ${pctColor(row.return_1m)}`}>
        {fmtReturn(row.return_1m)}
      </td>
      <td className={`${TD} font-mono font-semibold ${pctColor(row.return_3m)}`}>
        {fmtReturn(row.return_3m)}
      </td>
      <td className={`${TD} font-mono font-semibold ${pctColor(row.return_6m)}`}>
        {fmtReturn(row.return_6m)}
      </td>
      <td
        className={`${TD} font-mono font-semibold ${pctColor(row.vs_spy_6m)}`}
        title={row.vs_spy_6m != null ? `Beat S&P 500 by ${(row.vs_spy_6m * 100).toFixed(1)}% over 6 months` : ""}
      >
        {fmtReturn(row.vs_spy_6m)}
      </td>
      {/* RSI */}
      <td className={TD}>
        <RsiBadge rsi={row.rsi_14} />
      </td>
      {/* Day change */}
      <td className={`${TD} font-mono font-semibold ${pctColor(row.day_change_pct)}`}>
        {fmtPct(row.day_change_pct)}
      </td>
    </tr>
  );
}

// ── Info panel (explains what the user is looking at) ────────────────────────

function InfoPanel({ isAllSectors }: { isAllSectors: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-md border border-gray-800 bg-gray-900/60 text-xs">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-gray-400 hover:text-gray-200 transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className="text-indigo-400">ℹ</span>
          <span className="font-medium">
            {isAllSectors
              ? "What am I looking at? — All Sectors (Top 10 across all markets)"
              : "What am I looking at? — Single Sector view"}
          </span>
        </span>
        <span className="text-gray-600">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-800 pt-3 text-gray-400 leading-relaxed">
          {isAllSectors ? (
            <>
              <p>
                <span className="text-gray-200 font-medium">All Sectors</span> answers the question:{" "}
                <span className="text-indigo-300 italic">
                  "Which 10 stocks, out of 110 large-cap names across all 11 market sectors, have the strongest price momentum right now?"
                </span>
              </p>
              <p>
                Every stock is scored 0–100 by comparing its returns against all other stocks in our
                universe — not against a fixed target. A score of 80 means this stock outperformed
                roughly 80% of all 110 stocks across multiple timeframes. This is called{" "}
                <span className="text-gray-300">cross-sectional ranking</span>.
              </p>
            </>
          ) : (
            <p>
              <span className="text-gray-200 font-medium">Single Sector</span> shows the top 10
              momentum stocks within the selected GICS sector, ranked the same way — by how each
              stock's returns compare against the full 110-stock universe.
            </p>
          )}

          <div className="grid grid-cols-1 gap-2 mt-2">
            <p className="text-gray-300 font-medium">Column guide:</p>
            <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
              <div><span className="text-indigo-300 font-mono">#</span> — Rank by momentum score (1 = strongest)</div>
              <div><span className="text-indigo-300 font-mono">Score</span> — Composite 0–100: how this stock ranks vs. all 110 peers</div>
              <div><span className="text-indigo-300 font-mono">1-Month</span> — Price return over the last ~1 month</div>
              <div><span className="text-indigo-300 font-mono">3-Month</span> — Price return over the last ~3 months</div>
              <div><span className="text-indigo-300 font-mono">6-Month</span> — Price return over the last ~6 months (heaviest weight in score)</div>
              <div><span className="text-indigo-300 font-mono">vs S&P</span> — 6M return minus S&P 500's 6M return; shows if the stock <em>beat the market</em></div>
              <div>
                <span className="text-indigo-300 font-mono">RSI</span> — Relative Strength Index (14-day):{" "}
                <span className="text-green-400">50–70 = healthy uptrend</span>,{" "}
                <span className="text-amber-400">70–80 = watch for reversal</span>,{" "}
                <span className="text-red-400">&gt;80 = overbought</span>
              </div>
              <div><span className="text-indigo-300 font-mono">Today</span> — Price change % today</div>
            </div>
          </div>

          <p className="text-gray-600 italic border-t border-gray-800 pt-2">
            Score formula: 6M return rank (30%) + 3M rank (20%) + vs-S&P rank (20%) + 1M rank (10%) +
            SMA trend alignment (12 pts) + proximity to 52-week high (8 pts) − penalty if RSI is extreme.
            Not investment advice.
          </p>
        </div>
      )}
    </div>
  );
}

// ── Sector colour badges ──────────────────────────────────────────────────────

const SECTOR_COLORS: Record<string, string> = {
  "Technology":             "bg-blue-900/50 text-blue-300 border-blue-700/50",
  "Consumer Cyclical":      "bg-orange-900/50 text-orange-300 border-orange-700/50",
  "Communication Services": "bg-purple-900/50 text-purple-300 border-purple-700/50",
  "Healthcare":             "bg-green-900/50 text-green-300 border-green-700/50",
  "Financials":             "bg-yellow-900/50 text-yellow-300 border-yellow-700/50",
  "Industrials":            "bg-gray-800/80 text-gray-300 border-gray-600/50",
  "Consumer Defensive":     "bg-teal-900/50 text-teal-300 border-teal-700/50",
  "Energy":                 "bg-amber-900/50 text-amber-300 border-amber-700/50",
  "Basic Materials":        "bg-lime-900/50 text-lime-300 border-lime-700/50",
  "Real Estate":            "bg-rose-900/50 text-rose-300 border-rose-700/50",
  "Utilities":              "bg-cyan-900/50 text-cyan-300 border-cyan-700/50",
};

// ── Main component ────────────────────────────────────────────────────────────

const ALL_SECTORS_KEY = "__all__";

interface MomentumGridProps {
  onAnalyze?: (symbol: string) => void;
}

export function MomentumGrid({ onAnalyze }: MomentumGridProps) {
  const { data, isLoading, error, countdown, refresh } = useMomentumSectors(10);
  const [activeSector, setActiveSector] = useState<string>(ALL_SECTORS_KEY);
  const [sortKey, setSortKey] = useState<SortKey>("__rank__");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const sectors = data?.sectors ?? [];
  const isAllSectors = activeSector === ALL_SECTORS_KEY;

  // All-sectors: flatten → sort by score → top 10 (these become ranks #1–#10)
  const allSectorsTop10 = sectors
    .flatMap((s) => s.stocks)
    .sort((a, b) => (b.momentum_score ?? -1) - (a.momentum_score ?? -1))
    .slice(0, 10);

  const sectorData = sectors.find((s) => s.sector === activeSector);
  const baseRows = isAllSectors ? allSectorsTop10 : (sectorData?.stocks ?? []);

  // Preserve original rank position across re-sorts
  const rankedRows = baseRows.map((row, i) => ({ row, rank: i + 1 }));
  const sortedPairs = sortKey === "__rank__"
    ? (sortDir === "asc" ? rankedRows : [...rankedRows].reverse())
    : [...rankedRows].sort((a, b) => {
        const av = getValue(a.row, sortKey as keyof MomentumStockRow);
        const bv = getValue(b.row, sortKey as keyof MomentumStockRow);
        if (av === bv) return 0;
        const cmp = typeof av === "string" && typeof bv === "string"
          ? av.localeCompare(bv)
          : (av as number) < (bv as number) ? -1 : 1;
        return sortDir === "asc" ? cmp : -cmp;
      });

  const columns = getColumns(isAllSectors);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      const isNum = key === "__rank__" || NUMERIC_STOCK_COLS.includes(key as keyof MomentumStockRow);
      setSortDir(key === "__rank__" ? "asc" : isNum ? "desc" : "asc");
    }
  }

  const fetchedAt = data?.fetched_at_utc
    ? new Date(data.fetched_at_utc).toLocaleTimeString()
    : null;

  // Unique sectors represented in the All Sectors top 10
  const representedSectors = allSectorsTop10
    .map((r) => r.sector)
    .filter((s, i, arr): s is string => s != null && arr.indexOf(s) === i);

  return (
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-base font-semibold text-gray-100">Momentum Sectors</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {isAllSectors
              ? "Top 10 momentum stocks right now — ranked across all 110 large-caps in 11 GICS sectors"
              : `Top 10 momentum stocks in the ${activeSector} sector`}
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {isLoading && !data ? (
            <span className="flex items-center gap-1.5 text-indigo-400">
              <span className="inline-block w-3 h-3 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
              Scanning all sectors…
            </span>
          ) : (
            <>
              {fetchedAt && <span>Updated {fetchedAt}</span>}
              <span className={countdown <= 30 ? "text-amber-500" : ""}>
                Refreshes in {countdown}s
              </span>
            </>
          )}
          <button
            type="button"
            onClick={() => refresh()}
            disabled={isLoading}
            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded border border-gray-700 transition-colors disabled:opacity-50"
          >
            {isLoading ? "Loading…" : "↻ Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
          {error instanceof Error ? error.message : "Failed to load momentum data."}
        </p>
      )}

      {/* ── Sector tabs ── */}
      {isLoading && !data ? (
        <SkeletonTabs />
      ) : sectors.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => { setActiveSector(ALL_SECTORS_KEY); setSortKey("__rank__"); setSortDir("asc"); }}
            className={[
              "px-3 py-1 text-xs rounded-full border transition-colors font-medium",
              isAllSectors
                ? "bg-indigo-600 border-indigo-500 text-white"
                : "bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600",
            ].join(" ")}
          >
            All Sectors
          </button>
          {sectors.map((s) => (
            <button
              key={s.sector}
              type="button"
              onClick={() => { setActiveSector(s.sector); setSortKey("__rank__"); setSortDir("asc"); }}
              className={[
                "px-3 py-1 text-xs rounded-full border transition-colors",
                s.sector === activeSector
                  ? "bg-indigo-600 border-indigo-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600",
              ].join(" ")}
            >
              {s.sector}
            </button>
          ))}
        </div>
      )}

      {/* ── All-sectors context: which sectors are represented ── */}
      {isAllSectors && !isLoading && representedSectors.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-500">Sectors in top 10:</span>
          {representedSectors.map((s) => {
            const count = allSectorsTop10.filter((r) => r.sector === s).length;
            return (
              <span
                key={s}
                className={`text-[10px] px-2 py-0.5 rounded-full border ${SECTOR_COLORS[s] ?? "bg-gray-800 text-gray-400 border-gray-700"}`}
                title={`${count} stock${count > 1 ? "s" : ""} from ${s}`}
              >
                {s} {count > 1 && <span className="opacity-70">×{count}</span>}
              </span>
            );
          })}
        </div>
      )}

      {/* ── Info panel ── */}
      <InfoPanel isAllSectors={isAllSectors} />

      {/* ── Table ── */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-900 border-b border-gray-700">
              <tr>
                {columns.map((col) => (
                  <Th key={String(col.key)} col={col} sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
                ))}
              </tr>
            </thead>
            <tbody className="bg-gray-950 divide-y divide-gray-800/50">
              {isLoading && !data ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <SkeletonRow key={i} showSector={isAllSectors} />
                ))
              ) : sortedPairs.length === 0 && !error ? (
                <tr>
                  <td colSpan={columns.length} className="px-3 py-10 text-center text-xs text-gray-600">
                    No data for this sector.
                  </td>
                </tr>
              ) : (
                sortedPairs.map(({ row, rank }) => (
                  <StockRow
                    key={row.symbol}
                    row={row}
                    rank={rank}
                    showSector={isAllSectors}
                    onAnalyze={(s) => onAnalyze?.(s)}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
        {isLoading && data && <div className="h-0.5 bg-indigo-600/70 animate-pulse" />}
      </div>
    </div>
  );
}
