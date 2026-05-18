"use client";

import { useState } from "react";

import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { useDeleteWatchlist } from "@/hooks/useWatchlists";
import type { WatchlistResponse } from "@/types/api";

import { AddSymbolForm } from "./AddSymbolForm";
import { WatchlistSymbolList } from "./WatchlistSymbolList";

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
        </div>
      )}
    </div>
  );
}
