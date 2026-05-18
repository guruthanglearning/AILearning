import { StaleWarning } from "@/components/ui/StaleWarning";
import type { DataFreshness } from "@/types/api";

const STALE_MS = 120_000;

function ageLabel(ms: number | null): string {
  if (ms == null) return "—";
  if (ms < 1000) return `${ms}ms ago`;
  if (ms < 60_000) return `${Math.round(ms / 1000)}s ago`;
  return `${Math.round(ms / 60_000)}m ago`;
}

export function DataFreshnessStrip({ freshness }: { freshness: DataFreshness }) {
  return (
    <div className="flex flex-wrap gap-4 text-xs text-gray-500 py-2">
      <span>
        Quote:{" "}
        <span className="text-gray-300">{ageLabel(freshness.quote_age_ms)}</span>
        {freshness.quote_age_ms != null && freshness.quote_age_ms > STALE_MS && (
          <StaleWarning message="quote may be stale" />
        )}
      </span>
      <span>
        Chain:{" "}
        <span className="text-gray-300">{ageLabel(freshness.chain_age_ms)}</span>
        {freshness.chain_age_ms != null && freshness.chain_age_ms > STALE_MS && (
          <StaleWarning message="chain may be stale" />
        )}
      </span>
      {freshness.fundamentals_as_of_note && (
        <span>Fundamentals: {freshness.fundamentals_as_of_note}</span>
      )}
    </div>
  );
}
