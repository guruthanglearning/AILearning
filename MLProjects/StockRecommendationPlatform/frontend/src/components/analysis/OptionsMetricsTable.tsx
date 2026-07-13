"use client";

import {
  SortingState,
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import type { OptionLeg, OptionsMetricRow } from "@/types/api";

const fmtCurrency = (v: number | null) =>
  v == null ? "—" : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v);

function fmtLegs(legs: OptionLeg[]): string {
  return legs
    .map(
      (leg) =>
        `${leg.leg_type === "long" ? "Long" : "Short"} ${leg.right === "call" ? "C" : "P"} $${leg.strike}`
    )
    .join(" / ");
}

const QUALITY_VARIANT: Record<string, "success" | "warning" | "error"> = {
  full: "success",
  partial: "warning",
  degraded: "error",
};

function isMarketClosed(row: OptionsMetricRow): boolean {
  return row.row_data_quality === "degraded" && row.degraded_reasons.includes("market_closed");
}

const TREND_VARIANT: Record<string, "success" | "error" | "neutral"> = {
  aligned: "success",
  counter: "error",
  neutral: "neutral",
};

const THETA_COLOR: Record<string, string> = {
  positive: "text-green-400",
  negative: "text-red-400",
};

const GAMMA_COLOR: Record<string, string> = {
  positive: "text-green-400",
  high: "text-amber-400",
};

const col = createColumnHelper<OptionsMetricRow>();

const COLUMNS = [
  col.accessor("row_data_quality", {
    header: "Quality",
    cell: ({ getValue, row }) => {
      const q = getValue();
      const reasons = row.original.degraded_reasons;
      if (isMarketClosed(row.original)) {
        return (
          <Badge variant="warning" title="Bid/ask unavailable outside market hours">
            mkt closed
          </Badge>
        );
      }
      return (
        <Badge
          variant={QUALITY_VARIANT[q] ?? "neutral"}
          title={reasons.length ? reasons.join("; ") : undefined}
        >
          {q}
        </Badge>
      );
    },
  }),
  col.accessor("strategy_label", {
    header: "Strategy",
    cell: ({ getValue, row }) => (
      <div>
        <div className="font-medium text-white">{getValue()}</div>
        <div className="text-xs text-gray-600">{row.original.template_id}</div>
      </div>
    ),
  }),
  col.accessor("expiration", {
    header: "Expiry",
    cell: ({ getValue }) => getValue() ?? "—",
  }),
  col.accessor("dte_at_analysis", {
    header: "DTE",
    cell: ({ getValue }) => (getValue() == null ? "—" : getValue()),
  }),
  col.accessor("legs", {
    header: "Legs",
    cell: ({ getValue }) => {
      const legs = getValue();
      return legs.length ? (
        <span className="font-mono text-xs">{fmtLegs(legs)}</span>
      ) : (
        "—"
      );
    },
  }),
  col.accessor("net_debit_credit", {
    header: "Net D/C",
    cell: ({ getValue }) => {
      const v = getValue();
      if (v == null) return "—";
      return (
        <span className={v > 0 ? "text-green-400" : "text-red-400"}>
          {fmtCurrency(v)}
        </span>
      );
    },
  }),
  col.accessor("max_profit", {
    header: "Max Profit",
    cell: ({ getValue }) => (
      <span className="text-green-400">{fmtCurrency(getValue())}</span>
    ),
  }),
  col.accessor("max_loss", {
    header: "Max Loss",
    cell: ({ getValue }) => (
      <span className="text-red-400">{fmtCurrency(getValue())}</span>
    ),
  }),
  col.accessor("breakeven_prices", {
    header: "Breakeven(s)",
    cell: ({ getValue }) => {
      const bp = getValue();
      return bp.length ? bp.map((p) => `$${p}`).join(" / ") : "—";
    },
  }),
  col.accessor("underlying_at_analysis", {
    header: "Spot",
    cell: ({ getValue }) => fmtCurrency(getValue()),
  }),
  col.accessor("trend_alignment", {
    header: "Trend",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v) return "—";
      const key = v.toLowerCase();
      return (
        <Badge variant={TREND_VARIANT[key] ?? "neutral"}>{v}</Badge>
      );
    },
  }),
  col.accessor("liquidity", {
    header: "Liquidity",
    cell: ({ getValue }) => getValue() ?? "—",
  }),
  col.accessor("expected_move", {
    header: "Exp. Move",
    cell: ({ getValue }) => getValue() ?? "—",
  }),
  col.accessor("execution_quality", {
    header: "Execution",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v) return "—";
      return <span title={v} className="text-gray-400">{v.length > 30 ? v.slice(0, 30) + "…" : v}</span>;
    },
  }),
  col.accessor("risk_profile", {
    header: "Risk Profile",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v) return "—";
      return <span title={v} className="text-red-300">{v.length > 35 ? v.slice(0, 35) + "…" : v}</span>;
    },
  }),
  col.accessor("theta_edge", {
    header: "Theta Edge",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v) return "—";
      const key = v.split(" ")[0].toLowerCase();
      return <span className={THETA_COLOR[key] ?? "text-gray-300"} title={v}>{v.split(" ")[0]}</span>;
    },
  }),
  col.accessor("gamma_risk", {
    header: "Gamma Risk",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v) return "—";
      const key = v.split(" ")[0].toLowerCase();
      return <span className={GAMMA_COLOR[key] ?? "text-amber-400"} title={v}>{v.split(" ")[0]}</span>;
    },
  }),
  col.accessor("credit_quality", {
    header: "Credit Quality",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v || v.startsWith("N/A")) return <span className="text-gray-600">N/A</span>;
      const isGood = v.startsWith("Good");
      const isFair = v.startsWith("Fair");
      return (
        <span className={isGood ? "text-green-400" : isFair ? "text-amber-400" : "text-red-400"} title={v}>
          {v}
        </span>
      );
    },
  }),
  col.accessor("rule_30pct", {
    header: "30% Rule",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v) return "—";
      return <span title={v} className="text-blue-300">{v.length > 35 ? v.slice(0, 35) + "…" : v}</span>;
    },
  }),
  col.accessor("rule_60pct", {
    header: "60% Rule",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v) return "—";
      return <span title={v} className="text-indigo-300">{v.length > 35 ? v.slice(0, 35) + "…" : v}</span>;
    },
  }),
  col.accessor("management_rules", {
    header: "Management",
    cell: ({ getValue }) => {
      const v = getValue();
      if (!v) return "—";
      const truncated = v.length > 60 ? v.slice(0, 60) + "…" : v;
      return <span title={v}>{truncated}</span>;
    },
  }),
];

