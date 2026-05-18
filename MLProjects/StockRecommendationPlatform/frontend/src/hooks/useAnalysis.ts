import { useQuery } from "@tanstack/react-query";

import { useApiKey } from "@/contexts/ApiKeyContext";
import { runAnalysis } from "@/lib/api";
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
