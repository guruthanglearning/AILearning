"use client";

import { useEffect, useState } from "react";

import { useApiKey } from "@/contexts/ApiKeyContext";

interface NewKeyRevealModalProps {
  rawKey: string;
  keyName: string;
  onDismiss: () => void;
}

export function NewKeyRevealModal({ rawKey, keyName, onDismiss }: NewKeyRevealModalProps) {
  const { setApiKey } = useApiKey();
  const [copied, setCopied] = useState(false);

  // Auto-save to context so the app is immediately usable
  useEffect(() => {
    setApiKey(rawKey);
  }, [rawKey, setApiKey]);

  async function handleCopy() {
    await navigator.clipboard.writeText(rawKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-8 max-w-lg w-full mx-4 shadow-2xl">
        <h2 className="text-white font-semibold text-lg mb-1">API Key Created</h2>
        <p className="text-sm text-gray-400 mb-4">
          Key <span className="text-gray-200 font-medium">{keyName}</span> has been created.
        </p>

        <div className="bg-red-950 border border-red-800 rounded-lg p-3 mb-4">
          <p className="text-red-300 text-xs font-semibold">
            ⚠ This key will NOT be shown again. Copy it now.
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-3 font-mono text-sm text-green-300 break-all mb-4 select-all">
          {rawKey}
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleCopy}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium py-2 rounded-md transition-colors"
          >
            {copied ? "Copied!" : "Copy Key"}
          </button>
          <button
            type="button"
            onClick={onDismiss}
            className="flex-1 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm font-medium py-2 rounded-md transition-colors"
          >
            I&apos;ve copied it
          </button>
        </div>

        <p className="text-xs text-gray-500 mt-3 text-center">
          This key has been saved automatically for this session.
        </p>
      </div>
    </div>
  );
}
