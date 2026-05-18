"use client";

import { useState } from "react";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Spinner } from "@/components/ui/Spinner";
import { useCreateApiKey } from "@/hooks/useApiKeys";
import type { ApiKeyResponse } from "@/types/api";

interface CreateKeyFormProps {
  onCreated: (rawKey: string, response: ApiKeyResponse) => void;
}

export function CreateKeyForm({ onCreated }: CreateKeyFormProps) {
  const [name, setName] = useState("");
  const mutation = useCreateApiKey();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    const result = await mutation.mutateAsync(name.trim());
    if (result.key) {
      onCreated(result.key, result);
      setName("");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end">
      <div className="flex-1">
        <label className="block text-xs text-gray-400 mb-1">Key name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. dev-laptop"
          maxLength={100}
          className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
        />
      </div>
      <button
        type="submit"
        disabled={!name.trim() || mutation.isPending}
        className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
      >
        {mutation.isPending && <Spinner size="sm" />}
        Create Key
      </button>
      {mutation.error && (
        <div className="absolute mt-10">
          <ErrorMessage error={mutation.error as Error} />
        </div>
      )}
    </form>
  );
}
