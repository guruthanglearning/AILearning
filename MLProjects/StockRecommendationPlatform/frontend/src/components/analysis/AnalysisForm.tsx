"use client";

import { useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import type { AnalysisRunRequest } from "@/types/api";

interface AnalysisFormProps {
  onSubmit: (req: AnalysisRunRequest) => void;
  isLoading: boolean;
  defaultSymbol?: string;
}

export function AnalysisForm({ onSubmit, isLoading, defaultSymbol = "" }: AnalysisFormProps) {
  const [symbol, setSymbol] = useState(defaultSymbol.toUpperCase());
  const [portfolioValue, setPortfolioValue] = useState("");
  const [maxRisk, setMaxRisk] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol.trim()) return;
    onSubmit({
      symbol: symbol.trim().toUpperCase(),
      portfolio_value_usd: portfolioValue ? Number(portfolioValue) : undefined,
      max_risk_per_trade_pct: maxRisk ? Number(maxRisk) : undefined,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4"
    >
      <h1 className="text-lg font-semibold text-white">Analyze Symbol</h1>
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Symbol *</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="AAPL"
            maxLength={10}
            required
            className="w-28 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono uppercase"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Portfolio Value ($)</label>
          <input
            type="number"
            value={portfolioValue}
            onChange={(e) => setPortfolioValue(e.target.value)}
            placeholder="100000"
            min={0}
            className="w-36 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Max Risk % (0.1–10)</label>
          <input
            type="number"
            value={maxRisk}
            onChange={(e) => setMaxRisk(e.target.value)}
            placeholder="2.0"
            min={0.1}
            max={10}
            step={0.1}
            className="w-28 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <button
          type="submit"
          disabled={!symbol.trim() || isLoading}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-md transition-colors"
        >
          {isLoading && <Spinner size="sm" />}
          {isLoading ? "Analyzing…" : "Run Analysis"}
        </button>
      </div>
    </form>
  );
}
