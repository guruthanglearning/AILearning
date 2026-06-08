"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef } from "react";

import { AgentStatusGrid } from "@/components/analysis/AgentStatusGrid";
import { DeepPositionAnalysisPanel } from "@/components/analysis/DeepPositionAnalysisPanel";
import { AnalysisForm } from "@/components/analysis/AnalysisForm";
import { AnalysisHistory } from "@/components/analysis/AnalysisHistory";
import { AnalysisLoader } from "@/components/analysis/AnalysisLoader";
import { DecisionAidsPanel } from "@/components/analysis/DecisionAidsPanel";
import { EarningsCountdown } from "@/components/analysis/EarningsCountdown";
import { EntryExitCard } from "@/components/analysis/EntryExitCard";
import { FundamentalsPanel } from "@/components/analysis/FundamentalsPanel";
import { HowToReadModal } from "@/components/analysis/HowToReadModal";
import { LivePriceBar } from "@/components/analysis/LivePriceBar";
import { OptionsAnalysisPanel } from "@/components/analysis/OptionsAnalysisPanel";
import { OptionsGuidanceCard } from "@/components/analysis/OptionsGuidanceCard";
import { OptionsMetricsTable } from "@/components/analysis/OptionsMetricsTable";
import { PeerComparisonTable } from "@/components/analysis/PeerComparisonTable";
import { PriceChartPanel } from "@/components/analysis/PriceChartPanel";
import { PriceForecastPanel } from "@/components/analysis/PriceForecastPanel";
import { SentimentCard } from "@/components/analysis/SentimentCard";
import { TradeGuidancePanel } from "@/components/analysis/TradeGuidancePanel";
import { VerdictCard } from "@/components/analysis/VerdictCard";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useAnalysis } from "@/contexts/AnalysisContext";
import type { AnalysisRunRequest, SupervisorVerdict } from "@/types/api";

// ── Stage divider ─────────────────────────────────────────────────────────────

interface StageDividerProps {
  stage: number;
  title: string;
  subtitle: string;
}

function StageDivider({ stage, title, subtitle }: StageDividerProps) {
  return (
    <div className="flex items-center gap-3 pt-2">
      <span className="text-xs font-bold text-gray-600 uppercase tracking-widest shrink-0">
        Stage {stage}
      </span>
      <span className="text-xs font-medium text-gray-500 shrink-0">{title}</span>
      <span className="text-xs text-gray-700 shrink-0 hidden sm:inline">{subtitle}</span>
      <div className="flex-1 border-t border-gray-800" />
    </div>
  );
}

// ── Export / action buttons ───────────────────────────────────────────────────

