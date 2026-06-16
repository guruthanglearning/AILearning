"use client";

import { useEffect, useRef, useState } from "react";

export interface LivePriceUpdate {
  price: number;
  ts: number;           // Date.now() when received — used to trigger flash
  prevPrice: number | null; // previous price — determines flash color direction
}

const API_WS =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010")
    .replace(/^https/, "wss")
    .replace(/^http/, "ws");

export function useMarketGridWs(symbols: string[]): {
  livePrices: Record<string, LivePriceUpdate>;
  connected: boolean;
} {
  const [livePrices, setLivePrices] = useState<Record<string, LivePriceUpdate>>({});
  const [connected, setConnected] = useState(false);
  const prevPricesRef = useRef<Record<string, number>>({});
  const symbolKey = symbols.join(",");

  useEffect(() => {
    if (!symbols.length) return;
    const url = `${API_WS}/v1/ws/market-grid?symbols=${encodeURIComponent(symbolKey)}`;
    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch {
      return;
    }

    ws.onopen  = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data as string) as {
          type: string; symbol: string; price: number | null;
        };
        if (msg.type !== "price" || !msg.symbol || msg.price == null) return;
        const sym = msg.symbol;
        const price = msg.price;
        const prevPrice = prevPricesRef.current[sym] ?? null;
        prevPricesRef.current[sym] = price;
        setLivePrices((prev) => ({
          ...prev,
          [sym]: { price, ts: Date.now(), prevPrice },
        }));
      } catch { /* ignore malformed */ }
    };

    return () => {
      ws.close();
      setConnected(false);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbolKey]);

  return { livePrices, connected };
}
