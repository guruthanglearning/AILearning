"use client";

import Link from "next/link";

import { useApiKey } from "@/contexts/ApiKeyContext";

export function ApiKeyGate({ children }: { children: React.ReactNode }) {
  const { hasKey } = useApiKey();

  if (!hasKey) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-8 max-w-md text-center">
          <div className="text-red-400 text-2xl mb-3">🔑</div>
          <h2 className="text-white font-semibold text-lg mb-2">API Key Required</h2>
          <p className="text-gray-400 text-sm mb-5">
            You need an API key to use this feature. Create one or paste an existing key
            on the API Keys page.
          </p>
          <Link
            href="/keys"
            className="inline-block bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-5 py-2 rounded-md transition-colors"
          >
            Go to API Keys
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
