"use client";

import { useEffect, useRef, useState } from "react";

import { getPriceHistory } from "@/lib/api";

export interface PriceBar { date: string; close: number }

const CONCURRENCY = 4;

export function usePriceHistories(
  symbols: string[],
  period: string,
): { data: Map<string, PriceBar[]>; loading: boolean; error: string | null } {
  const [data,    setData]    = useState<Map<string, PriceBar[]>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const prevKey = useRef("");

  useEffect(() => {
    const key = symbols.join(",") + "|" + period;
    if (!symbols.length || key === prevKey.current) return;
    prevKey.current = key;

    setLoading(true);
    setError(null);
    setData(new Map());

    let idx = 0;
    const next = new Map<string, PriceBar[]>();

    const worker = async () => {
      while (true) {
        const i = idx++;
        if (i >= symbols.length) break;
        const sym = symbols[i];
        try {
          const r = await getPriceHistory(sym, period);
          const bars: PriceBar[] = r.data
            .filter((b) => b.close != null)
            .map((b) => ({ date: b.date, close: b.close! }));
          if (bars.length) next.set(sym, bars);
        } catch {
          // skip failed
        }
      }
    };

    Promise.all(
      Array.from({ length: Math.min(CONCURRENCY, symbols.length) }, worker),
    )
      .then(() => setData(new Map(next)))
      .catch((e) => setError(e instanceof Error ? e.message : "Fetch failed"))
      .finally(() => setLoading(false));
  }, [symbols, period]); // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error };
}
