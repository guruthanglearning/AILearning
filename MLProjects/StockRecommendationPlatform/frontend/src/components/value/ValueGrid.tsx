"use client";

import { useId, useLayoutEffect, useRef, useState } from "react";

import { useMarketGridWs, type LivePriceUpdate } from "@/hooks/useMarketGridWs";
import { useValueSectors } from "@/hooks/useValueSectors";
import type { ValueStockRow } from "@/types/api";

// ── Skeleton loading ──────────────────────────────────────────────────────────
// Widths are derived from getColumns() (defined below) so the skeleton always
// matches the real column count — no separate list to keep in sync by hand.

function SkeletonRow({ showSector }: { showSector: boolean }) {
  const columns = getColumns(showSector);
  return (
    <tr className="border-b border-gray-800/70">
      {columns.map((col) => (
        <td key={String(col.key)} className="px-3 py-3">
          <div className="h-2.5 bg-gray-800 rounded animate-pulse" style={{ width: Math.max(16, col.w - 20) }} />
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

// ── Data hygiene: "n/m" (not meaningful) ─────────────────────────────────────
// Ratios that are negative (losses / negative equity) or absurdly large (earnings
// near zero, cyclical troughs) aren't comparable — professional screeners show
// them as "n/m" rather than as a raw number, and exclude them from sorting.

const MEANINGFUL_MAX: Partial<Record<keyof ValueStockRow, number>> = {
  pe_ratio: 100,
  forward_pe: 100,
  price_to_book: 50,
  price_to_sales: 50,
  ev_to_ebitda: 100,
  peg_ratio: 5,
  fcf_to_net_income: 5,
};

function nmReason(key: keyof ValueStockRow, v: number | null): string | null {
  const max = MEANINGFUL_MAX[key];
  if (v == null || max == null) return null;
  if (v < 0) {
    return key === "price_to_book"
      ? `Negative book value (${v.toFixed(2)}) — shareholder equity is below zero, often from buybacks; not comparable`
      : key === "fcf_to_net_income"
        ? `Negative free cash flow (${v.toFixed(2)}x) — not comparable`
        : `Negative (${v.toFixed(2)}) — earnings or growth are negative; not comparable`;
  }
  if (v > max) {
    return `Extreme value (${v.toFixed(2)}, above ${max}) — usually earnings near zero or a cyclical trough; not comparable`;
  }
  return null;
}

function NotMeaningful({ reason }: { reason: string }) {
  return (
    <span className="text-gray-500 italic cursor-help border-b border-dotted border-gray-600" title={reason}>
      n/m
    </span>
  );
}

function RatioCell({ row, field, className }: { row: ValueStockRow; field: keyof ValueStockRow; className: string }) {
  const v = row[field] as number | null;
  const reason = nmReason(field, v);
  return (
    <td className={`${TD} font-mono ${className}`}>
      {reason ? <NotMeaningful reason={reason} /> : fmtRatio(v)}
    </td>
  );
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

// Stacked bar: cheapness (indigo, out of 85) + quality (emerald, out of 15), so
// the reader sees WHY a stock scored what it did, not just the blended number.
// Hover shows the exact parts, including any balance-sheet penalty.

function ScoreBar({ row }: { row: ValueStockRow }) {
  const score = row.value_score;
  if (score == null) return <span className="text-gray-600 text-xs">--</span>;
  const pct = Math.max(0, Math.min(100, score));
  const label = pct >= 70 ? "text-green-300" : pct >= 40 ? "text-amber-300" : "text-red-300";
  const cheap = row.score_cheapness_pts;
  const quality = row.score_quality_pts;
  const penalty = row.score_penalty_pts ?? 0;
  const hasParts = cheap != null && quality != null;
  return (
    <div className="group relative flex items-center gap-2 min-w-[80px] cursor-help">
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden flex">
        {hasParts ? (
          <>
            <div className="h-full bg-indigo-500" style={{ width: `${Math.max(0, cheap)}%` }} />
            <div className="h-full bg-emerald-400" style={{ width: `${Math.max(0, quality)}%` }} />
          </>
        ) : (
          <div className="h-full bg-indigo-500" style={{ width: `${pct}%` }} />
        )}
      </div>
      <span className={`text-xs font-mono font-semibold w-8 text-right shrink-0 ${label}`}>
        {pct.toFixed(0)}
        {penalty < 0 && <span className="text-red-400" aria-label="penalised">*</span>}
      </span>
      {hasParts && (
        <div
          role="tooltip"
          className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-2 z-30 hidden group-hover:block w-52 rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-[11px] shadow-xl"
        >
          <div className="flex justify-between text-gray-300">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-indigo-500" />Cheapness</span>
            <span className="font-mono">{cheap.toFixed(1)} / 85</span>
          </div>
          <div className="flex justify-between text-gray-300 mt-1">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm bg-emerald-400" />Quality</span>
            <span className="font-mono">{quality.toFixed(0)} / 15</span>
          </div>
          {penalty < 0 && (
            <div className="flex justify-between text-red-300 mt-1">
              <span>Debt/Equity penalty</span>
              <span className="font-mono">{penalty.toFixed(0)}</span>
            </div>
          )}
          <div className="flex justify-between text-gray-100 font-semibold border-t border-gray-700 mt-1.5 pt-1.5">
            <span>Score</span>
            <span className="font-mono">{pct.toFixed(1)}</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Trend badge (value + momentum falling-knife guard) ──────────────────────

const TREND_STYLE = {
  up:    { cls: "bg-green-900/50 text-green-300 border-green-700/50", label: "▲ Up" },
  mixed: { cls: "bg-gray-800 text-gray-300 border-gray-600",          label: "◆ Mixed" },
  down:  { cls: "bg-red-900/50 text-red-300 border-red-700/50",       label: "▼ Down" },
} as const;

function TrendBadge({ row }: { row: ValueStockRow }) {
  const t = row.trend_signal;
  if (t == null) return <span className="text-gray-600 text-xs">--</span>;
  const parts: string[] = [];
  if (row.return_6m_pct != null) parts.push(`6-month return ${fmtPct(row.return_6m_pct)}`);
  if (row.above_sma200 != null) parts.push(`price ${row.above_sma200 ? "above" : "below"} its 200-day average`);
  const verdict = t === "down"
    ? "Still falling — possible value trap (\"falling knife\")"
    : t === "up" ? "Cheap and already trending up" : "Trend signals disagree";
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded border whitespace-nowrap ${TREND_STYLE[t].cls}`} title={`${verdict}: ${parts.join(", ")}`}>
      {TREND_STYLE[t].label}
    </span>
  );
}

// ── Piotroski F-score (financial strength, year over year) ──────────────────

// "Strong" = 7+ of 9 tests, or the same share of the tests that could be
// evaluated (e.g. 4/4 for a bank, which skips the 5 tests that don't apply).
const F_STRONG_RATIO = 7 / 9;
const F_WEAK_RATIO = 2 / 9;

function fScoreRatio(r: ValueStockRow): number | null {
  return r.piotroski_score != null && r.piotroski_max ? r.piotroski_score / r.piotroski_max : null;
}

function passesFScore(r: ValueStockRow): boolean {
  const ratio = fScoreRatio(r);
  return ratio != null && ratio >= F_STRONG_RATIO - 1e-9;
}

function FScoreCell({ row }: { row: ValueStockRow }) {
  // Fixed-position panel: the table sits in an overflow-x-auto container that
  // would otherwise clip a 9-line tooltip on the top and bottom rows.
  const [anchor, setAnchor] = useState<DOMRect | null>(null);
  const [top, setTop] = useState<number | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const tooltipId = useId();
  // Place the panel once its real height is known: beside the cell, shifted up
  // just enough to stay inside the viewport.
  useLayoutEffect(() => {
    if (!anchor || !panelRef.current) {
      setTop(null);
      return;
    }
    const h = panelRef.current.offsetHeight;
    setTop(Math.max(8, Math.min(anchor.top - 120, window.innerHeight - h - 8)));
  }, [anchor]);
  const ratio = fScoreRatio(row);
  if (ratio == null) {
    const why = row.piotroski_tests.length
      ? "Too few of the 9 tests could be evaluated from the reported statements"
      : "Annual statements unavailable from the data feed";
    return <span className="text-gray-600 text-xs" title={why}>--</span>;
  }
  const cls = ratio >= F_STRONG_RATIO - 1e-9
    ? "bg-green-900/60 text-green-300 border-green-700/50"
    : ratio <= F_WEAK_RATIO + 1e-9
      ? "bg-red-900/60 text-red-300 border-red-700/50"
      : "bg-amber-900/60 text-amber-300 border-amber-700/50";
  const show = (el: HTMLElement) => setAnchor(el.getBoundingClientRect());
  const hide = () => setAnchor(null);
  return (
    <>
      <button
        type="button"
        onMouseEnter={(e) => show(e.currentTarget)}
        onMouseLeave={hide}
        onFocus={(e) => show(e.currentTarget)}
        onBlur={hide}
        onKeyDown={(e) => { if (e.key === "Escape") hide(); }}
        aria-label={`Piotroski F-score ${row.piotroski_score} of ${row.piotroski_max}`}
        aria-describedby={anchor ? tooltipId : undefined}
        className="flex items-center gap-1 cursor-help"
      >
        <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${cls}`}>
          {row.piotroski_score}/{row.piotroski_max}
        </span>
        {row.piotroski_bank_style && <span className="text-[9px] text-gray-500 uppercase">bank</span>}
      </button>
      {anchor && (
        <div
          ref={panelRef}
          id={tooltipId}
          role="tooltip"
          className="pointer-events-none fixed z-50 w-80 whitespace-normal rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-[11px] shadow-xl"
          style={{
            left: Math.min(anchor.right + 8, window.innerWidth - 328),
            top: top ?? anchor.top,
            visibility: top == null ? "hidden" : "visible",
          }}
        >
          <div className="flex justify-between text-gray-100 font-semibold">
            <span>Piotroski F-score</span>
            <span className="font-mono">{row.piotroski_score} / {row.piotroski_max}</span>
          </div>
          <div className="text-gray-500 mb-1.5">
            Fiscal year ending {row.piotroski_fiscal_year ?? "?"} vs the year before
          </div>
          <ul className="space-y-1">
            {row.piotroski_tests.map((t) => (
              <li key={t.id} className="flex gap-1.5">
                <span className={t.passed == null ? "text-gray-600" : t.passed ? "text-green-400" : "text-red-400"}>
                  {t.passed == null ? "–" : t.passed ? "✓" : "✗"}
                </span>
                <span className={t.passed == null ? "text-gray-500" : "text-gray-300"}>
                  {t.label}
                  {t.detail && <span className="block text-gray-500">{t.detail}</span>}
                </span>
              </li>
            ))}
          </ul>
          {row.piotroski_bank_style && (
            <div className="text-gray-500 border-t border-gray-700 mt-1.5 pt-1.5">
              Bank-style balance sheet: scored only on the {row.piotroski_max} tests that apply.
            </div>
          )}
        </div>
      )}
    </>
  );
}

// ── Quality badges (ROA / liquidity / earnings-quality / Debt-Equity) ───────

function RoaBadge({ roa }: { roa: number | null }) {
  if (roa == null) return <span className="text-gray-600 text-xs">--</span>;
  let cls: string;
  let hint: string;
  if (roa > 15)       { cls = "bg-green-900/60 text-green-300 border-green-700/50"; hint = "Strong profitability (ROA, unaffected by leverage/buybacks unlike ROE)"; }
  else if (roa > 8)   { cls = "bg-amber-900/60 text-amber-300 border-amber-700/50"; hint = "Moderate profitability"; }
  else if (roa > 0)   { cls = "bg-gray-800 text-gray-400 border-gray-600";          hint = "Weak profitability"; }
  else                { cls = "bg-red-900/60 text-red-300 border-red-700/50";       hint = "Unprofitable"; }
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${cls}`} title={hint}>
      {roa.toFixed(1)}%
    </span>
  );
}

function CurrentRatioBadge({ cr }: { cr: number | null }) {
  if (cr == null) return <span className="text-gray-600 text-xs">--</span>;
  let cls: string;
  let hint: string;
  if (cr >= 1.5)      { cls = "bg-green-900/60 text-green-300 border-green-700/50"; hint = "Strong short-term liquidity"; }
  else if (cr >= 1.0) { cls = "bg-amber-900/60 text-amber-300 border-amber-700/50"; hint = "Adequate liquidity"; }
  else                { cls = "bg-red-900/60 text-red-300 border-red-700/50";       hint = "Current liabilities exceed current assets"; }
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${cls}`} title={hint}>
      {cr.toFixed(2)}
    </span>
  );
}

function FcfQualityBadge({ ratio }: { ratio: number | null }) {
  if (ratio == null) return <span className="text-gray-600 text-xs">--</span>;
  const reason = nmReason("fcf_to_net_income", ratio);
  if (reason) return <NotMeaningful reason={reason} />;
  let cls: string;
  let hint: string;
  if (ratio >= 1.0)      { cls = "bg-green-900/60 text-green-300 border-green-700/50"; hint = "Reported earnings are fully backed by cash flow"; }
  else if (ratio >= 0.7) { cls = "bg-amber-900/60 text-amber-300 border-amber-700/50"; hint = "Earnings partially backed by cash flow"; }
  else                   { cls = "bg-red-900/60 text-red-300 border-red-700/50";       hint = "Earnings not well backed by cash flow — possible earnings-quality concern"; }
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${cls}`} title={hint}>
      {ratio.toFixed(2)}x
    </span>
  );
}

function DebtBadge({ de }: { de: number | null }) {
  if (de == null) return <span className="text-gray-600 text-xs">--</span>;
  let cls: string;
  let hint: string;
  if (de < 0)         { cls = "bg-red-900/60 text-red-300 border-red-700/50";       hint = "Negative shareholder equity — balance-sheet risk"; }
  else if (de < 50)   { cls = "bg-green-900/60 text-green-300 border-green-700/50"; hint = "Conservatively financed"; }
  else if (de < 100)  { cls = "bg-amber-900/60 text-amber-300 border-amber-700/50"; hint = "Moderate leverage"; }
  else if (de < 200)  { cls = "bg-gray-800 text-gray-400 border-gray-600";          hint = "Leveraged"; }
  else                { cls = "bg-red-900/60 text-red-300 border-red-700/50";       hint = "Overleveraged"; }
  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${cls}`} title={hint}>
      {de.toFixed(0)}%
    </span>
  );
}

function MarginOfSafetyCell({ v }: { v: number | null }) {
  if (v == null) return <span className="text-gray-600 text-xs">--</span>;
  const hint = v >= 0
    ? "Trading below the Graham Number — potential margin of safety"
    : "Trading above the Graham Number — no margin of safety by this measure";
  return (
    <span className={`font-mono font-semibold ${pctColor(v)}`} title={hint}>
      {fmtPct(v)}
    </span>
  );
}

// ── Sort helpers ──────────────────────────────────────────────────────────────

type SortKey = keyof ValueStockRow | "__rank__";
type SortDir = "asc" | "desc";

const NUMERIC_STOCK_COLS: (keyof ValueStockRow)[] = [
  "close_price", "value_score", "day_change_pct", "week_52_high", "week_52_low", "market_cap",
  "pe_ratio", "forward_pe", "price_to_book", "price_to_sales", "ev_to_ebitda", "peg_ratio",
  "fcf_yield_pct", "dividend_yield_pct",
  "return_on_assets_pct", "current_ratio", "fcf_to_net_income", "debt_to_equity_pct",
  "graham_number", "margin_of_safety_pct", "piotroski_score",
];

// "Lower is cheaper" ratios — ascending sort reads better-to-worse by default.
const LOWER_IS_BETTER_COLS: (keyof ValueStockRow)[] = [
  "pe_ratio", "forward_pe", "price_to_book", "price_to_sales", "ev_to_ebitda", "peg_ratio", "debt_to_equity_pct",
];

const TREND_ORDER = { down: 0, mixed: 1, up: 2 } as const;

function getValue(row: ValueStockRow, key: keyof ValueStockRow): string | number {
  if (key === "trend_signal") {
    return row.trend_signal == null ? -Infinity : TREND_ORDER[row.trend_signal];
  }
  // Sort by share of evaluated tests passed, so a bank's 4/4 and an 8/9 compare
  // fairly; on a tie, the score backed by more tests (9/9 over 4/4) ranks first.
  if (key === "piotroski_score") {
    const ratio = fScoreRatio(row);
    return ratio == null ? -Infinity : ratio * 100 + (row.piotroski_max ?? 0) / 100;
  }
  const v = row[key];
  if (v == null) return NUMERIC_STOCK_COLS.includes(key) ? -Infinity : "";
  // "n/m" values sort with the missing ones (always last), not as real numbers.
  if (typeof v === "number" && nmReason(key, v)) return -Infinity;
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
    title: "Relative composite 0–100 = cheapness (indigo, out of 85: EV/EBITDA, book, FCF, sales, PEG and dividend yields ranked against SECTOR peers only) + quality (green, out of 15: ROA, liquidity, earnings quality, Debt-Equity). * = Debt/Equity penalty applied. Hover a score for its breakdown. Not an intrinsic valuation — see Graham # and Margin for that." },
  { key: "trend_signal", label: "Trend",   w: 76,
    title: "Value + momentum guard. Up = 6-month return positive AND price above its 200-day average; Down = both negative (a cheap stock still falling — possible value trap); Mixed = signals disagree." },
  { key: "piotroski_score", label: "F-Score", numeric: true, w: 84,
    title: "Piotroski F-score: 9 pass/fail financial-strength tests comparing the latest fiscal year with the one before (profit, cash flow, rising ROA, cash-backed earnings, falling debt, better liquidity, no new shares, better margin and asset turnover). 7–9 = strong, 0–2 = weak (a likely value trap). Banks are scored only on the tests that apply (e.g. 4/4). Hover for each test. Not part of the Score." },
  { key: "company_name", label: "Company", w: 140, title: "Company name" },
];

const SECTOR_COL: ColDef = {
  key: "sector", label: "Sector", w: 105,
  title: "GICS sector — tells you which part of the economy this company operates in",
};

const DETAIL_COLS: ColDef[] = [
  { key: "industry",              label: "Industry",   w: 110, title: "Industry sub-group within the sector" },
  { key: "market_cap",            label: "Mkt Cap",    numeric: true, w: 70, title: "Market capitalisation — total market value of all outstanding shares" },
  { key: "close_price",           label: "Price",      numeric: true, w: 64, title: "Latest closing price (USD)" },
  { key: "pe_ratio",              label: "P/E",        numeric: true, w: 50,
    title: "Trailing price-to-earnings ratio. Lower generally means cheaper relative to current profits — but ignores debt, unlike EV/EBITDA." },
  { key: "forward_pe",            label: "Fwd P/E",    numeric: true, w: 60, title: "Forward P/E — priced against next year's expected earnings" },
  { key: "price_to_book",         label: "P/B",        numeric: true, w: 50, title: "Price-to-book — price relative to net asset (book) value" },
  { key: "price_to_sales",        label: "P/S",        numeric: true, w: 50,
    title: "Price-to-sales. Stays meaningful when earnings are temporarily depressed, or for sectors (e.g. Financials) where EBITDA-based metrics don't apply." },
  { key: "ev_to_ebitda",          label: "EV/EBITDA",  numeric: true, w: 78,
    title: "Enterprise Value ÷ EBITDA — the primary cheapness factor driving the score. Debt-aware (Greenblatt \"Magic Formula\" style), unlike raw P/E. Blank for sectors like banks where EBITDA isn't meaningful." },
  { key: "peg_ratio",             label: "PEG",        numeric: true, w: 50,
    title: "P/E divided by expected earnings growth. Below ~1.5 suggests the stock isn't overpaying for its growth." },
  { key: "fcf_yield_pct",         label: "FCF Yld",    numeric: true, w: 62,
    title: "Free cash flow ÷ market cap. Higher means more cash generated per dollar paid for the shares. Free cash flow here is after interest, so it's measured against equity value; EV/EBITDA is the debt-aware factor." },
  { key: "dividend_yield_pct",    label: "Div Yld",    numeric: true, w: 60, title: "Trailing dividend yield" },
  { key: "return_on_assets_pct",  label: "ROA",        numeric: true, w: 54,
    title: "Return on assets — profitability without ROE's leverage/buyback distortion (ROE can exceed 100% from buybacks alone). >15% is strong." },
  { key: "current_ratio",         label: "Curr R",     numeric: true, w: 56,
    title: "Current assets ÷ current liabilities — short-term liquidity safety. >=1.5 is strong; <1.0 means current liabilities exceed current assets." },
  { key: "fcf_to_net_income",     label: "FCF/NI",     numeric: true, w: 58,
    title: "Free cash flow ÷ net income — an earnings-quality check. >=1.0 means cash flow fully backs reported profit; well below 1.0 can flag aggressive accounting." },
  { key: "debt_to_equity_pct",    label: "D/E",        numeric: true, w: 54,
    title: "Debt-to-equity ratio. <50% is conservatively financed; >200% is overleveraged; negative means negative shareholder equity." },
  { key: "graham_number",         label: "Graham #",   numeric: true, w: 72,
    title: "Benjamin Graham's quick intrinsic-value estimate: sqrt(22.5 x EPS x Book Value per share). An ABSOLUTE anchor, not a sector-relative rank — not part of the Score. A 1930s heuristic, not a DCF; distorted for REITs and high-leverage financials." },
  { key: "margin_of_safety_pct",  label: "Margin",     numeric: true, w: 64,
    title: "Graham's margin of safety: (Graham Number − price) ÷ Graham Number. Positive = price is that % below the estimated value; negative = price is above it." },
  { key: "day_change_pct",        label: "Today",      numeric: true, w: 58, title: "Today's price change %" },
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
      title={col.title}
      style={{ width: col.w }}
      aria-sort={active ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
      className={[
        "px-0 py-0 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap",
        col.sticky ? "sticky left-0 bg-gray-900 z-10" : "",
      ].join(" ")}
    >
      <button
        type="button"
        onClick={() => onSort(col.key)}
        className={[
          "w-full px-2 py-2 text-left select-none cursor-pointer transition-colors",
          active
            ? "text-indigo-300 bg-gray-800/60"
            : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/30",
        ].join(" ")}
      >
        {col.label}
        <SortArrow active={active} dir={sortDir} />
      </button>
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
        <ScoreBar row={row} />
      </td>
      {/* Trend */}
      <td className={TD}>
        <TrendBadge row={row} />
      </td>
      {/* F-score */}
      <td className={TD}>
        <FScoreCell row={row} />
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
      <RatioCell row={row} field="pe_ratio"       className="text-gray-300" />
      <RatioCell row={row} field="forward_pe"     className="text-gray-400" />
      <RatioCell row={row} field="price_to_book"  className="text-gray-300" />
      <RatioCell row={row} field="price_to_sales" className="text-gray-400" />
      <RatioCell row={row} field="ev_to_ebitda"   className="text-gray-200 font-semibold" />
      <RatioCell row={row} field="peg_ratio"      className="text-gray-400" />
      {/* Yields */}
      <td className={`${TD} font-mono font-semibold ${pctColor(row.fcf_yield_pct)}`}>{fmtPctPlain(row.fcf_yield_pct)}</td>
      <td className={`${TD} font-mono font-semibold ${pctColor(row.dividend_yield_pct)}`}>{fmtPctPlain(row.dividend_yield_pct)}</td>
      {/* Quality badges */}
      <td className={TD}><RoaBadge roa={row.return_on_assets_pct} /></td>
      <td className={TD}><CurrentRatioBadge cr={row.current_ratio} /></td>
      <td className={TD}><FcfQualityBadge ratio={row.fcf_to_net_income} /></td>
      <td className={TD}><DebtBadge de={row.debt_to_equity_pct} /></td>
      {/* Absolute valuation anchor */}
      <td className={`${TD} font-mono text-gray-300`}>{row.graham_number != null ? `$${fmtRatio(row.graham_number)}` : "--"}</td>
      <td className={TD}><MarginOfSafetyCell v={row.margin_of_safety_pct} /></td>
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
                Every stock gets a 0–100 <span className="text-gray-300">relative composite score</span>, built the
                way professional quant value screens do it: EV/EBITDA, book-yield, FCF-yield, sales-yield, PEG, and
                dividend-yield are each ranked against <span className="text-gray-300">this stock&apos;s own GICS
                sector peers only</span> — not the full 110-stock universe — because Energy and Financials trade
                at structurally lower multiples than Tech, and comparing across sectors would just reward being in
                a cheap sector, not being a mispriced stock within one. Those ranks are blended, then an ROA /
                current-ratio / FCF-vs-net-income / Debt-Equity quality overlay adds or subtracts points on top so
                a cheap score isn&apos;t a melting ice cube or an accounting mirage. Because of that overlay, the
                score itself isn&apos;t a pure percentile, and it isn&apos;t on the same scale as the{" "}
                <span className="text-gray-300">Momentum</span> page&apos;s score — don&apos;t compare the two
                numbers directly.
                Use the <span className="text-gray-300">Sector</span> and{" "}
                <span className="text-gray-300">Industry</span> filters above the table to drill down.
              </p>
            </>
          ) : (
            <p>
              <span className="text-gray-200 font-medium">Single Sector</span> shows the top 10
              value stocks within the selected GICS sector, ranked by how each stock&apos;s valuation and
              quality metrics compare against the other stocks in that <span className="text-gray-300">same
              sector</span> (not the full 110-stock universe).
            </p>
          )}

          <div className="grid grid-cols-1 gap-2 mt-2">
            <p className="text-gray-300 font-medium">Column guide:</p>
            <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
              <div><span className="text-indigo-300 font-mono">#</span> — Rank by value score (1 = cheapest relative to quality, within sector)</div>
              <div><span className="text-indigo-300 font-mono">Score</span> — Relative composite 0–100: <span className="text-indigo-300">cheapness</span> (indigo bar, out of 85) + <span className="text-emerald-300">quality</span> (green bar, out of 15); <span className="text-red-400">*</span> = Debt/Equity penalty. Hover for the breakdown</div>
              <div><span className="text-indigo-300 font-mono">Trend</span> — value + momentum guard: <span className="text-green-400">▲ Up</span> = 6-month return positive and price above its 200-day average; <span className="text-red-400">▼ Down</span> = both negative (cheap but still falling — a possible value trap); ◆ Mixed = signals disagree</div>
              <div><span className="text-indigo-300 font-mono">F-Score</span> — Piotroski&apos;s 9 pass/fail financial-strength tests, latest fiscal year vs the year before: profitable, positive cash flow, rising ROA, cash flow above profit, debt not rising, better liquidity, no new shares, better gross margin and asset turnover. <span className="text-green-400">7–9 strong</span>, <span className="text-red-400">0–2 weak (likely value trap)</span>. Tests with missing data aren&apos;t counted; banks are scored only on the tests that apply (e.g. 4/4). Hover for each test</div>
              <div><span className="text-gray-500 italic">n/m</span> — not meaningful: a negative ratio (losses, negative equity) or an extreme one (e.g. P/E above 100, PEG above 5). Hover for why; these sort last</div>
              <div><span className="text-indigo-300 font-mono">P/E</span> &amp; <span className="text-indigo-300 font-mono">Fwd P/E</span> — price vs. current/expected earnings; lower is cheaper, but ignores debt</div>
              <div><span className="text-indigo-300 font-mono">P/B</span> / <span className="text-indigo-300 font-mono">P/S</span> — price vs. book value / revenue; lower is cheaper</div>
              <div><span className="text-indigo-300 font-mono">EV/EBITDA</span> — debt-aware cheapness (Greenblatt &ldquo;Magic Formula&rdquo; style); the score&apos;s primary cheapness factor</div>
              <div><span className="text-indigo-300 font-mono">PEG</span> — P/E adjusted for growth; below ~1.5 avoids overpaying for growth</div>
              <div><span className="text-indigo-300 font-mono">FCF Yld</span> — free cash flow ÷ market cap; higher is better</div>
              <div><span className="text-indigo-300 font-mono">Div Yld</span> — trailing dividend yield; higher adds shareholder return</div>
              <div>
                <span className="text-indigo-300 font-mono">ROA</span> / <span className="text-indigo-300 font-mono">Curr R</span> / <span className="text-indigo-300 font-mono">FCF/NI</span> / <span className="text-indigo-300 font-mono">D/E</span> — quality overlay:{" "}
                <span className="text-green-400">profitable, liquid, cash-backed earnings, low debt = sound business</span>,{" "}
                <span className="text-red-400">the opposite = possible value trap</span>
              </div>
              <div>
                <span className="text-indigo-300 font-mono">Graham #</span> / <span className="text-indigo-300 font-mono">Margin</span> — Benjamin Graham&apos;s absolute intrinsic-value estimate and how far price sits below/above it.{" "}
                <span className="text-gray-500">Not part of the Score — a separate, absolute signal, not a sector-relative rank.</span>
              </div>
              <div><span className="text-indigo-300 font-mono">Today</span> — Price change % today</div>
            </div>
          </div>

          <p className="text-gray-600 italic border-t border-gray-800 pt-2">
            Score formula (sector-relative): EV/EBITDA-yield rank (28 pts) + book-yield rank (15 pts) +
            FCF-yield rank (17 pts) + sales-yield rank (10 pts) + PEG rank (8 pts) + dividend-yield rank (7 pts) +
            ROA/liquidity/earnings-quality/Debt-Equity overlay (15 pts) − 5 pt penalty if Debt/Equity is above
            200% or negative (marked <span className="text-red-400 not-italic">*</span>). The indigo part of the
            score bar is the cheapness points, the green part the quality points.
            Graham Number margin of safety is shown separately and is not part of this score. Neither is the
            Trend signal (6-month return + price vs. 200-day average) — it&apos;s a separate falling-knife check;
            the <span className="text-gray-400 not-italic">Value + Momentum</span> filter keeps only stocks scoring{" "}
            {VALUE_MOMENTUM_MIN_SCORE}+ whose trend isn&apos;t Down. The Piotroski F-score (from the last two
            annual reports) isn&apos;t part of the score either; the{" "}
            <span className="text-gray-400 not-italic">F-Score ≥ 7</span> filter keeps stocks passing at least
            7 of 9 tests, or the same share of the tests that apply. Ratios shown as n/m (negative, or extreme
            such as P/E above 100 or PEG above 5) are excluded from sorting. This still isn&apos;t
            a full DCF or a substitute for reading the business — treat it as a screen for candidates, not a verdict.
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

// "Value + Momentum": cheap AND not still falling — the combination professional
// value screens use to avoid buying a falling knife.
const VALUE_MOMENTUM_MIN_SCORE = 70;

function passesValueMomentum(r: ValueStockRow): boolean {
  return (r.value_score ?? 0) >= VALUE_MOMENTUM_MIN_SCORE && r.trend_signal != null && r.trend_signal !== "down";
}

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
  const [valueMomentumOnly, setValueMomentumOnly] = useState(false);
  const [fStrongOnly, setFStrongOnly] = useState(false);

  const sectors = data?.sectors ?? [];
  const isAllSectors = activeSector === ALL_SECTORS_KEY;
  // Inherit sector name from parent group when the stock's own field is null
  const allStocksFlat = sectors.flatMap((s) =>
    s.stocks.map((stock) => ({ ...stock, sector: stock.sector ?? s.sector }))
  );

  // Live WebSocket prices — subscribe to all symbols in the value universe
  const allSymbols = Array.from(new Set(allStocksFlat.map((r) => r.symbol)));
  const { livePrices, connected: wsConnected } = useMarketGridWs(allSymbols);

  // All-sectors: top 5 per sector+industry combination, then sorted by score globally.
  // Value + Momentum and F-score filters run BEFORE the top-5 cut so a qualifying
  // stock ranked 6th in its industry is not discarded.
  const allSectorsByIndustry = (() => {
    const groups = new Map<string, ValueStockRow[]>();
    for (const stock of allStocksFlat) {
      if (valueMomentumOnly && !passesValueMomentum(stock)) continue;
      if (fStrongOnly && !passesFScore(stock)) continue;
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
    if (valueMomentumOnly && !passesValueMomentum(r)) return false;
    if (fStrongOnly && !passesFScore(r)) return false;
    return true;
  });

  // Preserve original rank position across re-sorts
  const rankedRows = baseRows.map((row, i) => ({ row, rank: i + 1 }));
  const sortedPairs = sortKey === "__rank__"
    ? (sortDir === "asc" ? rankedRows : [...rankedRows].reverse())
    : [...rankedRows].sort((a, b) => {
        const av = getValue(a.row, sortKey as keyof ValueStockRow);
        const bv = getValue(b.row, sortKey as keyof ValueStockRow);
        // Missing values (-Infinity sentinel) always sort last, regardless of
        // direction — otherwise "ascending" on a lower-is-better column like
        // P/E would put "no data" rows above real ones.
        const aMissing = av === -Infinity;
        const bMissing = bv === -Infinity;
        if (aMissing || bMissing) return aMissing === bMissing ? 0 : aMissing ? 1 : -1;
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
      const isNum = key === "__rank__" || key === "trend_signal" || NUMERIC_STOCK_COLS.includes(key as keyof ValueStockRow);
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
          <p className="text-[11px] text-gray-600 mt-1 max-w-2xl">
            How a stock is identified as &ldquo;value&rdquo;: EV/EBITDA, book yield, FCF yield, sales yield,
            PEG, and dividend yield are each ranked against the stock&apos;s own sector peers (not the whole
            universe), then an ROA / liquidity / earnings-quality / Debt-Equity check adds or subtracts points
            so a cheap score isn&apos;t a value trap — plus a separate Graham Number margin-of-safety estimate.
            Hover a score to see its cheapness / quality split. The Trend column flags cheap stocks that are
            still falling; turn on <span className="text-gray-400">Value + Momentum</span> to hide them. The
            F-Score column checks whether the business is getting financially stronger or weaker year over
            year; turn on <span className="text-gray-400">F-Score ≥ 7</span> to keep only the strong ones.
            Ratios shown as <span className="italic">n/m</span> are negative or extreme and not comparable.
            See <span className="text-gray-400">&ldquo;What am I looking at?&rdquo;</span> below for the full
            breakdown. Not investment advice.
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
          <span className="text-xs text-gray-500">Sectors represented:</span>
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
          <button
            type="button"
            onClick={() => setValueMomentumOnly((v) => !v)}
            aria-pressed={valueMomentumOnly}
            title={`Show only stocks scoring ${VALUE_MOMENTUM_MIN_SCORE}+ whose trend isn't Down — cheap AND not still falling`}
            className={[
              "text-xs px-2.5 py-1.5 rounded border transition-colors",
              valueMomentumOnly
                ? "bg-indigo-600 border-indigo-500 text-white"
                : "bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-500",
            ].join(" ")}
          >
            {valueMomentumOnly ? "✓ " : ""}Value + Momentum
            <span className="ml-1.5 opacity-70">
              (score ≥ {VALUE_MOMENTUM_MIN_SCORE}, trend not ▼)
            </span>
          </button>
          <button
            type="button"
            onClick={() => setFStrongOnly((v) => !v)}
            aria-pressed={fStrongOnly}
            title="Show only financially strong stocks: Piotroski F-score of 7+ out of 9, or the same share of the tests that apply (4/4 for banks)"
            className={[
              "text-xs px-2.5 py-1.5 rounded border transition-colors",
              fStrongOnly
                ? "bg-indigo-600 border-indigo-500 text-white"
                : "bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-500",
            ].join(" ")}
          >
            {fStrongOnly ? "✓ " : ""}F-Score ≥ 7
            <span className="ml-1.5 opacity-70">(financially strong)</span>
          </button>
          {(filterSector || filterIndustry || valueMomentumOnly || fStrongOnly) && (
            <>
              <button
                type="button"
                onClick={() => { setFilterSector(""); setFilterIndustry(""); setValueMomentumOnly(false); setFStrongOnly(false); }}
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
          <table className="text-left min-w-[1814px] w-max">
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
                    {valueMomentumOnly || fStrongOnly || filterSector || filterIndustry ? "No stocks match the current filters." : "No data for this sector."}
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
