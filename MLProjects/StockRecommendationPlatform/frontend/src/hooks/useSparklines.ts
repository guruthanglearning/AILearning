"use client";

import { useEffect, useRef, useState } from "react";

import { getPriceHistory } from "@/lib/api";

const CONCURRENCY = 8;

export function useSparklines(
  symbols: string[],
  enabled: boolean,
): Map<string, number[]> {
  const [data, setData] = useState<Map<string, number[]>>(new Map());
  const fetchedRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!enabled || symbols.length === 0) return;
    const toFetch = symbols.filter((s) => !fetchedRef.current.has(s));
    if (toFetch.length === 0) return;
    toFetch.forEach((s) => fetchedRef.current.add(s));

    let idx = 0;

    const runWorker = async () => {
      while (true) {
        const i = idx++;
        if (i >= toFetch.length) break;
        const sym = toFetch[i];
        try {
          const r = await getPriceHistory(sym, "1mo");
          const closes = r.data
            .filter((b) => b.close != null)
            .map((b) => b.close!);
          if (closes.length >= 2) {
            setData((prev) => {
              const next = new Map(prev);
              next.set(sym, closes);
              return next;
            });
          }
        } catch {
          // silently skip failed symbols
        }
      }
    };

    const workers = Array.from(
      { length: Math.min(CONCURRENCY, toFetch.length) },
      runWorker,
    );
    Promise.all(workers).catch(() => {});
  }, [symbols, enabled]);

  return data;
}
