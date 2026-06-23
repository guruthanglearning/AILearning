"use client";

import { useState } from "react";

import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { Spinner } from "@/components/ui/Spinner";
import { useBatchJob } from "@/hooks/useBatchJob";
import { useDeleteWatchlist, useListWatchlistSymbols } from "@/hooks/useWatchlists";
import type { WatchlistResponse } from "@/types/api";

import { AddSymbolForm } from "./AddSymbolForm";
import { WatchlistSymbolList } from "./WatchlistSymbolList";

function BatchPanel({ watchlistId, watchlistName }: { watchlistId: string; watchlistName: string }) {
  const { data: symbolRows } = useListWatchlistSymbols(watchlistId, true);
  const { job, loading, error, start, reset } = useBatchJob();

  const symbols = (symbolRows ?? []).map((s) => s.symbol);

  if (!symbols.length) return null;

  const handleAnalyzeAll = () => {
    start(symbols, `wl-${watchlistId}`);
  };

  const statusLine = () => {
    if (!job) return null;
    if (job.status === "pending" || job.status === "running") {
      return (
        <span className="flex items-center gap-1.5 text-xs text-gray-400">
          <Spinner size="sm" />
          {job.completed_symbols}/{job.total_symbols} analyzed…
        </span>
      );
    }
    if (job.status === "complete" || job.status === "partial") {
      const counts = { stock: 0, options: 0, no_trade: 0, insufficient_data: 0 } as Record<string, number>;
      job.results.forEach((r) => { if (r.verdict) counts[r.verdict] = (counts[r.verdict] ?? 0) + 1; });
      const parts = [
        counts.stock        && `${counts.stock} Stock`,
        counts.options      && `${counts.options} Options`,
        counts.no_trade     && `${counts.no_trade} No Trade`,
        counts.insufficient_data && `${counts.insufficient_data} N/A`,
      ].filter(Boolean);
      return (
        <span className="flex items-center gap-2 text-xs">
          <span className="text-green-400">Done</span>
          <span className="text-gray-500">{parts.join(" · ")}</span>
          <button type="button" onClick={reset} className="text-gray-600 hover:text-gray-400 text-xs underline">
            Clear
          </button>
        </span>
      );
    }
    if (job.status === "failed") {
      return (
        <span className="text-xs text-red-400">
          Failed
          <button type="button" onClick={reset} className="ml-2 text-gray-600 hover:text-gray-400 underline">
            Clear
          </button>
        </span>
      );
    }
    return null;
  };

  return (
    <div className="flex items-center gap-3 mt-3 pt-3 border-t border-gray-800">
      <button
        type="button"
        onClick={handleAnalyzeAll}
        disabled={loading}
        className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-700/60 hover:bg-indigo-600/60 disabled:opacity-50 text-indigo-300 text-xs font-medium rounded-md transition-colors"
      >
        {loading && <Spinner size="sm" />}
        Analyze All ({symbols.length})
      </button>
      {error && <span className="text-xs text-red-400">{error}</span>}
      {statusLine()}
    </div>
  );
}

export function WatchlistCard({ watchlist }: { watchlist: WatchlistResponse }) {
  const [expanded, setExpanded] = useState(false);
  const remove = useDeleteWatchlist();

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3">
        <button
          type="button"
          onClick={() => setExpanded((o) => !o)}
          className="flex-1 flex items-center gap-3 text-left"
        >
          <span className={`text-gray-500 transition-transform ${expanded ? "rotate-90" : ""}`}>
            ▶
          </span>
          <span className="font-medium text-white">{watchlist.name}</span>
          {watchlist.description && (
            <span className="text-xs text-gray-500 truncate">{watchlist.description}</span>
          )}
          <span className="ml-auto text-xs text-gray-500">
            {watchlist.symbol_count} symbol{watchlist.symbol_count !== 1 ? "s" : ""}
          </span>
        </button>
        <ConfirmButton
          onConfirm={() => remove.mutate(watchlist.id)}
          isLoading={remove.isPending}
          label="Delete"
        />
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-800">
          <WatchlistSymbolList watchlistId={watchlist.id} />
          <AddSymbolForm watchlistId={watchlist.id} />
          <BatchPanel watchlistId={watchlist.id} watchlistName={watchlist.name} />
        </div>
      )}
    </div>
  );
}
