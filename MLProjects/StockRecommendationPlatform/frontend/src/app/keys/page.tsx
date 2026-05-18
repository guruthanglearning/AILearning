"use client";

import { useState } from "react";

import { CreateKeyForm } from "@/components/keys/CreateKeyForm";
import { KeyList } from "@/components/keys/KeyList";
import { NewKeyRevealModal } from "@/components/keys/NewKeyRevealModal";
import { useApiKey } from "@/contexts/ApiKeyContext";
import type { ApiKeyResponse } from "@/types/api";

export default function KeysPage() {
  const { hasKey, setApiKey, apiKey } = useApiKey();
  const [modal, setModal] = useState<{ rawKey: string; name: string } | null>(null);
  const [pasteValue, setPasteValue] = useState("");

  function handleCreated(rawKey: string, response: ApiKeyResponse) {
    setModal({ rawKey, name: response.name });
  }

  return (
    <div className="max-w-2xl space-y-8">
      {modal && (
        <NewKeyRevealModal
          rawKey={modal.rawKey}
          keyName={modal.name}
          onDismiss={() => setModal(null)}
        />
      )}

      <div>
        <h1 className="text-xl font-semibold text-white mb-1">API Keys</h1>
        <p className="text-sm text-gray-400">
          Create a key below. The full key is shown once — save it immediately.
        </p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-medium text-gray-300">Create New Key</h2>
        <CreateKeyForm onCreated={handleCreated} />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-medium text-gray-300">Paste Existing Key</h2>
        <p className="text-xs text-gray-500">
          If you already have a key from a previous session, paste it here to activate it.
        </p>
        <div className="flex gap-3">
          <input
            type="password"
            value={pasteValue}
            onChange={(e) => setPasteValue(e.target.value)}
            placeholder="sk-…"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="button"
            disabled={!pasteValue.trim()}
            onClick={() => { setApiKey(pasteValue.trim()); setPasteValue(""); }}
            className="bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-md transition-colors"
          >
            Activate
          </button>
        </div>
        {apiKey && (
          <p className="text-xs text-green-400">
            Active key prefix: <span className="font-mono">{apiKey.slice(0, 10)}…</span>
          </p>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-medium text-gray-300">Your Keys</h2>
        {hasKey ? (
          <KeyList />
        ) : (
          <p className="text-sm text-gray-500">Set a key above to list your existing keys.</p>
        )}
      </div>
    </div>
  );
}
