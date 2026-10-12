"use client";

import { useState } from "react";

import { useMarketGridWs, type LivePriceUpdate } from "@/hooks/useMarketGridWs";
import { useValueSectors } from "@/hooks/useValueSectors";
import type { ValueStockRow } from "@/types/api";

// ── Skeleton loading ──────────────────────────────────────────────────────────

// All Sectors: #, Symbol, Score, Company, Sector, Industry, Mkt Cap, Price, P/E, Fwd P/E, P/B, PEG, FCF Yld, Div Yld, ROE, D/E, Day%
const SKELETON_ALL    = ["w-6","w-12","w-20","w-28","w-20","w-20","w-14","w-14","w-12","w-12","w-12","w-10","w-12","w-12","w-10","w-12","w-12"];
// Per-sector:   #, Symbol, Score, Company, Industry, Mkt Cap, Price, P/E, Fwd P/E, P/B, PEG, FCF Yld, Div Yld, ROE, D/E, Day%
const SKELETON_SECTOR = ["w-6","w-12","w-20","w-28","w-20","w-14","w-14","w-12","w-12","w-12","w-10","w-12","w-12","w-10","w-12","w-12"];

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

function fmtPctPlain(v: number | null): string {
  if (v == null) return "--";
  return v.toFixed(2) + "%";
}

function fmtRatio(v: number | null): string {
  if (v == null) return "--";
  return v.toFixed(2);
}

function fmtMarketCap(v: number | null): string {
  if (v == null) return "--";
  if (v >= 1e12) return "$" + (v / 1e12).toFixed(1) + "T";
  if (v >= 1e9)  return "$" + (v / 1e9).toFixed(1) + "B";
  if (v >= 1e6)  return "$" + (v / 1e6).toFixed(0) + "M";
  return "$" + v.toLocaleString();
}

function pctColor(v: number | null): string {
  if (v == null) return "text-gray-500";
  return v > 0 ? "text-green-400" : v < 0 ? "text-red-400" : "text-gray-400";
}

// ── Live price cell (flashes green/red on WS tick) ───────────────────────────

function LivePriceCell({ live, fallback }: { live: LivePriceUpdate | null; fallback: number | null }) {
  return (
    <span className="font-mono font-semibold text-white">
      {fmtPrice(live?.price ?? fallback)}
    </span>
  );
}

// ── Score bar ─────────────────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-600 text-xs">--</span>;
  const pct = Math.max(0, Math.min(100, score));
  const color = pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";
  const label = pct >= 70 ? "text-green-300" : pct >= 40 ? "text-amber-300" : "text-red-300";
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-mono font-semibold w-8 text-right shrink-0 ${label}`}>
        {pct.toFixed(0)}
      </span>
    </div>
  );
}

// ── Quality badges (ROE / Debt-Equity) ───────────────────────────────────────

function RoeBadge({ roe }: { roe: number | null }) {
  if (roe == null) return <span className="text-gray-600 text-xs">--</span>;
  let cls: string;
  let hint: string;
  if (roe > 15)       { cls = "bg-green-900/60 text-green-300 border-green-700/50"; hint = "Strong profitability"; }
  else if (roe > 8)   { cls = "bg-amber-900/60 text-amber-300 border-amber-700/50"; hint = "Moderate profitability"; }
  else if (roe > 0)   { cls = "bg-gray-800 text-gray-400 border-gray-600";          hint = "Weak profitability"; }
  else                { cls = "bg-red-900/60 text-red-300 border-red-700/50";       hint = "Unprofitable"; }
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${cls}`} title={hint}>
      {roe.toFixed(1)}%
    </span>
  );
}

