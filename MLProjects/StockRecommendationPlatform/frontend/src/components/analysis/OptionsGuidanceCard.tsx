import { Accordion } from "@/components/ui/Accordion";
import { Badge } from "@/components/ui/Badge";
import type { OptionsGuidance } from "@/types/api";

export function OptionsGuidanceCard({ guidance }: { guidance: OptionsGuidance }) {
  return (
    <Accordion title="Options Guidance" defaultOpen={false}>
      <div className="space-y-3 text-sm">
        {guidance.strategy_family && (
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wide">Strategy</span>
            <p className="text-gray-200 font-medium mt-0.5">
              {guidance.strategy_family.replace(/_/g, " ")}
            </p>
          </div>
        )}
        {guidance.rationale_codes.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {guidance.rationale_codes.map((code) => (
              <Badge key={code} variant="info" size="sm">
                {code}
              </Badge>
            ))}
          </div>
        )}

        {/* Chain-verified strikes — highest confidence, shown before generic guidance */}
        {guidance.chain_validated && guidance.chain_verified_strikes ? (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Strike Guidance</span>
              <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-950 border border-emerald-700 rounded px-1.5 py-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                Chain Verified
              </span>
            </div>
            <p className="font-mono text-emerald-300 bg-gray-900 rounded px-2 py-1 text-xs">
              {guidance.chain_verified_strikes}
            </p>
            {guidance.strike_guidance && (
              <p className="text-gray-500 mt-1 text-xs italic">{guidance.strike_guidance}</p>
            )}
          </div>
        ) : guidance.strike_guidance ? (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Strike Guidance</span>
              <span className="text-xs text-amber-500 bg-amber-950 border border-amber-700 rounded px-1.5 py-0.5">
                Estimated
              </span>
            </div>
            <p className="text-gray-300 mt-0.5">{guidance.strike_guidance}</p>
          </div>
        ) : null}

        {guidance.max_loss_scenario && (
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wide">Max Loss Scenario</span>
            <p className="text-red-400 mt-0.5">{guidance.max_loss_scenario}</p>
          </div>
        )}
        {guidance.profit_targets_scenario.length > 0 && (
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wide">Profit Targets</span>
            <ul className="mt-0.5 space-y-0.5">
              {guidance.profit_targets_scenario.map((t, i) => (
                <li key={i} className="text-green-400 text-sm">
                  • {t}
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="text-xs text-amber-500 italic border-t border-gray-800 pt-2">
          {guidance.disclaimer}
        </p>
      </div>
    </Accordion>
  );
}
