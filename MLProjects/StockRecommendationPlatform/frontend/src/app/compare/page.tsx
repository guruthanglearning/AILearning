"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { computeRSI } from "@/lib/indicators";
import { usePriceHistories, type PriceBar } from "@/hooks/usePriceHistories";
import { Spinner } from "@/components/ui/Spinner";

const COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e", "#8b5cf6"];
const PERIODS = ["1mo", "3mo", "6mo", "1y"] as const;
const MAX_SYMBOLS = 6;

function computeReturn(closes: number[], barCount: number): number | null {
  if (closes.length < barCount + 1) return null;
  const start = closes[closes.length - barCount - 1];
  const end   = closes[closes.length - 1];
  return ((end / start) - 1) * 100;
}

function computeVaR(closes: number[], confidence: number): number | null {
  if (closes.length < 5) return null;
  const logRets: number[] = [];
  for (let i = 1; i < closes.length; i++) logRets.push(Math.log(closes[i] / closes[i - 1]));
  logRets.sort((a, b) => a - b);
  const idx = Math.max(0, Math.floor((1 - confidence) * logRets.length));
  return -logRets[idx] * 100;
}

function buildChartData(
  histories: Map<string, PriceBar[]>,
  symbols: string[],
): Record<string, number | string>[] {
  const allDates = new Set<string>();
  for (const sym of symbols) histories.get(sym)?.forEach((b) => allDates.add(b.date));
  const sorted = Array.from(allDates).sort();

  const firstClose = new Map<string, number>();
  for (const sym of symbols) {
    const bars = histories.get(sym);
    if (bars?.length) firstClose.set(sym, bars[0].close);
  }

  const byDate = new Map<string, Map<string, number>>();
  for (const sym of symbols) {
    const base = firstClose.get(sym);
    if (!base) continue;
    histories.get(sym)?.forEach((b) => {
      if (!byDate.has(b.date)) byDate.set(b.date, new Map());
      byDate.get(b.date)!.set(sym, parseFloat(((b.close / base) * 100).toFixed(2)));
    });
  }

  return sorted.map((date) => {
    const row: Record<string, number | string> = { date };
    byDate.get(date)?.forEach((val, sym) => { row[sym] = val; });
    return row;
  });
}

function fmt(v: number | null, decimals = 2, suffix = ""): string {
  if (v == null) return "--";
  return `${v.toFixed(decimals)}${suffix}`;
}

function PctCell({ v }: { v: number | null }) {
  if (v == null) return <span className="text-gray-600">--</span>;
  return (
    <span className={v >= 0 ? "text-green-400" : "text-red-400"}>
      {v >= 0 ? "+" : ""}{v.toFixed(2)}%
    </span>
  );
}

