"use client";

import { useLiveQuote } from "@/hooks/useAnalysis";

const fmt = (v: number | null) =>
  v == null ? "—" : `$${v.toFixed(2)}`;

const fmtVol = (v: number | null) => {
  if (v == null) return "—";
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return String(v);
};

function changeColor(pct: number | null) {
  if (pct == null) return "text-gray-400";
  return pct >= 0 ? "text-green-400" : "text-red-400";
}

function MarketStateBadge({ state }: { state: string | null }) {
  if (!state) return null;
  const map: Record<string, { label: string; cls: string }> = {
    PRE:     { label: "Pre-Market",  cls: "bg-amber-900/50 text-amber-300 border-amber-700" },
    REGULAR: { label: "Market Open", cls: "bg-green-900/50 text-green-300 border-green-700" },
    POST:    { label: "After Hours", cls: "bg-blue-900/50 text-blue-300 border-blue-700" },
    CLOSED:  { label: "Closed",      cls: "bg-gray-800 text-gray-400 border-gray-700" },
  };
  const entry = map[state.toUpperCase()] ?? { label: state, cls: "bg-gray-800 text-gray-400 border-gray-700" };
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-medium ${entry.cls}`}>
      {entry.label}
    </span>
  );
}

interface PriceSlotProps {
  label: string;
  value: number | null;
  highlight?: boolean;
}

function PriceSlot({ label, value, highlight }: PriceSlotProps) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="text-xs text-gray-500">{label}</span>
      <span className={`text-sm font-mono font-semibold ${highlight ? "text-white" : "text-gray-300"}`}>
        {fmt(value)}
      </span>
    </div>
  );
}

export function LivePriceBar({ symbol }: { symbol: string }) {
  const { data: q, isFetching, dataUpdatedAt } = useLiveQuote(symbol);

  const updatedTime = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-3 flex flex-wrap items-center gap-6">

      {/* Symbol + market state */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-bold text-white font-mono">{symbol}</span>
        <MarketStateBadge state={q?.market_state ?? null} />
      </div>

      {/* Divider */}
      <div className="h-6 w-px bg-gray-700 hidden sm:block" />

      {/* Price slots */}
      <div className="flex items-center gap-6">
        <PriceSlot label="Pre-Market"  value={q?.pre_market ?? null} />
        <PriceSlot label="Open"        value={q?.open_price ?? null} />
        <PriceSlot label="Current"     value={q?.current ?? null} highlight />
        <PriceSlot label="Post-Market" value={q?.post_market ?? null} />
        <PriceSlot label="Prev Close"  value={q?.previous_close ?? null} />
      </div>

      {/* Divider */}
      <div className="h-6 w-px bg-gray-700 hidden sm:block" />

      {/* Change + volume */}
      <div className="flex items-center gap-5">
        <div className="flex flex-col items-center gap-0.5">
          <span className="text-xs text-gray-500">Day Change</span>
          <span className={`text-sm font-mono font-semibold ${changeColor(q?.day_change_pct ?? null)}`}>
            {q?.day_change_pct == null ? "—" : `${q.day_change_pct >= 0 ? "+" : ""}${q.day_change_pct.toFixed(2)}%`}
          </span>
        </div>
        <div className="flex flex-col items-center gap-0.5">
          <span className="text-xs text-gray-500">Volume</span>
          <span className="text-sm font-mono text-gray-300">{fmtVol(q?.volume ?? null)}</span>
        </div>
      </div>

      {/* Refresh indicator */}
      <div className="ml-auto flex items-center gap-2">
        {isFetching && (
          <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        )}
        {updatedTime && (
          <span className="text-xs text-gray-600">as of {updatedTime}</span>
        )}
      </div>
    </div>
  );
}
