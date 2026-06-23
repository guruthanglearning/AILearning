"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getBatchStatus, startCustomBatch } from "@/lib/api";
import { useApiKey } from "@/contexts/ApiKeyContext";
import type { BatchJobResponse } from "@/types/api";

export function useBatchJob() {
  const { apiKey } = useApiKey();
  const [job,     setJob]     = useState<BatchJobResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPoll = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  useEffect(() => () => stopPoll(), []);

  const start = useCallback(
    async (symbols: string[], batchKey?: string) => {
      stopPoll();
      setLoading(true);
      setError(null);
      setJob(null);
      try {
        const resp = await startCustomBatch(apiKey, symbols, batchKey);
        setJob(resp);

        pollRef.current = setInterval(async () => {
          try {
            const status = await getBatchStatus(apiKey, String(resp.job_id));
            setJob(status);
            if (status.status === "complete" || status.status === "partial" || status.status === "failed") {
              stopPoll();
              setLoading(false);
            }
          } catch {
            stopPoll();
            setLoading(false);
          }
        }, 3000);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Batch start failed");
        setLoading(false);
      }
    },
    [apiKey]
  );

  const reset = useCallback(() => {
    stopPoll();
    setJob(null);
    setError(null);
    setLoading(false);
  }, []);

  return { job, loading, error, start, reset };
}
