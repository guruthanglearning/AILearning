import { useEffect, useRef, useState } from "react";

import { useQuery } from "@tanstack/react-query";

import { getMomentumSectors } from "@/lib/api";

const POLL_MS = 5 * 60 * 1000; // 5 min — aligns with backend TTL cache

export function useMomentumSectors(limit = 10) {
  const result = useQuery({
    queryKey: ["momentum", "sectors", limit],
    queryFn: () => getMomentumSectors(limit),
    refetchInterval: POLL_MS,
    staleTime: POLL_MS - 10_000,
    retry: 2,
  });

  const [countdown, setCountdown] = useState(POLL_MS / 1000);
  const cdRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setCountdown(POLL_MS / 1000);
    if (cdRef.current) clearInterval(cdRef.current);
    cdRef.current = setInterval(
      () => setCountdown((c) => Math.max(0, c - 1)),
      1000
    );
    return () => { if (cdRef.current) clearInterval(cdRef.current); };
  }, [result.dataUpdatedAt]);

  return { ...result, isRefreshing: result.isFetching && !!result.data, countdown, refresh: result.refetch };
}
