"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

interface ApiKeyContextValue {
  apiKey: string;
  setApiKey: (key: string) => void;
  clearApiKey: () => void;
  hasKey: boolean;
}

const STORAGE_KEY = "srp_api_key";

const ApiKeyContext = createContext<ApiKeyContextValue>({
  apiKey: "",
  setApiKey: () => {},
  clearApiKey: () => {},
  hasKey: false,
});

export function ApiKeyProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKeyState] = useState<string>("");

  // Read from localStorage on first client render (SSR-safe)
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) ?? "";
    setApiKeyState(stored);
  }, []);

  const setApiKey = useCallback((key: string) => {
    localStorage.setItem(STORAGE_KEY, key);
    setApiKeyState(key);
  }, []);

  const clearApiKey = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setApiKeyState("");
  }, []);

  return (
    <ApiKeyContext.Provider
      value={{ apiKey, setApiKey, clearApiKey, hasKey: apiKey.length > 0 }}
    >
      {children}
    </ApiKeyContext.Provider>
  );
}

export function useApiKey(): ApiKeyContextValue {
  return useContext(ApiKeyContext);
}
