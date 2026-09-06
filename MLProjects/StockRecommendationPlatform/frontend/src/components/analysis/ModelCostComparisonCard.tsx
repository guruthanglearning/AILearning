import type { AnalysisCostBreakdown } from "@/types/api";

function formatCost(cost: number): string {
  return cost < 0.01 ? `$${cost.toFixed(4)}` : `$${cost.toFixed(3)}`;
}

export function ModelCostComparisonCard({ breakdown }: { breakdown: AnalysisCostBreakdown }) {
  const { estimates, input_tokens, output_tokens } = breakdown;
  if (estimates.length === 0) return null;

  const selected = estimates.find((e) => e.is_selected);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
      <div>
        <h2 className="text-xs font-semibold text-gray-300">Model Cost Comparison</h2>
        <p className="text-[10px] text-gray-600 mt-0.5">
          Estimated from this run&rsquo;s {input_tokens.toLocaleString()} in / {output_tokens.toLocaleString()} out tokens
          (incl. prompt-cache read/write), applied to each model&rsquo;s pricing. The GPT-4o mini row is a rougher
          approximation — OpenAI tokenizes text differently than Claude.
        </p>
      </div>

      {selected && (
        <div className="flex items-center justify-between bg-indigo-950/40 border border-indigo-900/60 rounded-md px-3 py-2">
          <span className="text-xs text-indigo-300">Cost for this analysis ({selected.label})</span>
          <span className="text-sm font-mono font-semibold text-indigo-200">
            {formatCost(selected.cost_usd)}
          </span>
        </div>
      )}

      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-600 border-b border-gray-800">
            <th className="text-left font-medium py-1">Model</th>
            <th className="text-right font-medium py-1">Cost</th>
          </tr>
        </thead>
        <tbody>
          {estimates.map((e) => (
            <tr
              key={e.model}
              className={`border-b border-gray-800/50 last:border-0 ${
                e.is_selected ? "bg-indigo-950/30" : ""
              }`}
            >
              <td
                className={`py-1.5 pr-2 ${
                  e.is_selected ? "text-indigo-300 font-medium" : "text-gray-400"
                }`}
              >
                {e.label}
                {e.is_selected && (
                  <span className="ml-1.5 text-[9px] uppercase tracking-wide text-indigo-500">
                    selected
                  </span>
                )}
              </td>
              <td
                className={`py-1.5 text-right font-mono ${
                  e.is_selected ? "text-indigo-200 font-medium" : "text-gray-500"
                }`}
              >
                {formatCost(e.cost_usd)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
