"use client";

import { useState } from "react";

import { useMomentumSectors } from "@/hooks/useMomentumSectors";
import type { MomentumStockRow } from "@/types/api";

// ── Skeleton loading ──────────────────────────────────────────────────────────

const SKELETON_WIDTHS = ["w-12", "w-28", "w-20", "w-14", "w-14", "w-14", "w-14", "w-20", "w-10"];

function SkeletonRow() {
  return (
    <tr className="border-b border-gray-800/70">
      {SKELETON_WIDTHS.map((w, i) => (
        <td key={i} className="px-3 py-3">
          <div className={`h-2.5 bg-gray-800 rounded animate-pulse ${w}`} />
        </td>
      ))}
    </tr>
  );
}

function SkeletonTabs() {
  const widths = [88, 120, 108, 72, 80, 96, 128, 64, 80, 80, 72];
  return (
    <div className="flex flex-wrap gap-1.5">
      {widths.map((w, i) => (
        <div
          key={i}
          className="h-6 rounded-full bg-gray-800 animate-pulse"
          style={{ width: `${w}px` }}
        />
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

function pctColor(v: number | null): string {
  if (v == null) return "text-gray-500";
  return v > 0 ? "text-green-400" : v < 0 ? "text-red-400" : "text-gray-400";
}

// ── Momentum score bar ────────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-600 text-xs">--</span>;
  const pct = Math.max(0, Math.min(100, score));
  const color =
    pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-300 w-8 text-right shrink-0">
        {pct.toFixed(0)}
      </span>
    </div>
  );
}

// ── Sort helpers ──────────────────────────────────────────────────────────────

type SortKey = keyof MomentumStockRow;
type SortDir = "asc" | "desc";

const NUMERIC_COLS: SortKey[] = [
  "pre_market", "open_price", "close_price", "post_market",
  "momentum_score", "day_change_pct", "week_52_high", "week_52_low",
];

function getValue(row: MomentumStockRow, key: SortKey): string | number {
  const v = row[key];
  if (v == null) return NUMERIC_COLS.includes(key) ? -Infinity : "";
  return v as string | number;
}

function sortRows(rows: MomentumStockRow[], key: SortKey, dir: SortDir): MomentumStockRow[] {
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

// ── Column definitions ────────────────────────────────────────────────────────

interface ColDef {
  key: SortKey;
  label: string;
  subLabel?: string;
  sticky?: boolean;
}

const COLUMNS: ColDef[] = [
  { key: "symbol",        label: "Symbol",    sticky: true },
  { key: "company_name",  label: "Company"                 },
  { key: "industry",      label: "Industry"                },
  { key: "pre_market",    label: "Pre-Mkt",  subLabel: "Price" },
  { key: "open_price",    label: "Open"                    },
  { key: "close_price",   label: "Close"                   },
  { key: "post_market",   label: "Post-Mkt", subLabel: "Price" },
  { key: "momentum_score", label: "Score"                  },
  { key: "day_change_pct", label: "Day Δ%"                 },
];

// ── Sortable header ───────────────────────────────────────────────────────────

function SortArrow({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="ml-1 text-gray-700">↕</span>;
  return <span className="ml-1 text-indigo-400">{dir === "asc" ? "↑" : "↓"}</span>;
}

function Th({
  col, sortKey, sortDir, onSort,
}: {
  col: ColDef; sortKey: SortKey; sortDir: SortDir; onSort: (k: SortKey) => void;
}) {
  const active = sortKey === col.key;
  return (
    <th
      onClick={() => onSort(col.key)}
      className={[
        "px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap",
        "select-none cursor-pointer transition-colors",
        active
          ? "text-indigo-300 bg-gray-800/60"
          : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/30",
        col.sticky ? "sticky left-0 bg-gray-900 z-10" : "",
      ].join(" ")}
    >
      {col.subLabel ? <span>{col.label}<br />{col.subLabel}</span> : col.label}
      <SortArrow active={active} dir={sortDir} />
    </th>
  );
}

// ── Table row ─────────────────────────────────────────────────────────────────

const TD = "px-3 py-2 text-xs whitespace-nowrap";

function StockRow({
  row,
  onAnalyze,
}: {
  row: MomentumStockRow;
  onAnalyze: (symbol: string) => void;
}) {
  return (
    <tr className="border-b border-gray-800/70 hover:bg-gray-800/30 transition-colors">
      <td className={`${TD} font-bold sticky left-0 bg-gray-950 z-10`}>
        <button
          type="button"
          onClick={() => onAnalyze(row.symbol)}
          className="text-indigo-400 hover:text-indigo-200 transition-colors"
          title="Open analysis for this stock"
        >
          {row.symbol}
        </button>
      </td>
      <td className={`${TD} text-gray-300 max-w-[160px] truncate`} title={row.company_name ?? ""}>
        {row.company_name ?? "--"}
      </td>
      <td className={`${TD} text-gray-500 max-w-[140px] truncate`} title={row.industry ?? ""}>
        {row.industry ?? "--"}
      </td>
      <td className={`${TD} font-mono text-gray-400`}>{fmtPrice(row.pre_market)}</td>
      <td className={`${TD} font-mono text-gray-300`}>{fmtPrice(row.open_price)}</td>
      <td className={`${TD} font-mono font-semibold text-white`}>{fmtPrice(row.close_price)}</td>
      <td className={`${TD} font-mono text-gray-400`}>{fmtPrice(row.post_market)}</td>
      <td className={`${TD}`}>
        <ScoreBar score={row.momentum_score} />
      </td>
      <td className={`${TD} font-mono font-semibold ${pctColor(row.day_change_pct)}`}>
        {fmtPct(row.day_change_pct)}
      </td>
    </tr>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

interface MomentumGridProps {
  onAnalyze?: (symbol: string) => void;
}

export function MomentumGrid({ onAnalyze }: MomentumGridProps) {
  const { data, isLoading, error, countdown, refresh } = useMomentumSectors(10);
  const [activeSector, setActiveSector] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("momentum_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const sectors = data?.sectors ?? [];
  const currentSector = activeSector ?? sectors[0]?.sector ?? null;
  const sectorData = sectors.find((s) => s.sector === currentSector);
  const rows = sortRows(sectorData?.stocks ?? [], sortKey, sortDir);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(NUMERIC_COLS.includes(key) ? "desc" : "asc");
    }
  }

  function handleAnalyze(symbol: string) {
    if (onAnalyze) onAnalyze(symbol);
  }

  const fetchedAt = data?.fetched_at_utc
    ? new Date(data.fetched_at_utc).toLocaleTimeString()
    : null;

  return (
    <div className="space-y-4">
      {/* ── Header bar ── */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-base font-semibold text-gray-100">Momentum Sectors</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Top momentum stocks per GICS sector — score = 52W position + SMA signals + day change. Not investment advice.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {isLoading && !data ? (
            <span className="flex items-center gap-1.5 text-indigo-400">
              <span className="inline-block w-3 h-3 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
              Scanning all sectors in background…
            </span>
          ) : (
            <>
              {fetchedAt && <span>Updated {fetchedAt}</span>}
              <span className={countdown <= 30 ? "text-amber-500" : ""}>
                Next in {countdown}s
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

      {/* ── Sector tabs — skeleton while loading ── */}
      {isLoading && !data ? (
        <SkeletonTabs />
      ) : (
        sectors.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {sectors.map((s) => (
              <button
                key={s.sector}
                type="button"
                onClick={() => setActiveSector(s.sector)}
                className={[
                  "px-3 py-1 text-xs rounded-full border transition-colors",
                  s.sector === currentSector
                    ? "bg-indigo-600 border-indigo-500 text-white"
                    : "bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600",
                ].join(" ")}
              >
                {s.sector}
              </button>
            ))}
          </div>
        )
      )}

      {/* ── Table — skeleton rows while loading ── */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-900 border-b border-gray-700">
              <tr>
                {COLUMNS.map((col) => (
                  <Th
                    key={col.key}
                    col={col}
                    sortKey={sortKey}
                    sortDir={sortDir}
                    onSort={handleSort}
                  />
                ))}
              </tr>
            </thead>
            <tbody className="bg-gray-950 divide-y divide-gray-800/50">
              {isLoading && !data ? (
                Array.from({ length: 10 }).map((_, i) => <SkeletonRow key={i} />)
              ) : rows.length === 0 && !error ? (
                <tr>
                  <td colSpan={COLUMNS.length} className="px-3 py-10 text-center text-xs text-gray-600">
                    No data for this sector.
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <StockRow key={row.symbol} row={row} onAnalyze={handleAnalyze} />
                ))
              )}
            </tbody>
          </table>
        </div>
        {isLoading && data && <div className="h-0.5 bg-indigo-600/70 animate-pulse" />}
      </div>

      <p className="text-xs text-gray-700 italic">
        Data via yfinance · Score 0–100: 52-week range (40 pts) + SMA50 (20 pts) + SMA200 (20 pts) + day change (20 pts) · Click symbol to analyze
      </p>
    </div>
  );
}
