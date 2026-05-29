"use client";

import type { SupervisorVerdict } from "@/types/api";

function urgencyStyle(days: number | null): { bg: string; border: string; text: string; dot: string } {
  if (days == null) return { bg: "bg-gray-800", border: "border-gray-700", text: "text-gray-300", dot: "bg-gray-500" };
  if (days <= 3)   return { bg: "bg-red-900/40",    border: "border-red-700",    text: "text-red-300",    dot: "bg-red-400" };
  if (days <= 7)   return { bg: "bg-amber-900/30",  border: "border-amber-700",  text: "text-amber-300",  dot: "bg-amber-400" };
  if (days <= 21)  return { bg: "bg-yellow-900/20", border: "border-yellow-800", text: "text-yellow-300", dot: "bg-yellow-400" };
  return              { bg: "bg-gray-900",         border: "border-gray-700",   text: "text-gray-300",   dot: "bg-gray-500" };
}

function daysLabel(days: number): string {
  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  return `${days} days`;
}

export function EarningsCountdown({ verdict }: { verdict: SupervisorVerdict }) {
  const { earnings_days_away, has_upcoming_earnings, decision_aids } = verdict;

  if (!has_upcoming_earnings && earnings_days_away == null) return null;

  const days   = earnings_days_away;
  const style  = urgencyStyle(days);
  const impliedMove = decision_aids?.volatility?.implied_move_1d_pct;

  // Estimate pre-earnings implied move: scale 1-day IV move by √(DTE) heuristic
  const earningsMove = impliedMove != null && days != null && days > 0
    ? impliedMove * Math.sqrt(Math.min(days, 5))
    : null;

  return (
    <div className={`rounded-lg border px-4 py-3 flex flex-wrap items-center gap-4 ${style.bg} ${style.border}`}>
      {/* Pulse dot */}
      <span className="relative flex h-3 w-3 shrink-0">
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-60 ${style.dot}`} />
        <span className={`relative inline-flex rounded-full h-3 w-3 ${style.dot}`} />
      </span>

      {/* Main copy */}
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-semibold ${style.text}`}>
          {days != null
            ? `Earnings in ${daysLabel(days)}`
            : "Upcoming Earnings"}
        </p>
        {days != null && days <= 21 && (
          <p className="text-xs text-gray-400 mt-0.5">
            {days <= 3
              ? "Imminent — consider reducing position size or hedging."
              : days <= 7
              ? "This week — elevated IV expected; review options exposure."
              : "Within 3 weeks — watch for pre-earnings drift."}
          </p>
        )}
      </div>

      {/* Expected move badge */}
      {earningsMove != null && (
        <div className="text-right shrink-0">
          <p className="text-xs text-gray-500">Expected Move</p>
          <p className={`text-base font-bold font-mono ${style.text}`}>
            ±{earningsMove.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-600">IV-implied range</p>
        </div>
      )}
    </div>
  );
}
