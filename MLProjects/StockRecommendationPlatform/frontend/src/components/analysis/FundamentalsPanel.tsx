"use client";

import type { FundamentalsSnapshot } from "@/types/api";

function fmtCap(v: number | null): string {
  if (v == null) return "—";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9)  return `$${(v / 1e9).toFixed(1)}B`;
  return `$${(v / 1e6).toFixed(0)}M`;
}

function fmtPct(v: number | null): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

function fmtRatio(v: number | null): string {
  if (v == null) return "—";
  return v.toFixed(1) + "×";
}

function peColor(v: number | null): string {
  if (v == null) return "text-gray-400";
  if (v < 15) return "text-green-400";
  if (v < 30) return "text-gray-200";
  return "text-red-400";
}

function revGrowthColor(v: number | null): string {
  if (v == null) return "text-gray-400";
  if (v > 0.15) return "text-green-400";
  if (v > 0)    return "text-gray-200";
  return "text-red-400";
}

interface Bullet { label: string; text: string }

interface MetricRowProps {
  label: string;
  value: string;
  color?: string;
  summary: string;
  bullets?: Bullet[];
  note?: string;
}

function MetricRow({ label, value, color = "text-gray-200", summary, bullets, note }: MetricRowProps) {
  return (
    <div className="py-3 border-b border-gray-800 last:border-0 space-y-2">
      {/* Label + value */}
      <div className="flex items-baseline gap-3">
        <span className="text-xs text-gray-400 w-36 shrink-0">{label}</span>
        <span className={`text-sm font-mono font-semibold ${color}`}>{value}</span>
      </div>
      {/* Summary line */}
      <p className="text-xs text-gray-500 leading-relaxed pl-0">{summary}</p>
      {/* Bullet detail rows */}
      {bullets && bullets.length > 0 && (
        <dl className="space-y-1 pl-2 border-l border-gray-800">
          {bullets.map(({ label: bl, text }) => (
            <div key={bl} className="flex gap-2 text-xs leading-relaxed">
              <dt className="text-gray-600 shrink-0 w-28">{bl}</dt>
              <dd className="text-gray-500">{text}</dd>
            </div>
          ))}
        </dl>
      )}
      {note && (
        <p className="text-xs text-amber-700/80 italic pl-0">{note}</p>
      )}
    </div>
  );
}

