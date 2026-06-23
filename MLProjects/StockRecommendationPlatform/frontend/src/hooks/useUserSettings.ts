"use client";

import { useCallback, useEffect, useState } from "react";

import { getUserSettings, saveUserSettings } from "@/lib/api";
import { useApiKey } from "@/contexts/ApiKeyContext";
import type { UserSettingsPayload, UserSettingsResponse } from "@/types/api";

const EMPTY: UserSettingsResponse = {
  default_symbol: null,
  default_portfolio_value: null,
  default_max_risk_pct: null,
  preferred_claude_model: null,
  market_grid_refresh_secs: null,
  market_grid_symbols: null,
  updated_at: null,
};

export function useUserSettings() {
  const { apiKey, hasKey } = useApiKey();
  const [settings, setSettings] = useState<UserSettingsResponse>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasKey) { setSettings(EMPTY); return; }
    setLoading(true);
    getUserSettings(apiKey)
      .then(setSettings)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [apiKey, hasKey]);

  const save = useCallback(
    async (payload: UserSettingsPayload) => {
      if (!hasKey) return;
      setSaving(true);
      setError(null);
      try {
        const updated = await saveUserSettings(apiKey, payload);
        setSettings(updated);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Save failed");
      } finally {
        setSaving(false);
      }
    },
    [apiKey, hasKey]
  );

  return { settings, loading, saving, error, save };
}
