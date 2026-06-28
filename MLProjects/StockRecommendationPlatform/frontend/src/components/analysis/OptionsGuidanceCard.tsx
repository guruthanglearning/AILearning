import { Accordion } from "@/components/ui/Accordion";
import { Badge } from "@/components/ui/Badge";
import type { OptionLeg, OptionsGuidance } from "@/types/api";

function LegTable({ legs, expiry }: { legs: OptionLeg[]; expiry?: string | null }) {
  return (
    <div className="mt-1 overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="text-gray-500 border-b border-gray-800">
            <th className="text-left py-1 pr-3">Action</th>
            <th className="text-left py-1 pr-3">Right</th>
            <th className="text-right py-1 pr-3">Strike</th>
            <th className="text-left py-1">Qty</th>
          </tr>
        </thead>
        <tbody>
          {legs.map((leg, i) => (
            <tr key={i} className="border-b border-gray-800/50 last:border-0">
              <td className={`py-1 pr-3 font-semibold ${leg.leg_type === "long" ? "text-emerald-400" : "text-red-400"}`}>
                {leg.leg_type === "long" ? "Buy" : "Sell"}
              </td>
              <td className="py-1 pr-3 text-gray-300 uppercase">{leg.right}</td>
              <td className="py-1 pr-3 text-gray-100 text-right">${leg.strike.toFixed(0)}</td>
              <td className="py-1 text-gray-500">{leg.quantity_signed > 0 ? `+${leg.quantity_signed}` : leg.quantity_signed}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {expiry && (
        <p className="text-gray-500 mt-1">Expiry: <span className="text-gray-300">{expiry}</span></p>
      )}
    </div>
  );
}

function parseExpiry(verifiedStr: string | null): string | null {
  if (!verifiedStr) return null;
  const m = verifiedStr.match(/exp (\S+)/);
  return m ? m[1] : null;
}

function isYfinanceFallback(source: string | null): boolean {
  return source !== null && source.includes("yfinance");
}

export function OptionsGuidanceCard({ guidance }: { guidance: OptionsGuidance }) {
  const expiry = parseExpiry(guidance.chain_verified_strikes ?? null);
  const yfinanceFallback = isYfinanceFallback(guidance.chain_source ?? null);

  return (
    <Accordion title="Options Guidance" defaultOpen={false}>
      <div className="space-y-3 text-sm">
        {yfinanceFallback && (
          <div className="flex items-center gap-2 text-xs bg-amber-950 border border-amber-700 rounded px-2 py-1.5">
            <span className="text-amber-400">⚠</span>
            <span className="text-amber-300 font-medium">yfinance data</span>
            <span className="text-amber-500">— Polygon unavailable; chain uses delayed yfinance quotes. Strike precision and IV may differ from live market.</span>
          </div>
        )}
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

        {/* Chain-verified strikes — structured leg table when chain data available */}
        {guidance.chain_validated && guidance.validated_legs.length > 0 ? (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Strike Guidance</span>
              <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-950 border border-emerald-700 rounded px-1.5 py-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                Chain Verified
              </span>
            </div>
            <div className="bg-gray-900 rounded px-3 py-2">
              <LegTable legs={guidance.validated_legs} expiry={expiry} />
            </div>
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
