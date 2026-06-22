"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getPriceHistory } from "@/lib/api";
import { computeMACD, computeRSI } from "@/lib/indicators";

const PERIODS = ["1mo", "3mo", "6mo", "1y"] as const;
type Period = (typeof PERIODS)[number];

interface ChartPoint {
  date: string;
  close: number;
  rsi: number | null;
  macd: number | null;
  macdSignal: number | null;
  macdHist: number | null;
}

function fmtDate(s: string): string {
  return new Date(s).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function SectionLabel({ text }: { text: string }) {
  return (
    <p className="text-[10px] text-gray-600 uppercase tracking-wider mb-1 mt-3 first:mt-0">
      {text}
    </p>
  );
}

export function TechnicalChartDrawer({
  symbol,
  onClose,
}: {
  symbol: string;
  onClose: () => void;
}) {
  const [period, setPeriod] = useState<Period>("3mo");
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getPriceHistory(symbol, period)
      .then((r) => {
        const bars = r.data.filter((b) => b.close != null);
        const closes = bars.map((b) => b.close!);
        const rsiValues = computeRSI(closes);
        const { macd, signal, histogram } = computeMACD(closes);
        setChartData(
          bars.map((b, i) => ({
            date: b.date,
            close: b.close!,
            rsi: rsiValues[i] as number | null,
            macd: macd[i] as number | null,
            macdSignal: signal[i] as number | null,
            macdHist: histogram[i] as number | null,
          })),
        );
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Failed to load chart"),
      )
      .finally(() => setLoading(false));
  }, [symbol, period]);

  const closes = chartData.map((d) => d.close);
  const trending =
    closes.length >= 2 ? closes[closes.length - 1] >= closes[0] : true;
  const priceColor = trending ? "#34d399" : "#f87171";

  const step = Math.max(1, Math.floor(chartData.length / 6));
  const xFmt = (_: string, i: number) =>
    i % step === 0 ? fmtDate(chartData[i]?.date ?? "") : "";

  const tooltipStyle = {
    background: "#111827",
    border: "1px solid #374151",
    borderRadius: 6,
    fontSize: 11,
    color: "#e5e7eb",
  };

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
    <div
      className="bg-gray-900 border border-indigo-900/60 rounded-xl shadow-2xl p-4 space-y-1 w-full max-w-3xl max-h-[88vh] overflow-y-auto"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm font-bold text-white font-mono">{symbol}</span>
          <span className="text-xs text-gray-500">Technical Chart</span>
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p}
                type="button"
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
        <button
          type="button"
          onClick={onClose}
          className="text-gray-600 hover:text-gray-300 transition-colors text-sm leading-none px-2 py-1 rounded hover:bg-gray-800"
        >
          ✕
        </button>
      </div>

      {loading && (
        <div className="h-96 flex items-center justify-center text-xs text-gray-500">
          Loading chart…
        </div>
      )}
      {error && (
        <div className="h-96 flex items-center justify-center text-xs text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && chartData.length === 0 && (
        <div className="h-40 flex items-center justify-center text-xs text-gray-600">
          No chart data available
        </div>
      )}

      {!loading && !error && chartData.length > 0 && (
        <>
          {/* Price */}
          <SectionLabel text="Price" />
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart
              data={chartData}
              syncId="tech-chart"
              margin={{ top: 4, right: 4, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="priceGradDrawer" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={priceColor} stopOpacity={0.25} />
                  <stop offset="95%" stopColor={priceColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                stroke="#1f2937"
                strokeDasharray="3 3"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tickFormatter={xFmt}
                tick={{ fill: "#6b7280", fontSize: 9 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                domain={["auto", "auto"]}
                tickFormatter={(v) => `$${Number(v).toFixed(0)}`}
                tick={{ fill: "#6b7280", fontSize: 9 }}
                tickLine={false}
                axisLine={false}
                width={44}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(v: unknown) => [`$${Number(v).toFixed(2)}`, "Close"]}
                labelFormatter={(l) => fmtDate(l as string)}
              />
              <Area
                type="monotone"
                dataKey="close"
                stroke={priceColor}
                strokeWidth={1.5}
                fill="url(#priceGradDrawer)"
                dot={false}
                activeDot={{ r: 3, fill: priceColor }}
              />
            </AreaChart>
          </ResponsiveContainer>

          {/* RSI */}
          <SectionLabel text="RSI (14) — overbought >70 · oversold <30" />
          <ResponsiveContainer width="100%" height={90}>
            <ComposedChart
              data={chartData}
              syncId="tech-chart"
              margin={{ top: 2, right: 4, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                stroke="#1f2937"
                strokeDasharray="3 3"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tickFormatter={xFmt}
                tick={{ fill: "#6b7280", fontSize: 9 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                domain={[0, 100]}
                ticks={[30, 50, 70]}
                tick={{ fill: "#6b7280", fontSize: 9 }}
                tickLine={false}
                axisLine={false}
                width={28}
              />
              <ReferenceLine
                y={70}
                stroke="#ef4444"
                strokeDasharray="3 3"
                strokeOpacity={0.5}
              />
              <ReferenceLine
                y={30}
                stroke="#22c55e"
                strokeDasharray="3 3"
                strokeOpacity={0.5}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(v: unknown) => [
                  v != null ? Number(v).toFixed(1) : "--",
                  "RSI",
                ]}
                labelFormatter={(l) => fmtDate(l as string)}
              />
              <Line
                type="monotone"
                dataKey="rsi"
                stroke="#a78bfa"
                strokeWidth={1.5}
                dot={false}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>

          {/* MACD */}
          <SectionLabel text="MACD (6 / 13 / 9) — histogram · MACD line · signal line" />
          <ResponsiveContainer width="100%" height={90}>
            <ComposedChart
              data={chartData}
              syncId="tech-chart"
              margin={{ top: 2, right: 4, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                stroke="#1f2937"
                strokeDasharray="3 3"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tickFormatter={xFmt}
                tick={{ fill: "#6b7280", fontSize: 9 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fill: "#6b7280", fontSize: 9 }}
                tickLine={false}
                axisLine={false}
                width={44}
                tickFormatter={(v) => Number(v).toFixed(1)}
              />
              <ReferenceLine y={0} stroke="#4b5563" />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(v: unknown, name: unknown) => [
                  v != null ? Number(v).toFixed(3) : "--",
                  String(name),
                ]}
                labelFormatter={(l) => fmtDate(l as string)}
              />
              <Bar
                dataKey="macdHist"
                name="Histogram"
                fill="#6366f1"
                opacity={0.65}
              />
              <Line
                type="monotone"
                dataKey="macd"
                name="MACD"
                stroke="#f59e0b"
                strokeWidth={1.5}
                dot={false}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="macdSignal"
                name="Signal"
                stroke="#f87171"
                strokeWidth={1}
                dot={false}
                connectNulls={false}
                strokeDasharray="4 2"
              />
            </ComposedChart>
          </ResponsiveContainer>

          <p className="text-[10px] text-gray-700 italic pt-1">
            Price history via Yahoo Finance · MACD(6,13,9) computed client-side · Not investment advice.
          </p>
        </>
      )}
    </div>
    </div>
  );
}
