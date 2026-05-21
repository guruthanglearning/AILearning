"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { AgentStatusGrid } from "@/components/analysis/AgentStatusGrid";
import { AnalysisForm } from "@/components/analysis/AnalysisForm";
import { AnalysisHistory } from "@/components/analysis/AnalysisHistory";
import { AnalysisLoader } from "@/components/analysis/AnalysisLoader";
import { DecisionAidsPanel } from "@/components/analysis/DecisionAidsPanel";
import { OptionsAnalysisPanel } from "@/components/analysis/OptionsAnalysisPanel";
import { OptionsGuidanceCard } from "@/components/analysis/OptionsGuidanceCard";
import { OptionsMetricsTable } from "@/components/analysis/OptionsMetricsTable";
import { TechnicalIndicatorsPanel } from "@/components/analysis/TechnicalIndicatorsPanel";
import { TradeGuidancePanel } from "@/components/analysis/TradeGuidancePanel";
import { VerdictCard } from "@/components/analysis/VerdictCard";
import { ApiKeyGate } from "@/components/layout/ApiKeyGate";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useRunAnalysis } from "@/hooks/useAnalysis";
import type { AnalysisRunRequest } from "@/types/api";

function HomePage() {
  const searchParams = useSearchParams();
  const autoSymbol = searchParams.get("symbol") ?? "";

  const [req, setReq] = useState<AnalysisRunRequest | null>(
    autoSymbol ? { symbol: autoSymbol } : null
  );
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const { data: verdict, isFetching, error, refetch } = useRunAnalysis(req);
  const autoSubmitted = useRef(false);

  // Auto-submit when navigated from watchlist
  useEffect(() => {
    if (autoSymbol && !autoSubmitted.current) {
      autoSubmitted.current = true;
      setReq({ symbol: autoSymbol });
      setStartedAt(Date.now());
      // refetch fires after state update
    }
  }, [autoSymbol]);

  // Trigger fetch whenever req changes (except initial null)
  useEffect(() => {
    if (req) refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [req]);

  function handleSubmit(newReq: AnalysisRunRequest) {
    setReq(newReq);
    setStartedAt(Date.now());
  }

  return (
    <ApiKeyGate>
      <div className="space-y-6">
        <AnalysisForm
          onSubmit={handleSubmit}
          isLoading={isFetching}
          defaultSymbol={autoSymbol}
        />

        {isFetching && startedAt != null && (
          <AnalysisLoader symbol={req?.symbol ?? ""} startedAt={startedAt} />
        )}

        {error && !isFetching && <ErrorMessage error={error as Error} />}

        {verdict && !isFetching && (
          <>
            <VerdictCard verdict={verdict} symbol={req?.symbol ?? ""} />
            <AgentStatusGrid contributions={verdict.agent_contributions} />

            {verdict.technicals && (
              <TechnicalIndicatorsPanel tech={verdict.technicals} />
            )}

            {verdict.technicals && (
              <TradeGuidancePanel verdict={verdict} />
            )}

            {verdict.options && (
              <OptionsGuidanceCard guidance={verdict.options} />
            )}

            {verdict.decision_aids && (
              <DecisionAidsPanel aids={verdict.decision_aids} />
            )}

            {(verdict.decision_aids?.options_metrics_table ?? []).length > 0 && (
              <OptionsAnalysisPanel
                rows={verdict.decision_aids!.options_metrics_table}
              />
            )}

            {(verdict.decision_aids?.options_metrics_table ?? []).length > 0 && (
              <div className="space-y-2">
                <h2 className="text-sm font-medium text-gray-400">Options Metrics Table</h2>
                <OptionsMetricsTable
                  rows={verdict.decision_aids!.options_metrics_table}
                />
              </div>
            )}

            {req?.symbol && <AnalysisHistory symbol={req.symbol} />}
          </>
        )}
      </div>
    </ApiKeyGate>
  );
}

export default function Page() {
  return (
    <Suspense>
      <HomePage />
    </Suspense>
  );
}
