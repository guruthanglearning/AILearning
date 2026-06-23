"use client";

import { useState } from "react";

import { getCorrelation, type CorrelationResult } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";

const PERIODS = ["1mo", "3mo", "6mo", "1y"] as const;
const MAX_SYMBOLS = 10;

function corrBg(v: number): string {
  if (v >=  0.7) return "bg-emerald-800";
  if (v >=  0.4) return "bg-emerald-900/70";
  if (v >=  0.1) return "bg-emerald-950/50";
  if (v >= -0.1) return "bg-gray-800";
  if (v >= -0.4) return "bg-red-950/50";
  if (v >= -0.7) return "bg-red-900/70";
  return "bg-red-800";
}

function corrText(v: number): string {
  if (Math.abs(v) >= 0.4) return "text-white font-medium";
  return "text-gray-400";
}

export default function CorrelationPage() {
  const [input,   setInput]   = useState("");
  const [symbols, setSymbols] = useState<string[]>([]);
  const [period,  setPeriod]  = useState<string>("3mo");
  const [result,  setResult]  = useState<CorrelationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  function addSymbol() {
    const sym = input.trim().toUpperCase();
    if (!sym || symbols.includes(sym) || symbols.length >= MAX_SYMBOLS) return;
    setSymbols((prev) => [...prev, sym]);
    setInput("");
  }

  function removeSymbol(sym: string) {
    setSymbols((prev) => prev.filter((s) => s !== sym));
    setResult(null);
  }

  async function runCorrelation() {
    if (symbols.length < 2) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await getCorrelation(symbols, period);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to compute correlation");
    } finally {
      setLoading(false);
    }
  }

  const syms = result?.symbols ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white mb-1">Correlation Matrix</h1>
        <p className="text-sm text-gray-400">Pearson correlation of daily log-returns across symbols.</p>
      </div>

      {/* Description card */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">What it measures</p>
          <p className="text-gray-300 leading-relaxed">
            Each cell shows the <span className="text-white font-medium">Pearson correlation</span> between the
            daily log-returns of two symbols over the selected period. Values range from
            <span className="text-emerald-400"> +1</span> (move in perfect lockstep) to
            <span className="text-red-400"> −1</span> (move in perfect opposition).
            The diagonal is always 1 — a symbol is perfectly correlated with itself.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">How to read it</p>
          <ul className="space-y-1 text-gray-300 leading-relaxed">
            <li><span className="text-emerald-400 font-medium">≥ 0.7</span> — Strong positive: assets tend to rise and fall together.</li>
            <li><span className="text-gray-400 font-medium">−0.1 to 0.1</span> — Near-zero: little linear relationship.</li>
            <li><span className="text-red-400 font-medium">≤ −0.7</span> — Strong negative: one rises while the other falls.</li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Portfolio use</p>
          <p className="text-gray-300 leading-relaxed">
            Low or negative correlations between holdings reduce overall portfolio volatility —
            diversification only works when assets don&apos;t all move together.
            Use a longer period (6mo, 1y) for structural relationships; shorter periods (1mo, 3mo)
            to capture recent regime shifts.
          </p>
        </div>
      </div>

      {/* Input */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
        <div className="flex gap-2 flex-wrap">
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
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-white text-sm rounded-md transition-colors"
          >
            Add
          </button>

          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => { setPeriod(p); setResult(null); }}
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

          <button
            type="button"
            onClick={runCorrelation}
            disabled={symbols.length < 2 || loading}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium rounded-md transition-colors flex items-center gap-2"
          >
            {loading && <Spinner size="sm" />}
            {loading ? "Computing…" : "Compute"}
          </button>
        </div>

        {symbols.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {symbols.map((sym) => (
              <span
                key={sym}
                className="flex items-center gap-1.5 bg-gray-800 border border-gray-700 text-gray-300 px-2.5 py-1 rounded-full text-xs font-mono"
              >
                {sym}
                <button
                  type="button"
                  onClick={() => removeSymbol(sym)}
                  className="text-gray-500 hover:text-white leading-none"
                >
                  ×
                </button>
              </span>
            ))}
            {symbols.length < 2 && (
              <span className="text-xs text-gray-600 self-center">Add at least 2 symbols.</span>
            )}
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-4 py-3">{error}</p>
      )}

      {/* Matrix */}
      {result && syms.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-300">
              Pearson Correlation — {result.period}
            </h2>
            <span className="text-xs text-gray-600">{syms.length}×{syms.length} matrix</span>
          </div>
          <div className="p-4 overflow-x-auto">
            <table className="border-collapse text-center text-sm">
              <thead>
                <tr>
                  <th className="w-16 h-10" />
                  {syms.map((s) => (
                    <th key={s} className="w-16 h-10 px-2 font-mono text-xs text-gray-400 font-medium">
                      {s}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {syms.map((row) => (
                  <tr key={row}>
                    <td className="pr-2 text-right font-mono text-xs text-gray-400 font-medium">{row}</td>
                    {syms.map((col) => {
                      const v = result.matrix[row]?.[col] ?? null;
                      const isDiag = row === col;
                      return (
                        <td
                          key={col}
                          className={`w-16 h-12 text-xs rounded m-0.5 ${
                            isDiag
                              ? "bg-gray-700 text-gray-400"
                              : v != null
                                ? `${corrBg(v)} ${corrText(v)}`
                                : "bg-gray-800 text-gray-600"
                          }`}
                        >
                          {isDiag ? "—" : v != null ? v.toFixed(2) : "N/A"}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="px-4 pb-4 flex items-center gap-3 text-xs text-gray-500">
            <span>Low</span>
            <div className="flex gap-0.5">
              {[-0.9, -0.6, -0.3, 0, 0.3, 0.6, 0.9].map((v) => (
                <div
                  key={v}
                  className={`w-6 h-4 rounded-sm ${corrBg(v)}`}
                  title={v.toFixed(1)}
                />
              ))}
            </div>
            <span>High</span>
            <span className="ml-4 text-gray-600">Green = positive · Red = negative · Gray = uncorrelated</span>
          </div>
        </div>
      )}

      {!result && !loading && symbols.length >= 2 && (
        <p className="text-sm text-gray-500 text-center py-6">Click Compute to run the correlation.</p>
      )}
    </div>
  );
}
