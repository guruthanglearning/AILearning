"use client";

import { useRouter } from "next/navigation";

import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { Spinner } from "@/components/ui/Spinner";
import { useListWatchlistSymbols, useRemoveWatchlistSymbol } from "@/hooks/useWatchlists";

export function WatchlistSymbolList({ watchlistId }: { watchlistId: string }) {
  const { data, isLoading } = useListWatchlistSymbols(watchlistId, true);
  const remove = useRemoveWatchlistSymbol(watchlistId);
  const router = useRouter();

  if (isLoading) return <Spinner size="sm" />;
  if (!data?.length) return <p className="text-xs text-gray-500">No symbols yet.</p>;

  return (
    <div className="space-y-1 mt-2">
      {data.map((sym) => (
        <div
          key={sym.symbol}
          className="flex items-center gap-3 text-sm text-gray-300 py-1"
        >
          <span className="font-mono text-white font-medium w-16 shrink-0">{sym.symbol}</span>
          <span className="text-xs text-gray-500 flex-1 truncate">{sym.note ?? ""}</span>
          <button
            type="button"
            onClick={() => router.push(`/?symbol=${sym.symbol}`)}
            className="text-xs text-indigo-400 hover:text-indigo-300 shrink-0"
          >
            Analyze →
          </button>
          <ConfirmButton
            onConfirm={() => remove.mutate(sym.symbol)}
            isLoading={remove.isPending}
            label="Remove"
          />
        </div>
      ))}
    </div>
  );
}
