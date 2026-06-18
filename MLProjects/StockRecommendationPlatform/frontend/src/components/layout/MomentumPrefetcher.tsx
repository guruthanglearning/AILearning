"use client";

import { useEffect, useRef } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { useNotifications } from "@/contexts/NotificationContext";
import { getMomentumSectors } from "@/lib/api";

const LIMIT = 10;
const CACHE_HIT_THRESHOLD_MS = 2_000; // if resolved in <2s, cache was warm — skip notification

export function MomentumPrefetcher() {
  const queryClient = useQueryClient();
  const { add } = useNotifications();
  const notifiedRef = useRef(false);

  useEffect(() => {
    const startedAt = Date.now();

    queryClient
      .prefetchQuery({
        queryKey: ["momentum", "sectors", LIMIT],
        queryFn: () => getMomentumSectors(LIMIT).catch(() => null),
        staleTime: 4 * 60 * 1000,
        retry: 0,
      })
      .then(() => {
        const elapsed = Date.now() - startedAt;
        const onMomentumPage =
          typeof window !== "undefined" &&
          window.location.pathname === "/momentum";

        if (!notifiedRef.current && !onMomentumPage && elapsed > CACHE_HIT_THRESHOLD_MS) {
          notifiedRef.current = true;
          add({
            type: "success",
            message:
              "Momentum scan complete — top movers identified across 11 GICS sectors.",
            action: { label: "Open Momentum", href: "/momentum" },
          });
        }
      })
      .catch(() => {
        // Prefetch failed; data will be fetched on demand when user opens the page
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally run once on mount

  return null;
}