function DebtBadge({ de }: { de: number | null }) {
  if (de == null) return <span className="text-gray-600 text-xs">--</span>;
  let cls: string;
  let hint: string;
  if (de < 50)        { cls = "bg-green-900/60 text-green-300 border-green-700/50"; hint = "Conservatively financed"; }
  else if (de < 100)  { cls = "bg-amber-900/60 text-amber-300 border-amber-700/50"; hint = "Moderate leverage"; }
  else if (de < 200)  { cls = "bg-gray-800 text-gray-400 border-gray-600";          hint = "Leveraged"; }
  else                { cls = "bg-red-900/60 text-red-300 border-red-700/50";       hint = "Overleveraged"; }
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${cls}`} title={hint}>
      {de.toFixed(0)}%
    </span>
  );
}

// ── Sort helpers ──────────────────────────────────────────────────────────────

type SortKey = keyof ValueStockRow | "__rank__";
type SortDir = "asc" | "desc";

const NUMERIC_STOCK_COLS: (keyof ValueStockRow)[] = [
  "close_price", "value_score", "day_change_pct", "week_52_high", "week_52_low", "market_cap",
  "pe_ratio", "forward_pe", "price_to_book", "peg_ratio",
  "fcf_yield_pct", "dividend_yield_pct", "return_on_equity_pct", "debt_to_equity_pct",
];

// "Lower is cheaper" ratios — ascending sort reads better-to-worse by default.
const LOWER_IS_BETTER_COLS: (keyof ValueStockRow)[] = ["pe_ratio", "forward_pe", "price_to_book", "peg_ratio", "debt_to_equity_pct"];

function getValue(row: ValueStockRow, key: keyof ValueStockRow): string | number {
  const v = row[key];
  if (v == null) return NUMERIC_STOCK_COLS.includes(key) ? -Infinity : "";
  return v as string | number;
}

// ── Column definitions ────────────────────────────────────────────────────────

interface ColDef {
  key: SortKey;
  label: string;
  title: string;
  sticky?: boolean;
  numeric?: boolean;
  w: number; // fixed column width in px for table-layout:fixed
}

const RANK_COL: ColDef = {
  key: "__rank__", label: "#", numeric: true, w: 32,
  title: "Rank by composite value score (1 = cheapest relative to quality)",
};

const BASE_COLS: ColDef[] = [
  { key: "symbol",      label: "Symbol",  sticky: true, w: 68,  title: "Click to run AI analysis on this stock" },
  { key: "value_score", label: "Score",   numeric: true, w: 100,
    title: "Composite score 0–100. Combines earnings yield, book yield, FCF yield, PEG, and dividend yield percentile ranks against the other 110 stocks in our universe, plus an ROE/Debt-Equity quality overlay." },
  { key: "company_name", label: "Company", w: 140, title: "Company name" },
];

const SECTOR_COL: ColDef = {
  key: "sector", label: "Sector", w: 105,
  title: "GICS sector — tells you which part of the economy this company operates in",
};

const DETAIL_COLS: ColDef[] = [
  { key: "industry",              label: "Industry", w: 110, title: "Industry sub-group within the sector" },
  { key: "market_cap",            label: "Mkt Cap",  numeric: true, w: 72, title: "Market capitalisation — total market value of all outstanding shares" },
  { key: "close_price",           label: "Price",    numeric: true, w: 68, title: "Latest closing price (USD)" },
  { key: "pe_ratio",              label: "P/E",       numeric: true, w: 56,
    title: "Trailing price-to-earnings ratio. Lower generally means cheaper relative to current profits." },
  { key: "forward_pe",            label: "Fwd P/E",   numeric: true, w: 62, title: "Forward P/E — priced against next year's expected earnings" },
  { key: "price_to_book",         label: "P/B",       numeric: true, w: 56, title: "Price-to-book — price relative to net asset (book) value" },
  { key: "peg_ratio",             label: "PEG",       numeric: true, w: 56,
    title: "P/E divided by expected earnings growth. Below ~1.5 suggests the stock isn't overpaying for its growth." },
  { key: "fcf_yield_pct",         label: "FCF Yld",   numeric: true, w: 64, title: "Free cash flow ÷ market cap. Higher means more cash generated per dollar invested." },
  { key: "dividend_yield_pct",    label: "Div Yld",   numeric: true, w: 62, title: "Trailing dividend yield" },
  { key: "return_on_equity_pct",  label: "ROE",       numeric: true, w: 56,
    title: "Return on equity — profitability relative to shareholder equity. >15% is strong." },
  { key: "debt_to_equity_pct",    label: "D/E",       numeric: true, w: 56,
    title: "Debt-to-equity ratio. <50% is conservatively financed; >200% is overleveraged." },
  { key: "day_change_pct",        label: "Today",     numeric: true, w: 62, title: "Today's price change %" },
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
      style={{ width: col.w }}
      className={[
        "px-2 py-2 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap",
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

const TD = "px-2 py-1.5 text-xs whitespace-nowrap";

const RANK_COLORS: Record<number, string> = {
  1: "text-yellow-400 font-bold",
  2: "text-gray-300 font-bold",
  3: "text-amber-600 font-bold",
};

function StockRow({ row, rank, showSector, onAnalyze, liveInfo }: {
  row: ValueStockRow; rank: number; showSector: boolean; onAnalyze: (s: string) => void;
  liveInfo?: LivePriceUpdate | null;
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
        <ScoreBar score={row.value_score} />
      </td>
      {/* Company */}
      <td className={TD} title={row.company_name ?? ""}>
        <div className="text-gray-300 truncate" style={{ maxWidth: 140 }}>{row.company_name ?? "--"}</div>
      </td>
      {/* Sector (All Sectors only) */}
      {showSector && (
        <td className={TD} title={row.sector ?? ""}>
          <div className="text-gray-400 truncate" style={{ maxWidth: 110 }}>{row.sector ?? "--"}</div>
        </td>
      )}
      {/* Industry */}
      <td className={TD} title={row.industry ?? ""}>
        <div className="text-gray-500 truncate" style={{ maxWidth: 120 }}>{row.industry ?? "--"}</div>
      </td>
      {/* Market Cap */}
      <td className={`${TD} font-mono text-gray-300`}>{fmtMarketCap(row.market_cap)}</td>
      {/* Price — live WS tick if connected, falls back to close_price */}
      <td className={`${TD}`}>
        <span className="flex items-center gap-1">
          <LivePriceCell live={liveInfo ?? null} fallback={row.close_price} />
          {liveInfo && (
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" title="Live" />
          )}
        </span>
      </td>
      {/* Valuation ratios */}
      <td className={`${TD} font-mono text-gray-300`}>{fmtRatio(row.pe_ratio)}</td>
      <td className={`${TD} font-mono text-gray-400`}>{fmtRatio(row.forward_pe)}</td>
      <td className={`${TD} font-mono text-gray-300`}>{fmtRatio(row.price_to_book)}</td>
      <td className={`${TD} font-mono text-gray-400`}>{fmtRatio(row.peg_ratio)}</td>
      {/* Yields */}
      <td className={`${TD} font-mono font-semibold ${pctColor(row.fcf_yield_pct)}`}>{fmtPctPlain(row.fcf_yield_pct)}</td>
      <td className={`${TD} font-mono font-semibold ${pctColor(row.dividend_yield_pct)}`}>{fmtPctPlain(row.dividend_yield_pct)}</td>
      {/* Quality badges */}
      <td className={TD}><RoeBadge roe={row.return_on_equity_pct} /></td>
      <td className={TD}><DebtBadge de={row.debt_to_equity_pct} /></td>
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
              ? "What am I looking at? — All Sectors (Top 5 per sector+industry)"
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
                <span className="text-gray-200 font-medium">All Sectors</span> shows the{" "}
                <span className="text-indigo-300 font-medium">top 5 cheapest stocks per sector+industry combination</span>{" "}
                — so every industry gets fair representation, not just the sector with the lowest overall valuations.
              </p>
              <p>
                Every stock is scored 0–100 by comparing its earnings yield, book yield, FCF yield, PEG,
                and dividend yield against all other stocks in our universe — not against a fixed target.
                A score of 80 means this stock is cheaper (and about as financially sound) than roughly
                80% of all 110 stocks. This is called{" "}
                <span className="text-gray-300">cross-sectional ranking</span> — the same approach the{" "}
                <span className="text-gray-300">Momentum</span> page uses, so the two scores are directly comparable.
                Use the <span className="text-gray-300">Sector</span> and{" "}
                <span className="text-gray-300">Industry</span> filters above the table to drill down.
              </p>
            </>
          ) : (
            <p>
              <span className="text-gray-200 font-medium">Single Sector</span> shows the top 10
              value stocks within the selected GICS sector, ranked the same way — by how each
              stock&apos;s valuation and quality metrics compare against the full 110-stock universe.
            </p>
          )}

          <div className="grid grid-cols-1 gap-2 mt-2">
            <p className="text-gray-300 font-medium">Column guide:</p>
            <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
              <div><span className="text-indigo-300 font-mono">#</span> — Rank by value score (1 = cheapest relative to quality)</div>
              <div><span className="text-indigo-300 font-mono">Score</span> — Composite 0–100: how cheap + financially sound this stock is vs. all 110 peers</div>
              <div><span className="text-indigo-300 font-mono">P/E</span> &amp; <span className="text-indigo-300 font-mono">Fwd P/E</span> — price vs. current/expected earnings; lower is cheaper</div>
              <div><span className="text-indigo-300 font-mono">P/B</span> — price vs. book (net asset) value; lower is cheaper</div>
              <div><span className="text-indigo-300 font-mono">PEG</span> — P/E adjusted for growth; below ~1.5 avoids overpaying for growth</div>
              <div><span className="text-indigo-300 font-mono">FCF Yld</span> — free cash flow ÷ market cap; higher is better</div>
              <div><span className="text-indigo-300 font-mono">Div Yld</span> — trailing dividend yield; higher adds shareholder return</div>
              <div>
                <span className="text-indigo-300 font-mono">ROE</span> / <span className="text-indigo-300 font-mono">D/E</span> — quality overlay:{" "}
                <span className="text-green-400">high ROE + low debt = sound business</span>,{" "}
                <span className="text-red-400">weak ROE + high debt = possible value trap</span>
              </div>
              <div><span className="text-indigo-300 font-mono">Today</span> — Price change % today</div>
            </div>
          </div>

          <p className="text-gray-600 italic border-t border-gray-800 pt-2">
            Score formula: earnings-yield rank (26 pts) + book-yield rank (20 pts) + FCF-yield rank (19 pts) +
            PEG rank (10 pts) + dividend-yield rank (10 pts) + ROE/Debt-Equity quality overlay (15 pts) −
            penalty if Debt/Equity is extreme. Not investment advice.
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

interface ValueGridProps {
  onAnalyze?: (symbol: string) => void;
}

export function ValueGrid({ onAnalyze }: ValueGridProps) {
  const { data, isLoading, isRefreshing, error, countdown, refresh } = useValueSectors(20);
  const [activeSector, setActiveSector] = useState<string>(ALL_SECTORS_KEY);
  const [sortKey, setSortKey] = useState<SortKey>("__rank__");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [filterSector, setFilterSector] = useState<string>("");
  const [filterIndustry, setFilterIndustry] = useState<string>("");

  const sectors = data?.sectors ?? [];
  const isAllSectors = activeSector === ALL_SECTORS_KEY;
  // Inherit sector name from parent group when the stock's own field is null
  const allStocksFlat = sectors.flatMap((s) =>
    s.stocks.map((stock) => ({ ...stock, sector: stock.sector ?? s.sector }))
  );

  // Live WebSocket prices — subscribe to all symbols in the value universe
  const allSymbols = Array.from(new Set(allStocksFlat.map((r) => r.symbol)));
  const { livePrices, connected: wsConnected } = useMarketGridWs(allSymbols);

  // All-sectors: top 5 per sector+industry combination, then sorted by score globally
  const allSectorsByIndustry = (() => {
    const groups = new Map<string, ValueStockRow[]>();
    for (const stock of allStocksFlat) {
      const key = `${stock.sector ?? ""}||${stock.industry ?? ""}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(stock);
    }
    return Array.from(groups.values())
      .flatMap((stocks) =>
        [...stocks]
          .sort((a, b) => (b.value_score ?? -1) - (a.value_score ?? -1))
          .slice(0, 5)
      )
      .sort((a, b) => (b.value_score ?? -1) - (a.value_score ?? -1));
  })();

  const sectorData = sectors.find((s) => s.sector === activeSector);

  // Filter options derived from all available data
  const uniqueSectors = Array.from(new Set(allStocksFlat.map((r) => r.sector).filter(Boolean) as string[])).sort();
  const uniqueIndustries = Array.from(new Set(
    allStocksFlat
      .filter((r) => !filterSector || r.sector === filterSector)
      .map((r) => r.industry)
      .filter(Boolean) as string[]
  )).sort();

  // Base rows: apply sector+industry filters
  const unfilteredRows = isAllSectors ? allSectorsByIndustry : (sectorData?.stocks ?? []);
  const baseRows = unfilteredRows.filter((r) => {
    if (filterSector && r.sector !== filterSector) return false;
    if (filterIndustry && r.industry !== filterIndustry) return false;
    return true;
  });

  // Preserve original rank position across re-sorts
  const rankedRows = baseRows.map((row, i) => ({ row, rank: i + 1 }));
  const sortedPairs = sortKey === "__rank__"
    ? (sortDir === "asc" ? rankedRows : [...rankedRows].reverse())
    : [...rankedRows].sort((a, b) => {
        const av = getValue(a.row, sortKey as keyof ValueStockRow);
        const bv = getValue(b.row, sortKey as keyof ValueStockRow);
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
      const isNum = key === "__rank__" || NUMERIC_STOCK_COLS.includes(key as keyof ValueStockRow);
      // Ratio columns where lower is cheaper default to ascending (cheapest first);
      // everything else (yields, score) defaults to descending (best first).
      const defaultsAsc = key === "__rank__" || LOWER_IS_BETTER_COLS.includes(key as keyof ValueStockRow);
      setSortDir(isNum ? (defaultsAsc ? "asc" : "desc") : "asc");
    }
  }

  const fetchedAt = data?.fetched_at_utc
    ? new Date(data.fetched_at_utc).toLocaleTimeString()
    : null;

  // Unique sectors represented in the All Sectors view
  const representedSectors = allSectorsByIndustry
    .map((r) => r.sector)
    .filter((s, i, arr): s is string => s != null && arr.indexOf(s) === i);

  return (
    <>
    <div className="space-y-4">
      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-100">Value Sectors</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {isAllSectors
              ? `Top 5 per sector+industry — ${allSectorsByIndustry.length} stocks across all 11 GICS sectors`
              : `Top 10 value stocks in the ${activeSector} sector`}
          </p>
          {/* Metadata row: updated time + countdown */}
          <div className="flex items-center gap-3 mt-1 text-xs text-gray-600">
            {isLoading && !data ? (
              <span className="flex items-center gap-1.5 text-indigo-400">
                <span className="inline-block w-3 h-3 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
                Scanning all sectors…
              </span>
            ) : (
              <>
                {isRefreshing ? (
                  <span className="flex items-center gap-1.5 text-indigo-400">
                    <span className="inline-block w-3 h-3 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
                    Refreshing…
                  </span>
                ) : (
                  fetchedAt && <span>Updated {fetchedAt}</span>
                )}
                <span className={countdown <= 30 ? "text-amber-500" : ""}>
                  Refreshes in {countdown}s
                </span>
                <span
                  className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] border ${
                    wsConnected
                      ? "text-emerald-400 border-emerald-800/50 bg-emerald-950/30"
                      : "text-gray-600 border-gray-800"
                  }`}
                  title={wsConnected ? "Live price feed connected" : "Live feed offline"}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? "bg-emerald-400 animate-pulse" : "bg-gray-700"}`} />
                  {wsConnected ? "Live" : "Offline"}
                </span>
              </>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={() => refresh()}
          disabled={isLoading || isRefreshing}
          className="shrink-0 px-3 py-1.5 bg-indigo-700 hover:bg-indigo-600 text-white text-xs rounded border border-indigo-500 transition-colors disabled:opacity-40"
        >
          {isLoading || isRefreshing ? "Loading…" : "↻ Refresh"}
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
          {error instanceof Error ? error.message : "Failed to load value data."}
        </p>
      )}

      {/* ── Sector tabs ── */}
      {isLoading && !data ? (
        <SkeletonTabs />
      ) : sectors.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => { setActiveSector(ALL_SECTORS_KEY); setSortKey("__rank__"); setSortDir("asc"); setFilterSector(""); setFilterIndustry(""); }}
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
              onClick={() => { setActiveSector(s.sector); setSortKey("__rank__"); setSortDir("asc"); setFilterSector(""); setFilterIndustry(""); }}
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
            const count = allSectorsByIndustry.filter((r) => r.sector === s).length;
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

      {/* ── Filters ── */}
      {!isLoading && allStocksFlat.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-500">Filter:</span>
          {isAllSectors && (
            <select
              value={filterSector}
              onChange={(e) => { setFilterSector(e.target.value); setFilterIndustry(""); }}
              className="text-xs bg-gray-800 border border-gray-700 text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="">All Sectors</option>
              {uniqueSectors.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          )}
          <select
            value={filterIndustry}
            onChange={(e) => setFilterIndustry(e.target.value)}
            className="text-xs bg-gray-800 border border-gray-700 text-gray-300 rounded px-2 py-1.5 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="">All Industries</option>
            {uniqueIndustries.map((i) => <option key={i} value={i}>{i}</option>)}
          </select>
          {(filterSector || filterIndustry) && (
            <>
              <button
                type="button"
                onClick={() => { setFilterSector(""); setFilterIndustry(""); }}
                className="text-xs text-gray-500 hover:text-gray-200 px-2 py-1 rounded border border-gray-700 hover:border-gray-500 transition-colors"
              >
                ✕ Clear
              </button>
              <span className="text-xs text-gray-600">
                {baseRows.length} stock{baseRows.length !== 1 ? "s" : ""}
              </span>
            </>
          )}
        </div>
      )}

    </div>{/* end space-y-4 */}

    {/* ── Table ── */}
    <div className="mt-4 rounded-lg border border-gray-800 overflow-hidden">
        {isRefreshing && (
          <div className="flex items-center gap-2.5 px-3 py-2 bg-indigo-950/70 border-b border-indigo-800/40">
            <span className="inline-block w-3.5 h-3.5 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin flex-shrink-0" />
            <span className="text-xs text-indigo-300 font-medium">Refreshing fundamentals — valuations and rankings updating…</span>
            <div className="flex-1 h-1 bg-indigo-900/60 rounded-full overflow-hidden">
              <div className="h-full w-2/5 bg-indigo-400/80 rounded-full animate-pulse" />
            </div>
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="text-left min-w-[1250px] w-max">
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
                    liveInfo={livePrices[row.symbol]}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
