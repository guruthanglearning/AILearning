import type { VolatilityContext } from "@/types/api";

function pct(v: number | null) {
  return v == null ? "—" : `${(v * 100).toFixed(1)}%`;
}

function ivRankColor(rank: number): string {
  if (rank >= 70) return "text-red-400";
  if (rank >= 40) return "text-amber-400";
  return "text-green-400";
}

function ivRankLabel(rank: number): string {
  if (rank >= 70) return "Elevated — favour selling premium (credit spreads)";
  if (rank >= 40) return "Neutral — directional bias drives instrument choice";
  return "Cheap — long premium structures relatively inexpensive";
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

        {/* IV Rank — spans full row for emphasis */}
        {vol.iv_rank_52w != null && (
          <div className="col-span-2 sm:col-span-3">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
              IV Rank (52W) <span className="normal-case text-gray-600">— vs rolling HV range</span>
            </p>
            <div className="flex items-center gap-3">
              {/* Gauge bar */}
              <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    vol.iv_rank_52w >= 70 ? "bg-red-500" :
                    vol.iv_rank_52w >= 40 ? "bg-amber-500" : "bg-green-500"
                  }`}
                  style={{ width: `${vol.iv_rank_52w.toFixed(0)}%` }}
                />
              </div>
              <span className={`text-sm font-bold font-mono w-12 text-right ${ivRankColor(vol.iv_rank_52w)}`}>
                {vol.iv_rank_52w.toFixed(0)}
              </span>
            </div>
            <p className={`text-xs mt-1 ${ivRankColor(vol.iv_rank_52w)}`}>
              {ivRankLabel(vol.iv_rank_52w)}
            </p>
          </div>
        )}

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
