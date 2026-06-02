import type { VolatilityContext } from "@/types/api";

function pct(v: number | null) {
  return v == null ? "—" : `${(v * 100).toFixed(1)}%`;
}

interface IvZone {
  label: string;
  hint: string;       // one-line action hint
  badgeBg: string;
  badgeText: string;
  barColor: string;
  textColor: string;
}

function ivZone(rank: number): IvZone {
  if (rank >= 70) return {
    label: "Elevated",
    hint: "Premium is historically expensive — favour selling premium (credit spreads, covered calls)",
    badgeBg: "bg-red-900/40 border-red-700",
    badgeText: "text-red-300",
    barColor: "bg-red-500",
    textColor: "text-red-400",
  };
  if (rank >= 40) return {
    label: "Neutral",
    hint: "Premium is fairly priced — let directional bias (trend, RSI) drive instrument choice",
    badgeBg: "bg-amber-900/40 border-amber-700",
    badgeText: "text-amber-300",
    barColor: "bg-amber-500",
    textColor: "text-amber-400",
  };
  return {
    label: "Cheap",
    hint: "Premium is historically inexpensive — buying long calls/puts costs less than usual vs recent swings",
    badgeBg: "bg-green-900/40 border-green-700",
    badgeText: "text-green-300",
    barColor: "bg-green-500",
    textColor: "text-green-400",
  };
}

export function VolatilitySection({ vol }: { vol: VolatilityContext }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Regime</p>
          <p className="text-gray-200 font-medium mt-0.5 capitalize">{vol.regime}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">ATM IV</p>
          <p className="text-gray-200 font-medium mt-0.5">{pct(vol.atm_iv)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">HV 20d</p>
          <p className="text-gray-200 font-medium mt-0.5">{pct(vol.hv_20d_annualized)}</p>
        </div>

        {/* IV Rank — full-width block */}
        {vol.iv_rank_52w != null && (() => {
          const zone = ivZone(vol.iv_rank_52w);
          const rank = vol.iv_rank_52w;
          return (
            <div className="col-span-2 sm:col-span-3 space-y-2">
              {/* Label row */}
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <p className="text-xs text-gray-500 uppercase tracking-wide">
                  IV Rank (52W)
                </p>
                {/* Zone badge */}
                <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-0.5 rounded-full border ${zone.badgeBg} ${zone.badgeText}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${zone.barColor}`} />
                  {zone.label}
                </span>
              </div>

              {/* Gauge with zone markers */}
              <div className="space-y-1">
                <div className="relative h-3 bg-gray-800 rounded-full overflow-visible">
                  {/* Filled bar */}
                  <div
                    className={`h-full rounded-full transition-all ${zone.barColor}`}
                    style={{ width: `${rank.toFixed(0)}%` }}
                  />
                  {/* Zone boundary tick at 40 */}
                  <div className="absolute top-0 bottom-0 w-px bg-gray-600" style={{ left: "40%" }} />
                  {/* Zone boundary tick at 70 */}
                  <div className="absolute top-0 bottom-0 w-px bg-gray-600" style={{ left: "70%" }} />
                </div>

                {/* Zone labels under gauge */}
                <div className="flex text-xs" style={{ position: "relative" }}>
                  <span className="text-green-500 font-medium" style={{ width: "40%" }}>Cheap &lt;40</span>
                  <span className="text-amber-500 font-medium text-center" style={{ width: "30%" }}>Neutral 40–70</span>
                  <span className="text-red-500 font-medium text-right flex-1">Elevated &gt;70</span>
                </div>

                {/* Rank number */}
                <div className="flex items-center justify-between">
                  <p className={`text-xs leading-relaxed ${zone.textColor}`}>{zone.hint}</p>
                  <span className={`text-sm font-bold font-mono ml-3 shrink-0 ${zone.textColor}`}>
                    {rank.toFixed(0)}
                  </span>
                </div>
              </div>
            </div>
          );
        })()}

        {vol.implied_move_1d_pct != null && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Implied Move 1d</p>
            <p className="text-gray-200 font-medium mt-0.5">{pct(vol.implied_move_1d_pct)}</p>
          </div>
        )}
        {vol.iv_vs_hv_note && (
          <div className="col-span-2">
            <p className="text-xs text-gray-500 uppercase tracking-wide">IV vs HV</p>
            <p className="text-gray-300 text-xs mt-0.5">{vol.iv_vs_hv_note}</p>
          </div>
        )}
      </div>
    </div>
  );
}