export default function ComparePage() {
  const [input,   setInput]   = useState("");
  const [symbols, setSymbols] = useState<string[]>([]);
  const [period,  setPeriod]  = useState<string>("3mo");

  const { data: histories, loading, error } = usePriceHistories(symbols, period);

  function addSymbol() {
    const sym = input.trim().toUpperCase();
    if (!sym || symbols.includes(sym) || symbols.length >= MAX_SYMBOLS) return;
    setSymbols((prev) => [...prev, sym]);
    setInput("");
  }

  function removeSymbol(sym: string) {
    setSymbols((prev) => prev.filter((s) => s !== sym));
  }

  const chartData = useMemo(() => buildChartData(histories, symbols), [histories, symbols]);

  const metrics = useMemo(
    () =>
      symbols.map((sym) => {
        const bars   = histories.get(sym) ?? [];
        const closes = bars.map((b) => b.close);
        const rsiArr = closes.length > 14 ? computeRSI(closes) : [];
        return {
          sym,
          lastPrice: closes.at(-1)   ?? null,
          dayPct:    closes.length >= 2 ? ((closes.at(-1)! / closes.at(-2)! - 1) * 100) : null,
          ret1m:     computeReturn(closes, 20),
          ret3m:     computeReturn(closes, 62),
          ret6m:     computeReturn(closes, 124),
          rsi14:     (rsiArr.at(-1) as number | null | undefined) ?? null,
          var95:     computeVaR(closes, 0.95),
          var99:     computeVaR(closes, 0.99),
          bars:      bars.length,
        };
      }),
    [histories, symbols]
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white mb-1">Multi-Symbol Comparison</h1>
        <p className="text-sm text-gray-400">Compare up to {MAX_SYMBOLS} symbols — normalized chart + risk metrics.</p>
      </div>

      {/* Description card */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Normalized chart</p>
          <p className="text-gray-300 leading-relaxed">
            All prices are <span className="text-white font-medium">indexed to 100</span> at the start of the
            selected period, so you can compare relative performance regardless of each stock&apos;s actual price.
            A value of 120 means the stock is up 20% from the period start; 80 means it&apos;s down 20%.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Return &amp; risk metrics</p>
          <ul className="space-y-1 text-gray-300 leading-relaxed">
            <li><span className="text-white font-medium">1M / 3M / 6M%</span> — price return over approx. 20, 62, and 124 trading bars.</li>
            <li><span className="text-white font-medium">RSI(14)</span> — momentum oscillator: above 70 = overbought, below 30 = oversold.</li>
            <li><span className="text-white font-medium">VaR 95% / 99%</span> — daily loss not exceeded 95% / 99% of days, from historical log-returns.</li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">How to use it</p>
          <p className="text-gray-300 leading-relaxed">
            Add 2–{MAX_SYMBOLS} ticker symbols, choose a lookback period, and scan the chart for
            divergence between assets. Pair with the{" "}
            <span className="text-indigo-400">Correlation</span> page to check whether assets
            that look similar in returns also move together day-to-day — two stocks can have the
            same 3M return but very different correlation.
          </p>
        </div>
      </div>

      {/* Symbol input */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && addSymbol()}
            placeholder="AAPL"
            maxLength={10}
            className="w-28 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono uppercase"
          />
          <button
            type="button"
            onClick={addSymbol}
            disabled={!input.trim() || symbols.length >= MAX_SYMBOLS}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium rounded-md transition-colors"
          >
            Add
          </button>

          {/* Period selector */}
          <div className="ml-auto flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                  period === p
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:text-white"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Symbol tags */}
        {symbols.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {symbols.map((sym, i) => (
              <span
                key={sym}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium"
                style={{ backgroundColor: `${COLORS[i]}22`, color: COLORS[i], border: `1px solid ${COLORS[i]}44` }}
              >
                {sym}
                <button
                  type="button"
                  onClick={() => removeSymbol(sym)}
                  className="opacity-60 hover:opacity-100 leading-none"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {loading && (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-4 py-3">{error}</p>
      )}

      {!loading && symbols.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-10">Add two or more symbols to compare.</p>
      )}

      {/* Normalized chart */}
      {!loading && chartData.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-3">Indexed to 100 at period start</p>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: "#6b7280" }}
                tickFormatter={(d: string) => d.slice(5)}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10, fill: "#6b7280" }}
                tickFormatter={(v: number) => `${v.toFixed(0)}`}
                domain={["auto", "auto"]}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: "8px", fontSize: "12px" }}
                formatter={(val, name) => [typeof val === "number" ? val.toFixed(2) : String(val), String(name)]}
              />
              <Legend wrapperStyle={{ fontSize: "12px" }} />
              {symbols.map((sym, i) => (
                <Line
                  key={sym}
                  type="monotone"
                  dataKey={sym}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Metrics table */}
      {!loading && metrics.some((m) => m.bars > 0) && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <h2 className="text-sm font-medium text-gray-300">Metrics</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-right">
              <thead>
                <tr className="text-xs text-gray-500 border-b border-gray-800">
                  <th className="px-4 py-2 text-left">Symbol</th>
                  <th className="px-4 py-2">Price</th>
                  <th className="px-4 py-2">Day%</th>
                  <th className="px-4 py-2">1M%</th>
                  <th className="px-4 py-2">3M%</th>
                  <th className="px-4 py-2">6M%</th>
                  <th className="px-4 py-2">RSI(14)</th>
                  <th className="px-4 py-2">VaR 95%</th>
                  <th className="px-4 py-2">VaR 99%</th>
                  <th className="px-4 py-2 text-right text-gray-500">Bars</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m, i) => (
                  <tr key={m.sym} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="px-4 py-2 text-left">
                      <span
                        className="font-mono font-semibold text-sm px-1.5 py-0.5 rounded"
                        style={{ color: COLORS[i % COLORS.length] }}
                      >
                        {m.sym}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono text-white">{fmt(m.lastPrice)}</td>
                    <td className="px-4 py-2"><PctCell v={m.dayPct} /></td>
                    <td className="px-4 py-2"><PctCell v={m.ret1m} /></td>
                    <td className="px-4 py-2"><PctCell v={m.ret3m} /></td>
                    <td className="px-4 py-2"><PctCell v={m.ret6m} /></td>
                    <td className="px-4 py-2 text-gray-300">{fmt(m.rsi14, 1)}</td>
                    <td className="px-4 py-2 text-amber-400">{fmt(m.var95, 2, "%")}</td>
                    <td className="px-4 py-2 text-red-400">{fmt(m.var99, 2, "%")}</td>
                    <td className="px-4 py-2 text-gray-600 text-xs">{m.bars}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="px-4 py-2 text-xs text-gray-600">
            VaR = daily log-return percentile loss at given confidence. 1M/3M/6M use approx. 21/63/126 trading bars.
          </p>
        </div>
      )}
    </div>
  );
}
