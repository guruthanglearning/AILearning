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

const TREND_VARIANT: Record<string, "success" | "error" | "neutral"> = {
  aligned: "success",
  counter: "error",
  neutral: "neutral",
};

const col = createColumnHelper<OptionsMetricRow>();

const COLUMNS = [
  col.accessor("row_data_quality", {
    header: "Quality",
    cell: ({ getValue, row }) => {
      const q = getValue();
      const reasons = row.original.degraded_reasons;
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

export function OptionsMetricsTable({ rows }: { rows: OptionsMetricRow[] }) {
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

  return (
    <div className="space-y-2">
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