function buildExportText(symbol: string, verdict: SupervisorVerdict): string {
  const lines: string[] = [
    `=== Stock Analysis: ${symbol} ===`,
    `Generated: ${new Date().toLocaleString()}`,
    "",
    `Recommendation: ${verdict.instrument_recommendation.toUpperCase()}`,
    `Confidence: ${verdict.confidence_note}`,
    "",
  ];

  if (verdict.fundamentals) {
    const f = verdict.fundamentals;
    lines.push("--- Fundamentals ---");
    if (f.company_name) lines.push(`Company: ${f.company_name}`);
    if (f.sector)       lines.push(`Sector: ${f.sector}`);
    if (f.market_cap)   lines.push(`Market Cap: $${(f.market_cap / 1e9).toFixed(1)}B`);
    if (f.pe_ratio)     lines.push(`Trailing P/E: ${f.pe_ratio.toFixed(1)}×`);
    if (f.forward_pe)   lines.push(`Forward P/E: ${f.forward_pe.toFixed(1)}×`);
    if (f.revenue_growth) lines.push(`Revenue Growth: ${(f.revenue_growth * 100).toFixed(1)}%`);
    lines.push("");
  }

  if (verdict.technicals) {
    const t = verdict.technicals;
    lines.push("--- Technicals ---");
    if (t.trend_hint)  lines.push(`Trend: ${t.trend_hint}`);
    if (t.rsi_14)      lines.push(`RSI 14: ${t.rsi_14.toFixed(1)}`);
    if (t.sma_20)      lines.push(`SMA 20: $${t.sma_20.toFixed(2)}`);
    if (t.sma_50)      lines.push(`SMA 50: $${t.sma_50.toFixed(2)}`);
    if (t.atr_pct_14)  lines.push(`ATR 14d: ${t.atr_pct_14.toFixed(2)}%`);
    lines.push("");
  }

  if (verdict.sentiment_score != null || verdict.sentiment_forecast) {
    lines.push("--- Sentiment ---");
    if (verdict.sentiment_forecast) lines.push(`Signal: ${verdict.sentiment_forecast}`);
    if (verdict.sentiment_score != null) lines.push(`Score: ${verdict.sentiment_score.toFixed(3)}`);
    if (verdict.sentiment_headlines.length > 0) {
      lines.push("Top Headlines:");
      verdict.sentiment_headlines.forEach((h, i) => lines.push(`  ${i + 1}. ${h}`));
    }
    lines.push("");
  }

  if (verdict.has_upcoming_earnings && verdict.earnings_days_away != null) {
    lines.push(`Earnings: ${verdict.earnings_days_away} days away`);
    lines.push("");
  }

  if (verdict.decision_aids) {
    const da = verdict.decision_aids;
    lines.push("--- Decision Aids ---");
    lines.push(`Summary: ${da.summary_headline}`);
    lines.push(`Stock vs Options Score: ${da.stock_vs_options_score.toFixed(2)}`);
    if (da.user_questions.length > 0) {
      lines.push("Reflective Questions:");
      da.user_questions.forEach((q, i) => {
        lines.push(`  Q${i + 1}: ${q}`);
        if (da.user_answers[i]) lines.push(`  A${i + 1}: ${da.user_answers[i]}`);
      });
    }
    lines.push("");
  }

  lines.push("--- Agent Contributions ---");
  verdict.agent_contributions.forEach(a => {
    lines.push(`[${a.status.toUpperCase()}] ${a.agent_name}: ${a.headline}`);
  });

  lines.push("");
  lines.push("Disclaimer: This analysis is for informational purposes only and is not investment advice.");

  return lines.join("\n");
}

function RerunButton({ onRerun }: { onRerun: () => void }) {
  return (
    <button
      onClick={onRerun}
      className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 border border-gray-700 px-3 py-1.5 rounded-md transition-colors"
    >
      <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M1.5 8a6.5 6.5 0 1 0 2.2-4.9" strokeLinecap="round" />
        <polyline points="1.5,3 1.5,8 6.5,8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      Re-run
    </button>
  );
}

function ExportButton({ symbol, verdict }: { symbol: string; verdict: SupervisorVerdict }) {
  function handleExport() {
    const text = buildExportText(symbol, verdict);
    navigator.clipboard.writeText(text).catch(() => {
      const blob = new Blob([text], { type: "text/plain" });
      window.open(URL.createObjectURL(blob), "_blank");
    });
  }

  return (
    <button
      onClick={handleExport}
      title="Copy analysis summary to clipboard"
      className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 border border-gray-700 px-3 py-1.5 rounded-md transition-colors"
    >
      <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="5" y="5" width="9" height="9" rx="1" />
        <path d="M11 5V3a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h2" strokeLinecap="round" />
      </svg>
      Copy Summary
    </button>
  );
}

function HowToReadButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 bg-indigo-900/30 hover:bg-indigo-900/50 border border-indigo-800/60 px-3 py-1.5 rounded-md transition-colors"
    >
      <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="8" cy="8" r="6.5" />
        <path d="M8 7v4" strokeLinecap="round" />
        <circle cx="8" cy="5" r="0.5" fill="currentColor" />
      </svg>
      How to read this
    </button>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

