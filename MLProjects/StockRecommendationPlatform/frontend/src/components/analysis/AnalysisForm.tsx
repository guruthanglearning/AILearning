"use client";

import { useEffect, useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { useUserSettings } from "@/hooks/useUserSettings";
import { getClaudeUsage } from "@/lib/api";
import type { AnalysisRunRequest, ClaudeUsage } from "@/types/api";

interface AnalysisFormProps {
  onSubmit: (req: AnalysisRunRequest) => void;
  isLoading: boolean;
  defaultSymbol?: string;
}

const MODEL_OPTIONS = [
  {
    id: "claude-haiku-4-5-20251001",
    label: "Haiku 4.5",
    tier: "Dev / Fast",
    cost: "~$0.004",
    color: "text-emerald-400",
    border: "border-emerald-700/50",
    activeBg: "bg-emerald-900/40",
    activeBorder: "border-emerald-500",
  },
  {
    id: "claude-sonnet-4-6",
    label: "Sonnet 4.6",
    tier: "Balanced",
    cost: "~$0.02",
    color: "text-sky-400",
    border: "border-sky-700/50",
    activeBg: "bg-sky-900/40",
    activeBorder: "border-sky-500",
  },
  {
    id: "claude-opus-4-8",
    label: "Opus 4.8",
    tier: "Professional",
    cost: "~$0.05",
    color: "text-violet-400",
    border: "border-violet-700/50",
    activeBg: "bg-violet-900/40",
    activeBorder: "border-violet-500",
  },
] as const;

const DEFAULT_MODEL = "claude-opus-4-8";
const STORAGE_KEY = "claude_selected_model";

export function AnalysisForm({ onSubmit, isLoading, defaultSymbol = "" }: AnalysisFormProps) {
  const { settings } = useUserSettings();

  const [symbol, setSymbol] = useState(defaultSymbol.toUpperCase());
  const [model,  setModel]  = useState<string>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(STORAGE_KEY) ?? DEFAULT_MODEL;
    }
    return DEFAULT_MODEL;
  });
  const [usage, setUsage] = useState<ClaudeUsage | null>(null);

  // Apply server-side preferred model when settings load (takes precedence over localStorage)
  useEffect(() => {
    if (settings.preferred_claude_model) {
      setModel(settings.preferred_claude_model);
    }
  }, [settings.preferred_claude_model]);

  // Apply server-side default symbol only when no explicit defaultSymbol was provided
  useEffect(() => {
    if (!defaultSymbol && settings.default_symbol) {
      setSymbol(settings.default_symbol);
    }
  }, [defaultSymbol, settings.default_symbol]);

  useEffect(() => {
    getClaudeUsage().then(setUsage).catch(() => {});
  }, []);

  function handleModelChange(id: string) {
    setModel(id);
    localStorage.setItem(STORAGE_KEY, id);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol.trim()) return;
    onSubmit({ symbol: symbol.trim().toUpperCase(), claude_model: model });
  }

  const sessionCost = usage?.total_estimated_cost_usd ?? 0;
  const sessionCount = usage?.total_analyses ?? 0;

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4"
    >
      <h1 className="text-lg font-semibold text-white">Analyze Symbol</h1>

      {/* Symbol input row */}
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

        <button
          type="submit"
          disabled={!symbol.trim() || isLoading}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-md transition-colors"
        >
          {isLoading && <Spinner size="sm" />}
          {isLoading ? "Analyzing…" : "Run Analysis"}
        </button>

        {/* Session spend badge */}
        {sessionCount > 0 && (
          <div className="ml-auto flex items-center gap-1.5 text-xs text-gray-500 bg-gray-800/60 border border-gray-700/50 rounded-md px-2.5 py-1.5">
            <span className="text-gray-600">Session</span>
            <span className="font-mono text-gray-300">${sessionCost.toFixed(4)}</span>
            <span className="text-gray-600">· {sessionCount} {sessionCount === 1 ? "run" : "runs"}</span>
          </div>
        )}
      </div>

      {/* Model selector */}
      <div>
        <label className="block text-xs text-gray-400 mb-2">
          AI Model
          <span className="ml-2 text-gray-600 font-normal">— cost per analysis</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {MODEL_OPTIONS.map((m) => {
            const active = model === m.id;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => handleModelChange(m.id)}
                className={`flex flex-col px-3 py-2 rounded-lg border text-left transition-all ${
                  active
                    ? `${m.activeBg} ${m.activeBorder}`
                    : `bg-gray-800/40 ${m.border} hover:bg-gray-800`
                }`}
              >
                <span className={`text-xs font-semibold ${active ? m.color : "text-gray-300"}`}>
                  {m.label}
                </span>
                <span className={`text-[10px] ${active ? "text-gray-400" : "text-gray-600"}`}>
                  {m.tier} · {m.cost}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </form>
  );
}
