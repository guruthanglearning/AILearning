import { useQuery } from "@tanstack/react-query";

import { useApiKey } from "@/contexts/ApiKeyContext";
import { getAnalysisHistory, getLatestAnalysisPerSymbol, getLiveQuote, runAnalysis } from "@/lib/api";
import type { AnalysisRunRequest } from "@/types/api";

export function useRunAnalysis(req: AnalysisRunRequest | null) {
  const { apiKey } = useApiKey();
  return useQuery({
    queryKey: ["analysis", req?.symbol, req?.portfolio_value_usd, req?.max_risk_per_trade_pct],
    queryFn: () => runAnalysis(apiKey, req!),
    enabled: false,
    staleTime: Infinity,
    retry: false,
  });
}

export function useLiveQuote(symbol: string | null) {
  return useQuery({
    queryKey: ["quote", "live", symbol],
    queryFn: () => getLiveQuote(symbol!),
    enabled: !!symbol,
    refetchInterval: 10_000,
    staleTime: 9_000,
    retry: false,
  });
}

export function useAnalysisHistory(symbol: string | null, limit = 20) {
  const { apiKey } = useApiKey();
  return useQuery({
    queryKey: ["analysis", "history", symbol, limit],
    queryFn: () => getAnalysisHistory(apiKey, symbol!, limit),
    enabled: !!symbol && !!apiKey,
    staleTime: 60_000,
    retry: false,
  });
}

// One request for a whole list of symbols (e.g. a watchlist) instead of one
// per-symbol history call per row.
export function useLatestAnalysisRuns(symbols: string[]) {
  const { apiKey, hasKey } = useApiKey();
  const key = [...symbols].sort().join(",");
  return useQuery({
    queryKey: ["analysis", "history", "latest", key],
    queryFn: () => getLatestAnalysisPerSymbol(apiKey, symbols),
    enabled: symbols.length > 0 && hasKey,
    staleTime: 60_000,
    retry: false,
  });
}
