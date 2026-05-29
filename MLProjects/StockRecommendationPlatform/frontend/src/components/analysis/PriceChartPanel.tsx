"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getPriceHistory } from "@/lib/api";
import type { PriceBar } from "@/types/api";

const PERIODS = ["1mo", "3mo", "6mo", "1y"] as const;
type Period = typeof PERIODS[number];

function fmtDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function fmtPrice(v: number): string {
  return `$${v.toFixed(2)}`;
}

interface TooltipPayload {
  value: number;
  payload: PriceBar;
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) {
  if (!active || !payload?.length) return null;
  const bar = payload[0].payload;
  return (
    <div className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-xs space-y-0.5">
      <p className="text-gray-400">{bar.date}</p>
      <p className="text-white font-mono font-semibold">{fmtPrice(bar.close ?? 0)}</p>
      {bar.volume != null && (
        <p className="text-gray-500">Vol: {(bar.volume / 1e6).toFixed(1)}M</p>
      )}
    </div>
  );
}

export function PriceChartPanel({ symbol }: { symbol: string }) {
  const [period, setPeriod] = useState<Period>("3mo");
  const [data, setData] = useState<PriceBar[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    getPriceHistory(symbol, period)
      .then(r => setData(r.data.filter(b => b.close != null)))
      .catch(e => setError(e instanceof Error ? e.message : "Failed to load chart"))
      .finally(() => setLoading(false));
  }, [symbol, period]);

  const closes = data.map(b => b.close!);
  const minClose = closes.length ? Math.min(...closes) : 0;
  const maxClose = closes.length ? Math.max(...closes) : 0;
  const first = closes[0] ?? 0;
  const last  = closes[closes.length - 1] ?? 0;
  const trending = last >= first;
  const strokeColor = trending ? "#34d399" : "#f87171";
  const gradStart   = trending ? "#34d39940" : "#f8717140";

  // Thin the data for x-axis labels to avoid crowding
  const labelStep = Math.max(1, Math.floor(data.length / 6));
  const tickFormatter = (_: string, idx: number) =>
    idx % labelStep === 0 ? fmtDate(data[idx]?.date ?? "") : "";

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-sm font-medium text-gray-400">Price History</h2>
        <div className="flex gap-1">
          {PERIODS.map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-2 py-0.5 text-xs rounded transition-colors ${
                period === p
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        {loading && (
          <div className="h-44 flex items-center justify-center text-xs text-gray-500">
            Loading chart…
          </div>
        )}
        {error && (
          <div className="h-44 flex items-center justify-center text-xs text-red-400">
            {error}
          </div>
        )}
        {!loading && !error && data.length === 0 && (
          <div className="h-44 flex items-center justify-center text-xs text-gray-500">
            No price data available
          </div>
        )}
        {!loading && !error && data.length > 0 && (
          <>
            {/* Mini stats bar */}
            <div className="flex gap-4 mb-3 text-xs">
              <span className="text-gray-500">
                Range: <span className="text-gray-300 font-mono">{fmtPrice(minClose)} – {fmtPrice(maxClose)}</span>
              </span>
              <span className={trending ? "text-green-400" : "text-red-400"}>
                {trending ? "↑" : "↓"} {(((last - first) / first) * 100).toFixed(1)}% over period
              </span>
            </div>

            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={gradStart} stopOpacity={1} />
                    <stop offset="95%" stopColor={gradStart} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={tickFormatter}
                  tick={{ fill: "#6b7280", fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  tickFormatter={v => `$${Number(v).toFixed(0)}`}
                  tick={{ fill: "#6b7280", fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  width={48}
                />
                <Tooltip content={<ChartTooltip />} />
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke={strokeColor}
                  strokeWidth={1.5}
                  fill="url(#priceGrad)"
                  dot={false}
                  activeDot={{ r: 4, fill: strokeColor, stroke: "#111827" }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </>
        )}
      </div>
    </div>
  );
}
