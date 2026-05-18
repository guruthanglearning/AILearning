"use client";

import { useEffect, useState } from "react";

import { Spinner } from "@/components/ui/Spinner";

const MAX_SECONDS = 45;

export function AnalysisLoader({ symbol, startedAt }: { symbol: string; startedAt: number }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    const id = setInterval(() => {
      const s = Math.floor((Date.now() - startedAt) / 1000);
      setElapsed(s);
      if (s >= MAX_SECONDS) clearInterval(id);
    }, 1000);
    return () => clearInterval(id);
  }, [startedAt]);

  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4 text-gray-400">
      <Spinner size="lg" />
      <p className="text-lg font-medium text-white">Analyzing {symbol}…</p>
      <p className="text-sm">
        {elapsed}s elapsed
        {elapsed < MAX_SECONDS ? ` (up to ${MAX_SECONDS}s)` : " — almost done"}
      </p>
      <p className="text-xs text-gray-600">
        Seven specialist agents are running in parallel
      </p>
    </div>
  );
}
