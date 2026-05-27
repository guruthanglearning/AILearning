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

interface MetricRowProps {
  label: string;
  value: string;
  color?: string;
  description: string;
}

function MetricRow({ label, value, color = "text-gray-200", description }: MetricRowProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-4 py-2.5 border-b border-gray-800 last:border-0">
      <div className="flex items-baseline gap-3 sm:w-64 shrink-0">
        <span className="text-xs text-gray-400 w-36 shrink-0">{label}</span>
        <span className={`text-sm font-mono font-semibold ${color}`}>{value}</span>
      </div>
      <p className="text-xs text-gray-600 leading-relaxed">{description}</p>
    </div>
  );
}

export function FundamentalsPanel({ fund }: { fund: FundamentalsSnapshot }) {
  const hasAnyData = fund.pe_ratio != null || fund.forward_pe != null ||
                     fund.market_cap != null || fund.revenue_growth != null;

  if (!hasAnyData && !fund.company_name && !fund.sector) return null;

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

        <div className="divide-y divide-gray-800/0">
          {fund.market_cap != null && (
            <MetricRow
              label="Market Cap"
              value={fmtCap(fund.market_cap)}
              description="Total market value of all outstanding shares. Large-cap (>$10B) companies are generally more stable; small-cap offer more growth potential with higher risk."
            />
          )}

          <MetricRow
            label="Trailing P/E"
            value={fmtRatio(fund.pe_ratio)}
            color={peColor(fund.pe_ratio)}
            description="Price-to-Earnings using the last 12 months of actual earnings. Shows what investors are paying today per dollar of realized profit. < 15× = historically cheap; > 30× = growth premium priced in."
          />

          <MetricRow
            label="Forward P/E"
            value={fmtRatio(fund.forward_pe)}
            color={peColor(fund.forward_pe)}
            description="Price-to-Earnings using next 12 months of analyst-estimated earnings. A lower Forward P/E than Trailing P/E signals expected earnings growth. Compare to peers in the same sector — high-growth sectors (tech, biotech) typically command higher multiples."
          />

          {fund.revenue_growth != null && (
            <MetricRow
              label="Revenue Growth"
              value={fmtPct(fund.revenue_growth)}
              color={revGrowthColor(fund.revenue_growth)}
              description="Year-over-year change in total revenue. Sustained growth above 15% supports premium valuation multiples. Negative growth is a red flag unless the business is in a deliberate restructuring phase."
            />
          )}
        </div>

        {fund.forward_pe == null && fund.pe_ratio == null && (
          <p className="text-xs text-gray-600 italic mt-2">
            P/E ratios unavailable — common for pre-earnings, negative-earnings, or index/ETF symbols.
          </p>
        )}
      </div>
    </div>
  );
}
