import { useQuery } from "@tanstack/react-query";

import { useApiKey } from "@/contexts/ApiKeyContext";
import { getAnalysisHistory, getLiveQuote, runAnalysis } from "@/lib/api";
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
