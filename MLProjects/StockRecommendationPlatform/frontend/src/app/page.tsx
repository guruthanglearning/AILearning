"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";

import { AgentStatusGrid } from "@/components/analysis/AgentStatusGrid";
import { AnalysisForm } from "@/components/analysis/AnalysisForm";
import { LivePriceBar } from "@/components/analysis/LivePriceBar";
import { AnalysisHistory } from "@/components/analysis/AnalysisHistory";
import { AnalysisLoader } from "@/components/analysis/AnalysisLoader";
import { DecisionAidsPanel } from "@/components/analysis/DecisionAidsPanel";
import { FundamentalsPanel } from "@/components/analysis/FundamentalsPanel";
import { OptionsAnalysisPanel } from "@/components/analysis/OptionsAnalysisPanel";
import { OptionsGuidanceCard } from "@/components/analysis/OptionsGuidanceCard";
import { OptionsMetricsTable } from "@/components/analysis/OptionsMetricsTable";
import { PriceForecastPanel } from "@/components/analysis/PriceForecastPanel";
import { TradeGuidancePanel } from "@/components/analysis/TradeGuidancePanel";
import { VerdictCard } from "@/components/analysis/VerdictCard";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useAnalysis } from "@/contexts/AnalysisContext";
import type { AnalysisRunRequest } from "@/types/api";

function HomePage() {
  const searchParams = useSearchParams();
  const autoSymbol = searchParams.get("symbol") ?? "";
  const { req, verdict, partialContributions, isFetching, error, startedAt, submit } = useAnalysis();
  const autoSubmitted = useRef(false);

  // Auto-submit when navigated from watchlist
  useEffect(() => {
    if (autoSymbol && !autoSubmitted.current) {
      autoSubmitted.current = true;
      submit({ symbol: autoSymbol });
    }
  }, [autoSymbol]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleSubmit(newReq: AnalysisRunRequest) {
    submit(newReq);
  }

  // Which contributions to show in the agent grid
  const gridContributions = verdict?.agent_contributions ?? partialContributions;
  const showGrid = gridContributions.length > 0;

  return (
    <div className="space-y-6">
      <AnalysisForm
        onSubmit={handleSubmit}
        isLoading={isFetching}
        defaultSymbol={autoSymbol || req?.symbol || ""}
      />

      {isFetching && startedAt != null && (
        <AnalysisLoader symbol={req?.symbol ?? ""} startedAt={startedAt} />
      )}

      {error && !isFetching && <ErrorMessage error={error as Error} />}

      {req?.symbol && <LivePriceBar symbol={req.symbol} />}

      {/* Live agent grid: visible as each agent reports in, pending cards fill the rest */}
      {showGrid && (
        <AgentStatusGrid
          contributions={gridContributions}
          streaming={isFetching}
        />
      )}

      {verdict && !isFetching && (
        <>
          <VerdictCard verdict={verdict} symbol={req?.symbol ?? ""} />

          {verdict.fundamentals && (
            <FundamentalsPanel fund={verdict.fundamentals} />
          )}

          {verdict.technicals && (
            <TradeGuidancePanel verdict={verdict} />
          )}

          {verdict.technicals && (
            <PriceForecastPanel verdict={verdict} />
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
  );
}

export default function Page() {
  return (
    <Suspense>
      <HomePage />
    </Suspense>
  );
}
