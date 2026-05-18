import { Badge } from "@/components/ui/Badge";
import type { InstrumentPlayRow } from "@/types/api";

const COMPLEXITY_VARIANT: Record<string, "success" | "warning" | "error" | "neutral"> = {
  low: "success",
  medium: "warning",
  high: "error",
};

export function InstrumentPlaysSection({ plays }: { plays: InstrumentPlayRow[] }) {
  if (!plays.length) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-left">
        <thead>
          <tr className="text-gray-500 border-b border-gray-800">
            <th className="pb-2 pr-4 font-medium">Strategy</th>
            <th className="pb-2 pr-4 font-medium">When Favored</th>
            <th className="pb-2 pr-4 font-medium">Max Risk</th>
            <th className="pb-2 pr-4 font-medium">Capital Efficiency</th>
            <th className="pb-2 font-medium">Complexity</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {plays.map((play) => (
            <tr key={play.play_id} className="text-gray-300">
              <td className="py-2 pr-4 font-medium text-white">{play.label}</td>
              <td className="py-2 pr-4">{play.when_favored}</td>
              <td className="py-2 pr-4">{play.max_risk_profile}</td>
              <td className="py-2 pr-4">{play.capital_efficiency_note}</td>
              <td className="py-2">
                <Badge
                  variant={COMPLEXITY_VARIANT[play.complexity.toLowerCase()] ?? "neutral"}
                  size="sm"
                >
                  {play.complexity}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
