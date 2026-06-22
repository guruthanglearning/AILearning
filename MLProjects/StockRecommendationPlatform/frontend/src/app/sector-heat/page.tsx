"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";

const SectorHeatmap = dynamic(
  () =>
    import("@/components/market/SectorHeatmap").then((m) => m.SectorHeatmap),
  { ssr: false },
);

export default function SectorHeatPage() {
  const router = useRouter();

  function handleAnalyze(symbol: string) {
    router.push(`/?symbol=${encodeURIComponent(symbol)}`);
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-white">Sector Heatmap</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Today&apos;s price change across all GICS sectors — green is up, red is
          down. Click any cell to analyze.
        </p>
      </div>
      <SectorHeatmap onAnalyze={handleAnalyze} />
    </div>
  );
}
