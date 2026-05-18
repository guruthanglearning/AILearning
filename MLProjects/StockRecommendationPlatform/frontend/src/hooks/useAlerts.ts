import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useApiKey } from "@/contexts/ApiKeyContext";
import { createAlert, deleteAlert, listAlerts, listTriggeredAlerts } from "@/lib/api";
import type { AlertCreate } from "@/types/api";

const ALERTS_KEY = ["alerts"];
const TRIGGERED_KEY = ["alerts", "triggered"];

export function useListAlerts() {
  const { apiKey, hasKey } = useApiKey();
  return useQuery({
    queryKey: ALERTS_KEY,
    queryFn: () => listAlerts(apiKey),
    enabled: hasKey,
    refetchInterval: 30_000,
  });
}

export function useListTriggeredAlerts() {
  const { apiKey, hasKey } = useApiKey();
  return useQuery({
    queryKey: TRIGGERED_KEY,
    queryFn: () => listTriggeredAlerts(apiKey),
    enabled: hasKey,
    refetchInterval: 30_000,
  });
}

export function useCreateAlert() {
  const { apiKey } = useApiKey();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: AlertCreate) => createAlert(apiKey, req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ALERTS_KEY });
      qc.invalidateQueries({ queryKey: TRIGGERED_KEY });
    },
  });
}

export function useDeleteAlert() {
  const { apiKey } = useApiKey();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteAlert(apiKey, id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ALERTS_KEY });
      qc.invalidateQueries({ queryKey: TRIGGERED_KEY });
    },
  });
}
