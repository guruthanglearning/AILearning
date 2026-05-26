"use client";

import { createContext, useContext, useRef, useState } from "react";

import { useApiKey } from "@/contexts/ApiKeyContext";
import { streamAnalysis } from "@/lib/api";
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
  submit: (req: AnalysisRunRequest) => void;
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
  const abortRef = useRef<AbortController | null>(null);

  function submit(newReq: AnalysisRunRequest) {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setReq(newReq);
    setStartedAt(Date.now());
    setIsFetching(true);
    setError(null);
    setVerdict(null);
    setPartialContributions([]);

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

  function clear() {
    abortRef.current?.abort();
    setReq(null);
    setVerdict(null);
    setPartialContributions([]);
    setError(null);
    setStartedAt(null);
    setIsFetching(false);
  }

  return (
    <AnalysisContext.Provider
      value={{ req, verdict, partialContributions, isFetching, error, startedAt, submit, clear }}
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
