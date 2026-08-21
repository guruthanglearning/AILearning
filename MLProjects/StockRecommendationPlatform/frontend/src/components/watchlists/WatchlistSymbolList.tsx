"use client";

import { useRouter } from "next/navigation";

import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { Spinner } from "@/components/ui/Spinner";
import { useAnalysisHistory } from "@/hooks/useAnalysis";
import { useListWatchlistSymbols, useRemoveWatchlistSymbol } from "@/hooks/useWatchlists";
import type { WatchlistSymbolResponse } from "@/types/api";

function WatchlistSymbolRow({
  sym,
  onRemove,
  removing,
}: {
  sym: WatchlistSymbolResponse;
  onRemove: () => void;
  removing: boolean;
}) {
  const router = useRouter();
  const { data: history, isLoading } = useAnalysisHistory(sym.symbol, 1);
  const latestRun = history?.[0];

  return (
    <div className="flex items-center gap-3 text-sm text-gray-300 py-1">
      <span className="font-mono text-white font-medium w-16 shrink-0">{sym.symbol}</span>
      <span className="text-xs text-gray-500 flex-1 truncate">{sym.note ?? ""}</span>
      <button
        type="button"
        onClick={() => router.push(`/?symbol=${sym.symbol}`)}
        className="text-xs text-indigo-400 hover:text-indigo-300 shrink-0"
      >
        Analyze →
      </button>
      {!isLoading && latestRun && (
        <button
          type="button"
          onClick={() => router.push(`/?run_id=${latestRun.run_id}`)}
          className="text-xs text-emerald-400 hover:text-emerald-300 shrink-0"
          title={`View the report from ${new Date(latestRun.started_at).toLocaleString()}`}
        >
          View →
        </button>
      )}
      <ConfirmButton onConfirm={onRemove} isLoading={removing} label="Remove" />
    </div>
  );
}

export function WatchlistSymbolList({ watchlistId }: { watchlistId: string }) {
  const { data, isLoading } = useListWatchlistSymbols(watchlistId, true);
  const remove = useRemoveWatchlistSymbol(watchlistId);

  if (isLoading) return <Spinner size="sm" />;
  if (!data?.length) return <p className="text-xs text-gray-500">No symbols yet.</p>;

  return (
    <div className="space-y-1 mt-2">
      {data.map((sym) => (
        <WatchlistSymbolRow
          key={sym.symbol}
          sym={sym}
          onRemove={() => remove.mutate(sym.symbol)}
          removing={remove.isPending}
        />
      ))}
    </div>
  );
}
