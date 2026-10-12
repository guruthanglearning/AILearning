"use client";

import { useRouter } from "next/navigation";

import { ValueGrid } from "@/components/value/ValueGrid";

export default function ValuePage() {
  const router = useRouter();

  function handleAnalyze(symbol: string) {
    router.push(`/?symbol=${encodeURIComponent(symbol)}`);
  }

  return (
    <div className="space-y-4">
      <ValueGrid onAnalyze={handleAnalyze} />
    </div>
  );
}
