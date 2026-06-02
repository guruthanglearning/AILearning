"use client";

import { useRouter } from "next/navigation";

import { MomentumGrid } from "@/components/momentum/MomentumGrid";

export default function MomentumPage() {
  const router = useRouter();

  function handleAnalyze(symbol: string) {
    router.push(`/?symbol=${encodeURIComponent(symbol)}`);
  }

  return (
    <div className="space-y-4">
      <MomentumGrid onAnalyze={handleAnalyze} />
    </div>
  );
}
