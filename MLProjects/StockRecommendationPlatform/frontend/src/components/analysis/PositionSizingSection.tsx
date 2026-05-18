import type { PositionSizingHint } from "@/types/api";

function fmt(v: number | null) {
  if (v == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

export function PositionSizingSection({ hints }: { hints: PositionSizingHint[] }) {
  if (!hints.length) return null;
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {hints.map((hint, i) => (
        <div key={i} className="bg-gray-800 rounded-lg p-4 text-sm space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-wide">{hint.instrument_type}</p>
          <p className="text-gray-200">{hint.note}</p>
          <p className="text-xs text-gray-400">
            Risk budget: {hint.suggested_risk_budget_pct_range[0]}%–
            {hint.suggested_risk_budget_pct_range[1]}%
          </p>
          {hint.example_notional_at_1pct_portfolio != null && (
            <p className="text-xs text-gray-500">
              ~{fmt(hint.example_notional_at_1pct_portfolio)} at 1% of portfolio
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
