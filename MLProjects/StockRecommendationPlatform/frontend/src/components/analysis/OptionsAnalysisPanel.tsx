"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import type { OptionsMetricRow } from "@/types/api";

interface MetricRowProps {
  label: string;
  value: string | null | undefined;
  colorFn?: (v: string) => string;
  fullText?: boolean;
}

function MetricRow({ label, value, colorFn, fullText }: MetricRowProps) {
  if (!value) return null;
  const color = colorFn ? colorFn(value) : "text-gray-200";
  const display = !fullText && value.length > 48 ? value.slice(0, 48) + "…" : value;
  return (
    <div className="flex justify-between items-start gap-3 py-1.5 border-b border-gray-800 last:border-0">
      <span className="text-xs text-gray-500 shrink-0 w-36">{label}</span>
      <span className={`text-xs text-right ${color}`} title={value}>
        {display}
      </span>
    </div>
  );
}

function trendColor(v: string) {
  const k = v.toLowerCase();
  if (k.startsWith("aligned")) return "text-green-400";
  if (k.startsWith("counter")) return "text-red-400";
  return "text-amber-400";
}

function thetaColor(v: string) {
  return v.toLowerCase().startsWith("positive") ? "text-green-400" : "text-red-400";
}

function gammaColor(v: string) {
  return v.toLowerCase().startsWith("positive") ? "text-green-400" : "text-amber-400";
}

function creditColor(v: string) {
  if (v.startsWith("Good")) return "text-green-400";
  if (v.startsWith("Fair")) return "text-amber-400";
  if (v.startsWith("Poor")) return "text-red-400";
  return "text-gray-500";
}

function liquidityColor(v: string) {
  const k = v.toLowerCase();
  if (k.includes("good") || k.includes("adequate")) return "text-green-400";
  if (k.includes("thin")) return "text-amber-400";
  return "text-gray-300";
}

const QUALITY_VARIANT: Record<string, "success" | "warning" | "error"> = {
  full: "success",
  partial: "warning",
  degraded: "error",
};

function StrategyCard({ row }: { row: OptionsMetricRow }) {
  const [open, setOpen] = useState(true);
  const isDegraded = row.row_data_quality === "degraded";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-100">{row.strategy_label}</span>
          <Badge variant={QUALITY_VARIANT[row.row_data_quality] ?? "neutral"}>
            {row.row_data_quality}
          </Badge>
          {row.expiration && (
            <span className="text-xs text-gray-500">
              {row.expiration}{row.dte_at_analysis != null ? ` · ${row.dte_at_analysis}DTE` : ""}
            </span>
          )}
        </div>
        <span className="text-gray-500 text-xs">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="px-4 pb-3">
          {isDegraded && row.degraded_reasons.length > 0 && (
            <p className="text-xs text-red-400 mb-2">
              Degraded: {row.degraded_reasons.join(", ")}
            </p>
          )}
          <MetricRow label="Trend Alignment" value={row.trend_alignment} colorFn={trendColor} />
          <MetricRow label="Theta Edge"      value={row.theta_edge}      colorFn={thetaColor} />
          <MetricRow label="Gamma Risk"      value={row.gamma_risk}      colorFn={gammaColor} />
          <MetricRow label="Credit Quality"  value={row.credit_quality}  colorFn={creditColor} />
          <MetricRow label="Liquidity"       value={row.liquidity}       colorFn={liquidityColor} />
          <MetricRow label="Expected Move"   value={row.expected_move} />
          <MetricRow label="Execution Quality" value={row.execution_quality} />
          <MetricRow label="Risk Profile"    value={row.risk_profile} />
          <MetricRow label="30% Rule"        value={row.rule_30pct}  colorFn={() => "text-blue-300"} />
          <MetricRow label="60% Rule"        value={row.rule_60pct}  colorFn={() => "text-indigo-300"} />
          {row.management_rules && (
            <MetricRow label="Management" value={row.management_rules} />
          )}
        </div>
      )}
    </div>
  );
}

export function OptionsAnalysisPanel({ rows }: { rows: OptionsMetricRow[] }) {
  const strategies = rows.filter((r) => r.template_id !== "underlying_summary");
  const summary = rows.find((r) => r.template_id === "underlying_summary");

  if (strategies.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-gray-400">Options Analysis</h2>
        {summary && (
          <div className="flex items-center gap-3 text-xs text-gray-500">
            {summary.expected_move && <span>Implied move {summary.expected_move}</span>}
            {summary.liquidity && <span>Chain liquidity: {summary.liquidity}</span>}
            {summary.expiration && <span>Nearest expiry {summary.expiration}</span>}
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {strategies.map((row) => (
          <StrategyCard key={row.template_id} row={row} />
        ))}
      </div>
      <p className="text-xs text-amber-600 italic px-1">
        {rows[0]?.disclaimer ?? "Hypothetical scenarios only; not investment advice."}
      </p>
    </div>
  );
}
