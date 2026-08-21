"use client";

import { createContext, useContext, useRef, useState } from "react";

import { useApiKey } from "@/contexts/ApiKeyContext";
import { getAnalysisRunDetail, streamAnalysis } from "@/lib/api";
import type { AgentContribution, AnalysisRunRequest, SupervisorVerdict } from "@/types/api";

export const KNOWN_AGENTS = [
  "MarketDataAgent",
  "FundamentalsAgent",
  "TechnicalsAgent",
  "FinancialsAgent",
  "OptionsAgent",
  "RiskProWorkflowAgent",
  "SentimentMLAgent",
] as const;

interface AnalysisState {
  req: AnalysisRunRequest | null;
  verdict: SupervisorVerdict | null;
  partialContributions: AgentContribution[];
  isFetching: boolean;
  error: Error | null;
  startedAt: number | null;
  savedReportAt: string | null;
  submit: (req: AnalysisRunRequest) => void;
  loadSaved: (runId: string) => Promise<void>;
  clear: () => void;
}

const AnalysisContext = createContext<AnalysisState | null>(null);

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const { apiKey } = useApiKey();
  const [req, setReq] = useState<AnalysisRunRequest | null>(null);
  const [verdict, setVerdict] = useState<SupervisorVerdict | null>(null);
  const [partialContributions, setPartialContributions] = useState<AgentContribution[]>([]);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [savedReportAt, setSavedReportAt] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  // Bumped by every submit()/loadSaved() call so a slower, superseded request
  // can detect it's stale and avoid clobbering newer state when it resolves.
  const requestSeq = useRef(0);

  function submit(newReq: AnalysisRunRequest) {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    requestSeq.current += 1;

    setReq(newReq);
    setStartedAt(Date.now());
    setIsFetching(true);
    setError(null);
    setVerdict(null);
    setPartialContributions([]);
    setSavedReportAt(null);

    streamAnalysis(
      apiKey,
      newReq,
      {
        onAgentDone(contribution) {
          if (ctrl.signal.aborted) return;
          setPartialContributions((prev) => {
            const idx = prev.findIndex((c) => c.agent_name === contribution.agent_name);
            if (idx >= 0) {
              const next = [...prev];
              next[idx] = contribution;
              return next;
            }
            return [...prev, contribution];
          });
        },
        onVerdict(v) {
          if (ctrl.signal.aborted) return;
          setVerdict(v);
        },
        onError(err) {
          if (ctrl.signal.aborted) return;
          setError(err);
          setIsFetching(false);
        },
        onDone() {
          if (ctrl.signal.aborted) return;
          setIsFetching(false);
        },
      },
      ctrl.signal
    );
  }

  async function loadSaved(runId: string) {
    abortRef.current?.abort();
    const seq = ++requestSeq.current;
    setIsFetching(true);
    setError(null);
    setVerdict(null);
    setPartialContributions([]);
    setSavedReportAt(null);
    try {
      const detail = await getAnalysisRunDetail(apiKey, runId);
      if (requestSeq.current !== seq) return; // superseded by a newer submit()/loadSaved()
      setReq({
        symbol: detail.symbol,
        portfolio_value_usd: detail.portfolio_value_usd ?? undefined,
        max_risk_per_trade_pct: detail.max_risk_per_trade_pct ?? undefined,
      });
      setVerdict(detail.verdict);
      setSavedReportAt(detail.finished_at ?? detail.started_at);
      if (!detail.verdict) {
        setError(new Error("This run has no saved report data."));
      }
    } catch (e) {
      if (requestSeq.current !== seq) return;
      setError(e instanceof Error ? e : new Error("Failed to load saved report"));
    } finally {
      if (requestSeq.current === seq) setIsFetching(false);
    }
  }

  function clear() {
    abortRef.current?.abort();
    setReq(null);
    setVerdict(null);
    setPartialContributions([]);
    setError(null);
    setStartedAt(null);
    setSavedReportAt(null);
    setIsFetching(false);
  }

  return (
    <AnalysisContext.Provider
      value={{
        req,
        verdict,
        partialContributions,
        isFetching,
        error,
        startedAt,
        savedReportAt,
        submit,
        loadSaved,
        clear,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error("useAnalysis must be used within AnalysisProvider");
  return ctx;
}
