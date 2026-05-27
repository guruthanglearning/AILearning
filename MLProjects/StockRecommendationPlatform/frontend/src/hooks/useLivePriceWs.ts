"use client";

import { useEffect, useRef, useState } from "react";

export interface WsPrice {
  type: "price";
  symbol: string;
  price: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  volume: number | null;
  vwap: number | null;
  ts: number | null;
}

const API_WS =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010")
    .replace(/^https/, "wss")
    .replace(/^http/, "ws");

export function useLivePriceWs(symbol: string | null): {
  data: WsPrice | null;
  connected: boolean;
} {
  const [data, setData] = useState<WsPrice | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!symbol) return;

    const url = `${API_WS}/v1/ws/quote/${encodeURIComponent(symbol)}`;
    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch {
      return;
    }
    wsRef.current = ws;

    ws.onopen  = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data as string) as WsPrice;
        if (msg.type === "price") setData(msg);
      } catch { /* ignore malformed */ }
    };

    return () => {
      ws.close();
      setConnected(false);
    };
  }, [symbol]);

  return { data, connected };
}
