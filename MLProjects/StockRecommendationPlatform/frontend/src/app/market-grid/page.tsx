"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";

const MarketGrid = dynamic(
  () => import("@/components/market/MarketGrid").then((m) => m.MarketGrid),
  { ssr: false },
);

export default function MarketGridPage() {
  const router = useRouter();

  function handleAnalyze(symbol: string) {
    router.push(`/?symbol=${encodeURIComponent(symbol)}`);
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-white">Market Grid</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Live quotes for your tracked symbols — click any ticker to run a full analysis.
        </p>
      </div>
      <MarketGrid onAnalyze={handleAnalyze} />
    </div>
  );
}
