"use client";

import { useState } from "react";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Spinner } from "@/components/ui/Spinner";
import { useCreateAlert } from "@/hooks/useAlerts";
import type { AlertCondition } from "@/types/api";

const VERDICT_OPTIONS = ["stock", "options", "no_trade", "insufficient_data"];

export function CreateAlertForm() {
  const [symbol, setSymbol] = useState("");
  const [condition, setCondition] = useState<AlertCondition>("price_above");
  const [thresholdValue, setThresholdValue] = useState("");
  const [thresholdVerdict, setThresholdVerdict] = useState("stock");
  const mutation = useCreateAlert();

  const isPriceCond = condition === "price_above" || condition === "price_below";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol.trim()) return;
    await mutation.mutateAsync({
      symbol: symbol.trim().toUpperCase(),
      condition,
      threshold_value: isPriceCond && thresholdValue ? Number(thresholdValue) : null,
      threshold_verdict: !isPriceCond ? thresholdVerdict : null,
    });
    setSymbol("");
    setThresholdValue("");
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Symbol *</label>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="AAPL"
            maxLength={10}
            className="w-24 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono uppercase"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Condition *</label>
          <select
            value={condition}
            onChange={(e) => setCondition(e.target.value as AlertCondition)}
            className="bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="price_above">Price Above</option>
            <option value="price_below">Price Below</option>
            <option value="verdict_changes_to">Verdict Changes To</option>
          </select>
        </div>
        {isPriceCond ? (
          <div>
            <label className="block text-xs text-gray-400 mb-1">Threshold Price *</label>
            <input
              type="number"
              value={thresholdValue}
              onChange={(e) => setThresholdValue(e.target.value)}
              placeholder="200.00"
              min={0}
              step={0.01}
              className="w-32 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        ) : (
          <div>
            <label className="block text-xs text-gray-400 mb-1">Verdict *</label>
            <select
              value={thresholdVerdict}
              onChange={(e) => setThresholdVerdict(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              {VERDICT_OPTIONS.map((v) => (
                <option key={v} value={v}>
                  {v.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>
        )}
        <button
          type="submit"
          disabled={!symbol.trim() || mutation.isPending}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
        >
          {mutation.isPending && <Spinner size="sm" />}
          Create Alert
        </button>
      </div>
      {mutation.error && <ErrorMessage error={mutation.error as Error} />}
    </form>
  );
}
