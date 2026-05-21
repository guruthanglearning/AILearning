"use client";

import { createContext, useContext, useRef, useState } from "react";

import { useApiKey } from "@/contexts/ApiKeyContext";
import { runAnalysis } from "@/lib/api";
import type { AnalysisRunRequest, SupervisorVerdict } from "@/types/api";

interface AnalysisState {
  req: AnalysisRunRequest | null;
  verdict: SupervisorVerdict | null;
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
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function submit(newReq: AnalysisRunRequest) {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setReq(newReq);
    setStartedAt(Date.now());
    setIsFetching(true);
    setError(null);

    try {
      const result = await runAnalysis(apiKey, newReq);
      if (!ctrl.signal.aborted) setVerdict(result);
    } catch (err) {
      if (!ctrl.signal.aborted) setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      if (!ctrl.signal.aborted) setIsFetching(false);
    }
  }

  function clear() {
    abortRef.current?.abort();
    setReq(null);
    setVerdict(null);
    setError(null);
    setStartedAt(null);
    setIsFetching(false);
  }

  return (
    <AnalysisContext.Provider value={{ req, verdict, isFetching, error, startedAt, submit, clear }}>
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error("useAnalysis must be used within AnalysisProvider");
  return ctx;
}