export function OptionsMetricsTable({ rows, marketState }: { rows: OptionsMetricRow[]; marketState?: string | null }) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data: rows,
    columns: COLUMNS,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const disclaimer = rows[0]?.disclaimer ?? "Hypothetical scenarios only; not investment advice.";
  const hasMarketClosedRows = rows.some(isMarketClosed);
  const showMarketClosedBanner = hasMarketClosedRows && marketState !== "REGULAR";

  return (
    <div className="space-y-2">
      {showMarketClosedBanner && (
        <div className="flex items-center gap-2 text-xs bg-amber-950 border border-amber-700 rounded px-3 py-1.5">
          <span className="text-amber-400">⏸</span>
          <span className="text-amber-300 font-medium">Market closed</span>
          <span className="text-amber-500">— bid/ask unavailable; spread debit/credit and max profit/loss cannot be calculated until next session.</span>
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border border-gray-800">
        <table className="w-full text-xs text-left">
          <thead className="bg-gray-900 text-gray-400 sticky top-0">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-3 py-2 font-medium whitespace-nowrap cursor-pointer select-none hover:text-gray-200"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() === "asc"
                      ? " ▲"
                      : header.column.getIsSorted() === "desc"
                      ? " ▼"
                      : ""}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-800">
            {table.getRowModel().rows.map((row, i) => (
              <tr
                key={row.id}
                className={`${i % 2 === 0 ? "bg-gray-950" : "bg-gray-900"} hover:bg-gray-800 transition-colors`}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 text-gray-300 whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-amber-600 italic px-1">{disclaimer}</p>
    </div>
  );
}
