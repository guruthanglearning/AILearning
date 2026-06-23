"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useUserSettings } from "@/hooks/useUserSettings";
import { useApiKey } from "@/contexts/ApiKeyContext";

const MODEL_OPTIONS = [
  { id: "claude-haiku-4-5-20251001", label: "Haiku 4.5 — Dev / Fast" },
  { id: "claude-sonnet-4-6",         label: "Sonnet 4.6 — Balanced" },
  { id: "claude-opus-4-8",           label: "Opus 4.8 — Professional" },
];

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="block text-xs font-medium text-gray-300">{label}</label>
      {hint && <p className="text-[11px] text-gray-600">{hint}</p>}
      {children}
    </div>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const { hasKey } = useApiKey();
  const { settings, loading, saving, error, save } = useUserSettings();

  const [symbol,     setSymbol]     = useState("");
  const [portVal,    setPortVal]    = useState("");
  const [maxRisk,    setMaxRisk]    = useState("");
  const [model,      setModel]      = useState("");
  const [refresh,    setRefresh]    = useState("");
  const [gridSyms,   setGridSyms]   = useState("");
  const [saved,      setSaved]      = useState(false);

  useEffect(() => {
    if (loading) return;
    setSymbol(settings.default_symbol ?? "");
    setPortVal(settings.default_portfolio_value != null ? String(settings.default_portfolio_value) : "");
    setMaxRisk(settings.default_max_risk_pct != null ? String(settings.default_max_risk_pct) : "");
    setModel(settings.preferred_claude_model ?? "claude-opus-4-8");
    setRefresh(settings.market_grid_refresh_secs != null ? String(settings.market_grid_refresh_secs) : "");
    setGridSyms(settings.market_grid_symbols?.join(", ") ?? "");
  }, [loading, settings]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    await save({
      default_symbol:          symbol.toUpperCase().trim() || null,
      default_portfolio_value: portVal ? parseFloat(portVal) : null,
      default_max_risk_pct:    maxRisk ? parseFloat(maxRisk) : null,
      preferred_claude_model:  model || null,
      market_grid_refresh_secs: refresh ? parseInt(refresh, 10) : null,
      market_grid_symbols: gridSyms.trim()
        ? gridSyms.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean)
        : null,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  if (!hasKey) {
    return (
      <div className="text-sm text-gray-500 py-8 text-center">
        Set an API key in{" "}
        <button onClick={() => router.push("/keys")} className="text-indigo-400 hover:text-indigo-300 underline">
          API Keys
        </button>{" "}
        to save preferences.
      </div>
    );
  }

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-white">Settings</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Preferences saved to the server — persist across browsers and devices.
        </p>
      </div>

      {loading ? (
        <p className="text-xs text-gray-600">Loading…</p>
      ) : (
        <form onSubmit={handleSave} className="space-y-5">

          {/* Analysis defaults */}
          <section className="space-y-4 border border-gray-800 rounded-xl p-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Analysis Defaults</h2>

            <Field label="Default Symbol" hint="Pre-fills the symbol box on the Analysis page.">
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="AAPL"
                maxLength={10}
                className="w-32 bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </Field>

            <div className="flex gap-4">
              <Field label="Portfolio Value ($)" hint="Used for position sizing in analysis.">
                <input
                  type="number"
                  value={portVal}
                  onChange={(e) => setPortVal(e.target.value)}
                  placeholder="100000"
                  min="0"
                  className="w-36 bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                />
              </Field>
              <Field label="Max Risk / Trade (%)" hint="Risk per trade for sizing.">
                <input
                  type="number"
                  value={maxRisk}
                  onChange={(e) => setMaxRisk(e.target.value)}
                  placeholder="2"
                  min="0"
                  max="100"
                  step="0.5"
                  className="w-28 bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                />
              </Field>
            </div>

            <Field label="Preferred AI Model">
              <div className="flex flex-col gap-1.5">
                {MODEL_OPTIONS.map((m) => (
                  <label key={m.id} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="model"
                      value={m.id}
                      checked={model === m.id}
                      onChange={() => setModel(m.id)}
                      className="accent-indigo-500"
                    />
                    <span className="text-sm text-gray-300">{m.label}</span>
                  </label>
                ))}
              </div>
            </Field>
          </section>

          {/* Market grid */}
          <section className="space-y-4 border border-gray-800 rounded-xl p-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Market Grid</h2>

            <Field label="Auto-refresh Interval (seconds)" hint="How often the Market Grid refreshes quotes. Min 5, max 300.">
              <input
                type="number"
                value={refresh}
                onChange={(e) => setRefresh(e.target.value)}
                placeholder="30"
                min="5"
                max="300"
                className="w-28 bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
              />
            </Field>

            <Field
              label="Custom Symbols"
              hint="Comma-separated list of symbols shown on the Market Grid page (e.g. AAPL, MSFT, NVDA). Leave blank to use the default universe."
            >
              <textarea
                value={gridSyms}
                onChange={(e) => setGridSyms(e.target.value.toUpperCase())}
                placeholder="AAPL, MSFT, NVDA, TSLA, GOOGL"
                rows={3}
                className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 font-mono resize-none"
              />
            </Field>
          </section>

          {error && (
            <p className="text-xs text-red-400 bg-red-900/20 border border-red-900/50 rounded px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-sm text-white bg-indigo-600 hover:bg-indigo-500 rounded-md transition-colors disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save Settings"}
            </button>
            {saved && (
              <span className="text-xs text-emerald-400 flex items-center gap-1">
                <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M2.5 8.5l3.5 3.5 7-7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Saved
              </span>
            )}
            {settings.updated_at && (
              <span className="text-[11px] text-gray-600 ml-auto">
                Last saved {new Date(settings.updated_at).toLocaleString()}
              </span>
            )}
          </div>
        </form>
      )}
    </div>
  );
}