function HomePage() {
  const searchParams = useSearchParams();
  const autoSymbol = searchParams.get("symbol") ?? "";
  const { req, verdict, partialContributions, isFetching, error, startedAt, submit } = useAnalysis();
  const autoSubmitted = useRef(false);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    if (autoSymbol && !autoSubmitted.current) {
      autoSubmitted.current = true;
      submit({ symbol: autoSymbol });
    }
  }, [autoSymbol]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = (newReq: AnalysisRunRequest) => submit(newReq);
  const handleRerun  = useCallback(() => { if (req) submit(req); }, [req, submit]);

  const gridContributions = verdict?.agent_contributions ?? partialContributions;
  const showGrid = gridContributions.length > 0;
  const optRows  = verdict?.decision_aids?.options_metrics_table ?? [];

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

      {/* ── STAGE 1 — Go / No-Go ─────────────────────────────────────── */}
      {req?.symbol && (
        <>
          <StageDivider stage={1} title="Go / No-Go" subtitle="30 seconds" />
          <LivePriceBar symbol={req.symbol} />
        </>
      )}

      {showGrid && (
        <AgentStatusGrid contributions={gridContributions} streaming={isFetching} />
      )}

      {verdict && !isFetching && (
        <DeepPositionAnalysisPanel verdict={verdict} symbol={req?.symbol ?? ""} />
      )}

      {verdict && !isFetching && verdict.has_upcoming_earnings && (
        <EarningsCountdown verdict={verdict} />
      )}

      {verdict && !isFetching && (
        <>
          {/* ── STAGE 2 — Stock or Options? ──────────────────────────────── */}
          <StageDivider stage={2} title="Stock or Options?" subtitle="1–2 minutes" />

          {/* Action bar */}
          <div className="flex items-center justify-end gap-2 flex-wrap">
            <HowToReadButton onClick={() => setModalOpen(true)} />
            <RerunButton onRerun={handleRerun} />
            <ExportButton symbol={req?.symbol ?? ""} verdict={verdict} />
          </div>

          <VerdictCard verdict={verdict} symbol={req?.symbol ?? ""} />

          {verdict.decision_aids && (
            <DecisionAidsPanel aids={verdict.decision_aids} />
          )}

          {/* ── STAGE 3 — Confirm the Direction ──────────────────────────── */}
          <StageDivider stage={3} title="Confirm the Direction" subtitle="2 minutes" />

          {req?.symbol && <PriceChartPanel symbol={req.symbol} />}

          {verdict.technicals && (
            <TradeGuidancePanel verdict={verdict} />
          )}

          {(verdict.sentiment_score != null || verdict.sentiment_forecast) && (
            <SentimentCard verdict={verdict} />
          )}

          {/* ── STAGE 4 — Entry, Size & Exit ─────────────────────────────── */}
          <StageDivider stage={4} title="Entry, Size &amp; Exit" subtitle="2 minutes" />

          {verdict.technicals && <EntryExitCard verdict={verdict} />}

          {optRows.length > 0 && (
            <>
              <OptionsAnalysisPanel rows={optRows} />
              <div className="space-y-2">
                <h2 className="text-sm font-medium text-gray-400">Options Metrics Table</h2>
                <OptionsMetricsTable rows={optRows} />
              </div>
            </>
          )}

          {verdict.options && <OptionsGuidanceCard guidance={verdict.options} />}

          {/* ── STAGE 5 — Valuation & Context ────────────────────────────── */}
          <StageDivider stage={5} title="Valuation &amp; Context" subtitle="1 minute · swing trades" />

          {verdict.fundamentals && <FundamentalsPanel fund={verdict.fundamentals} />}

          {req?.symbol && <PeerComparisonTable symbol={req.symbol} />}

          {/* ── Reference ────────────────────────────────────────────────── */}
          <div className="flex items-center gap-3 pt-2">
            <span className="text-xs font-bold text-gray-700 uppercase tracking-widest shrink-0">
              Reference
            </span>
            <div className="flex-1 border-t border-gray-800" />
          </div>

          {verdict.technicals && <PriceForecastPanel verdict={verdict} />}

          {req?.symbol && <AnalysisHistory symbol={req.symbol} />}
        </>
      )}

      {/* How to read modal */}
      <HowToReadModal open={modalOpen} onClose={() => setModalOpen(false)} />
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
