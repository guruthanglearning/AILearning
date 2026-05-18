"use client";

import { useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { ApiError } from "@/lib/api";
import { useAddWatchlistSymbol } from "@/hooks/useWatchlists";

export function AddSymbolForm({ watchlistId }: { watchlistId: string }) {
  const [symbol, setSymbol] = useState("");
  const [note, setNote] = useState("");
  const [conflict, setConflict] = useState(false);
  const mutation = useAddWatchlistSymbol(watchlistId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setConflict(false);
    if (!symbol.trim()) return;
    try {
      await mutation.mutateAsync({ symbol: symbol.trim().toUpperCase(), note: note.trim() || null });
      setSymbol("");
      setNote("");
    } catch (err) {
      if (err instanceof ApiError && err.statusCode === 409) setConflict(true);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-center flex-wrap mt-2">
      <input
        value={symbol}
        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
        placeholder="TSLA"
        maxLength={10}
        className="w-20 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-mono uppercase"
      />
      <input
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Note (optional)"
        className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
      />
      <button
        type="submit"
        disabled={!symbol.trim() || mutation.isPending}
        className="flex items-center gap-1 text-xs bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white px-3 py-1 rounded transition-colors"
      >
        {mutation.isPending && <Spinner size="sm" />}
        Add
      </button>
      {conflict && <span className="text-xs text-amber-400">Already in watchlist</span>}
    </form>
  );
}
