"use client";

import dynamic from "next/dynamic";

const EarningsCalendar = dynamic(
  () => import("@/components/market/EarningsCalendar").then((m) => m.EarningsCalendar),
  { ssr: false },
);

export default function EarningsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-white">Earnings Calendar</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Upcoming earnings dates for your tracked symbols — same list as Market Grid.
        </p>
      </div>
      <EarningsCalendar />
    </div>
  );
}
