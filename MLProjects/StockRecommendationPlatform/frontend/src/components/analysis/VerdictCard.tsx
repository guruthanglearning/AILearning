import { Badge } from "@/components/ui/Badge";
import { ScoreMeter } from "@/components/ui/ScoreMeter";
import type { InstrumentRecommendation, SupervisorVerdict } from "@/types/api";

import { DataFreshnessStrip } from "./DataFreshnessStrip";

const REC_CONFIG: Record<
  InstrumentRecommendation,
  { label: string; border: string; badge: "success" | "info" | "warning" | "neutral" }
> = {
  stock: { label: "Stock", border: "border-green-700", badge: "success" },
  options: { label: "Options", border: "border-blue-700", badge: "info" },
  no_trade: { label: "No Trade", border: "border-amber-700", badge: "warning" },
  insufficient_data: { label: "Insufficient Data", border: "border-gray-700", badge: "neutral" },
};

interface VerdictCardProps {
  verdict: SupervisorVerdict;
  symbol: string;
}

export function VerdictCard({ verdict, symbol }: VerdictCardProps) {
  const cfg = REC_CONFIG[verdict.instrument_recommendation];

  return (
    <div className={`bg-gray-900 border-l-4 ${cfg.border} border border-gray-800 rounded-xl p-6`}>
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-xl font-bold text-white font-mono">{symbol}</span>
            <Badge variant={cfg.badge} size="md">
              {cfg.label}
            </Badge>
          </div>
          <p className="text-sm text-gray-300 max-w-xl">{verdict.confidence_note}</p>
        </div>
      </div>

      {verdict.decision_aids && (
        <div className="mt-4 space-y-2">
          <p className="text-xs text-gray-400 font-medium">
            {verdict.decision_aids.summary_headline}
          </p>
          <ScoreMeter score={verdict.decision_aids.stock_vs_options_score} />
        </div>
      )}

      <div className="mt-3 border-t border-gray-800 pt-3">
        <DataFreshnessStrip freshness={verdict.data_freshness} />
      </div>
    </div>
  );
}