export function FundamentalsPanel({ fund }: { fund: FundamentalsSnapshot }) {
  const hasAnyData = fund.pe_ratio != null || fund.forward_pe != null ||
                     fund.market_cap != null || fund.revenue_growth != null;

  if (!hasAnyData && !fund.company_name && !fund.sector) return null;

  const trailingLabel = fund.pe_ratio != null
    ? (fund.pe_ratio < 15 ? "Below 15× — historically cheap territory."
       : fund.pe_ratio < 25 ? "15–25× — fairly valued range."
       : fund.pe_ratio < 35 ? "25–35× — growth premium; market expects above-average earnings."
       : "Above 35× — high-growth or speculative valuation; verify earnings trajectory.")
    : null;

  const forwardVsTrailing =
    fund.forward_pe != null && fund.pe_ratio != null
      ? fund.forward_pe < fund.pe_ratio
        ? `Forward P/E (${fmtRatio(fund.forward_pe)}) is below Trailing P/E (${fmtRatio(fund.pe_ratio)}) — analysts expect earnings to grow over the next 12 months.`
        : fund.forward_pe > fund.pe_ratio
        ? `Forward P/E (${fmtRatio(fund.forward_pe)}) is above Trailing P/E (${fmtRatio(fund.pe_ratio)}) — analysts expect earnings to shrink or slow; verify the reason.`
        : `Forward P/E matches Trailing P/E — flat earnings expected.`
      : null;

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-gray-400">Fundamentals</h2>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">

        {/* Header: company + sector */}
        {(fund.company_name || fund.sector) && (
          <div className="flex flex-wrap items-baseline gap-2 mb-4 pb-3 border-b border-gray-800">
            {fund.company_name && (
              <span className="text-sm font-semibold text-white">{fund.company_name}</span>
            )}
            {fund.sector && (
              <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{fund.sector}</span>
            )}
          </div>
        )}

        {/* Market Cap */}
        {fund.market_cap != null && (
          <MetricRow
            label="Market Cap"
            value={fmtCap(fund.market_cap)}
            summary="Total market value of all outstanding shares (share price × shares outstanding)."
            bullets={[
              { label: "Large-cap >$10B", text: "Established companies with lower volatility; institutional-grade liquidity." },
              { label: "Mid-cap $2–10B",  text: "Balance of growth potential and relative stability." },
              { label: "Small-cap <$2B",  text: "Higher growth ceiling but wider bid-ask spreads and more price volatility." },
            ]}
          />
        )}

        {/* Trailing P/E */}
        <MetricRow
          label="Trailing P/E"
          value={fmtRatio(fund.pe_ratio)}
          color={peColor(fund.pe_ratio)}
          summary="Formula: Stock Price ÷ Earnings Per Share over the last 12 months (actual, reported). Tells you how much investors pay today for each dollar of profit the company already earned."
          bullets={[
            { label: "< 15×",   text: "Historically cheap — often value stocks, cyclicals at a trough, or stocks with slower growth." },
            { label: "15 – 25×", text: "Fairly valued for a mature business. Compare to the sector median." },
            { label: "25 – 35×", text: "Growth premium — market expects above-average earnings expansion ahead." },
            { label: "> 35×",   text: "High-growth or speculative. Can be justified by strong revenue acceleration, but leaves little margin for disappointment." },
            { label: "Limitation",text: "Uses past earnings; a one-time write-down or gain can distort it. Always pair with Forward P/E." },
          ]}
          note={trailingLabel ?? undefined}
        />

        {/* Forward P/E */}
        <MetricRow
          label="Forward P/E"
          value={fmtRatio(fund.forward_pe)}
          color={peColor(fund.forward_pe)}
          summary="Formula: Stock Price ÷ Analyst Consensus EPS Estimate for the next 12 months. Reflects what the market is willing to pay for expected future profits — the most forward-looking single valuation number."
          bullets={[
            { label: "Key signal",   text: "Forward P/E < Trailing P/E → earnings expected to GROW (positive). Forward P/E > Trailing P/E → earnings expected to SHRINK or slow (negative)." },
            { label: "Sector context", text: "High-growth sectors (tech, biotech, AI) routinely trade at 30–60× forward earnings. Utilities and banks typically trade at 10–15×. Always compare within the sector." },
            { label: "PEG shortcut", text: "Divide Forward P/E by expected growth rate. PEG < 1.0 is often considered undervalued relative to growth; PEG > 2.0 may be stretched." },
            { label: "Limitation",   text: "Analyst estimates can be wrong — especially for volatile or early-stage companies. Earnings revisions (up or down) drive significant price moves." },
            { label: "Revision risk",text: "If analysts have recently cut their estimates, the printed Forward P/E may look low but could rise as the consensus adjusts." },
          ]}
          note={forwardVsTrailing ?? undefined}
        />

        {/* Revenue Growth */}
        {fund.revenue_growth != null && (
          <MetricRow
            label="Revenue Growth"
            value={fmtPct(fund.revenue_growth)}
            color={revGrowthColor(fund.revenue_growth)}
            summary="Year-over-year change in total revenue. High revenue growth can justify elevated P/E multiples; declining revenue under a low P/E is a value trap warning."
            bullets={[
              { label: "> 20%",    text: "Hyper-growth — premium multiples often warranted; watch for profitability path." },
              { label: "5 – 20%",  text: "Healthy expansion; sustainable if margins are intact or improving." },
              { label: "0 – 5%",   text: "Slow growth; value or turnaround thesis needed to justify paying up." },
              { label: "Negative", text: "Contracting revenues — red flag unless driven by a known strategic divestiture." },
            ]}
          />
        )}

        {fund.forward_pe == null && fund.pe_ratio == null && (
          <p className="text-xs text-gray-600 italic mt-2">
            P/E ratios unavailable — common for pre-earnings, negative-earnings, or index / ETF symbols.
          </p>
        )}
      </div>
    </div>
  );
}
