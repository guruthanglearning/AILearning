"use client";

import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { useApiKey } from "@/contexts/ApiKeyContext";
import { useRevokeApiKey } from "@/hooks/useApiKeys";
import type { ApiKeyResponse } from "@/types/api";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

interface KeyCardProps {
  apiKey: ApiKeyResponse;
}

export function KeyCard({ apiKey: key }: KeyCardProps) {
  const { apiKey: currentKey, setApiKey } = useApiKey();
  const revoke = useRevokeApiKey();

  const isCurrentKey = currentKey.startsWith(key.key_prefix);

  return (
    <div
      className={`flex items-center gap-4 p-3 rounded-lg border ${
        isCurrentKey
          ? "border-green-800 bg-green-950/30"
          : "border-gray-800 bg-gray-900"
      }`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white truncate">{key.name}</span>
          {isCurrentKey && (
            <span className="text-xs text-green-400 border border-green-700 rounded px-1">
              active
            </span>
          )}
        </div>
        <div className="flex gap-4 mt-0.5 text-xs text-gray-500">
          <span className="font-mono">{key.key_prefix}…</span>
          <span>Created {formatDate(key.created_at)}</span>
          {key.last_used_at && <span>Last used {formatDate(key.last_used_at)}</span>}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {!isCurrentKey && (
          <button
            type="button"
            onClick={() => {
              // Prompt user to paste the full key since we don't store it
              const raw = prompt("Paste the full API key to activate it:");
              if (raw?.trim()) setApiKey(raw.trim());
            }}
            className="text-xs text-indigo-400 border border-indigo-700 rounded px-2 py-1 hover:bg-indigo-900 transition-colors"
          >
            Use This Key
          </button>
        )}
        <ConfirmButton
          onConfirm={() => revoke.mutate(key.id)}
          isLoading={revoke.isPending}
          label="Revoke"
        />
      </div>
    </div>
  );
}
