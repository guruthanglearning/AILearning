import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useApiKey } from "@/contexts/ApiKeyContext";
import {
  addWatchlistSymbol,
  createWatchlist,
  deleteWatchlist,
  listWatchlistSymbols,
  listWatchlists,
  removeWatchlistSymbol,
} from "@/lib/api";
import type { WatchlistCreate, WatchlistSymbolAdd } from "@/types/api";

const WL_KEY = ["watchlists"];
const WL_SYMBOLS_KEY = (id: string) => ["watchlists", id, "symbols"];

export function useListWatchlists() {
  const { apiKey, hasKey } = useApiKey();
  return useQuery({ queryKey: WL_KEY, queryFn: () => listWatchlists(apiKey), enabled: hasKey });
}

export function useCreateWatchlist() {
  const { apiKey } = useApiKey();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: WatchlistCreate) => createWatchlist(apiKey, req),
    onSuccess: () => qc.invalidateQueries({ queryKey: WL_KEY }),
  });
}

export function useDeleteWatchlist() {
  const { apiKey } = useApiKey();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteWatchlist(apiKey, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: WL_KEY }),
  });
}

export function useListWatchlistSymbols(watchlistId: string, enabled: boolean) {
  const { apiKey } = useApiKey();
  return useQuery({
    queryKey: WL_SYMBOLS_KEY(watchlistId),
    queryFn: () => listWatchlistSymbols(apiKey, watchlistId),
    enabled,
  });
}

export function useAddWatchlistSymbol(watchlistId: string) {
  const { apiKey } = useApiKey();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: WatchlistSymbolAdd) => addWatchlistSymbol(apiKey, watchlistId, req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: WL_SYMBOLS_KEY(watchlistId) });
      qc.invalidateQueries({ queryKey: WL_KEY });
    },
  });
}

export function useRemoveWatchlistSymbol(watchlistId: string) {
  const { apiKey } = useApiKey();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => removeWatchlistSymbol(apiKey, watchlistId, symbol),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: WL_SYMBOLS_KEY(watchlistId) });
      qc.invalidateQueries({ queryKey: WL_KEY });
    },
  });
}
