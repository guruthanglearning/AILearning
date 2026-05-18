import type { VolatilityContext } from "@/types/api";

function pct(v: number | null) {
  return v == null ? "—" : `${(v * 100).toFixed(1)}%`;
}

export function VolatilitySection({ vol }: { vol: VolatilityContext }) {
  return (
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
  );
}
