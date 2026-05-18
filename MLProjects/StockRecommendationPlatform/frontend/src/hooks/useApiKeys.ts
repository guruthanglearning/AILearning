import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useApiKey } from "@/contexts/ApiKeyContext";
import { createApiKey, listApiKeys, revokeApiKey } from "@/lib/api";

const KEYS_QUERY_KEY = ["apiKeys"];

export function useListApiKeys() {
  const { apiKey, hasKey } = useApiKey();
  return useQuery({
    queryKey: KEYS_QUERY_KEY,
    queryFn: () => listApiKeys(apiKey),
    enabled: hasKey,
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => createApiKey(name),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEYS_QUERY_KEY }),
  });
}

export function useRevokeApiKey() {
  const { apiKey } = useApiKey();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (keyId: string) => revokeApiKey(apiKey, keyId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEYS_QUERY_KEY }),
  });
}
