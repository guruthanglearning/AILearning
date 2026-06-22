"use client";

import { PortfolioTracker } from "@/components/portfolio/PortfolioTracker";

export default function PortfolioPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-white">Portfolio</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Track positions, cost basis, and unrealized P&amp;L in real time.
        </p>
      </div>
      <PortfolioTracker />
    </div>
  );
}
