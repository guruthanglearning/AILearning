"use client";

import { useEffect, useState } from "react";

import { getMomentumSectors } from "@/lib/api";
import type { MomentumSectorsResponse, MomentumStockRow, SectorMomentum } from "@/types/api";

// ── color helpers ─────────────────────────────────────────────────────────────

function heatBg(pct: number | null): string {
  if (pct == null) return "bg-gray-800 text-gray-500 border-gray-700";
  if (pct >= 5)  return "bg-emerald-600 text-white border-emerald-500";
  if (pct >= 3)  return "bg-green-600 text-white border-green-500";
  if (pct >= 1)  return "bg-green-700 text-white border-green-600";
  if (pct >= 0)  return "bg-green-900/80 text-green-300 border-green-800";
  if (pct >= -1) return "bg-red-900/80 text-red-300 border-red-800";
  if (pct >= -3) return "bg-red-700 text-white border-red-600";
  if (pct >= -5) return "bg-red-600 text-white border-red-500";
  return "bg-red-500 text-white border-red-400";
}

function etfHeaderBg(pct: number | null): string {
  if (pct == null) return "border-gray-800 text-gray-500";
  if (pct >= 1)  return "border-green-800/60 text-green-400";
  if (pct >= 0)  return "border-green-900/40 text-green-600";
  if (pct >= -1) return "border-red-900/40 text-red-500";
  return "border-red-800/60 text-red-400";
}

function fmtPct(pct: number | null): string {
  if (pct == null) return "—";
  return (pct >= 0 ? "+" : "") + pct.toFixed(2) + "%";
}

// ── StockCell ─────────────────────────────────────────────────────────────────

function StockCell({
  stock,
  onAnalyze,
}: {
  stock: MomentumStockRow;
  onAnalyze: (s: string) => void;
}) {
  const chg = stock.day_change_pct;
  return (
    <button
      type="button"
      onClick={() => onAnalyze(stock.symbol)}
      title={[
        stock.company_name ?? stock.symbol,
        stock.industry ? `· ${stock.industry}` : "",
        chg != null ? `· Day: ${chg > 0 ? "+" : ""}${chg.toFixed(2)}%` : "",
        stock.close_price != null ? `· $${stock.close_price.toFixed(2)}` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      className={`flex flex-col items-center justify-center w-[76px] h-[52px] rounded border text-center transition-all hover:opacity-80 hover:scale-105 ${heatBg(chg)}`}
    >
      <span className="text-[11px] font-bold font-mono leading-tight">
        {stock.symbol}
      </span>
      <span className="text-[10px] font-mono leading-tight mt-0.5">
        {chg != null ? `${chg > 0 ? "+" : ""}${chg.toFixed(1)}%` : "--"}
      </span>
    </button>
  );
}

// ── SectorHeader — matches Yahoo Finance / Bloomberg style ───────────────────

function SectorHeader({ sector }: { sector: SectorMomentum }) {
  const { etf_symbol, etf_price, etf_change_pct, etf_prev_close } = sector;
  const colorCls = etfHeaderBg(etf_change_pct);

  return (
    <div className="flex items-center gap-3 mb-2">
      {/* Sector name */}
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider shrink-0">
        {sector.sector}
      </h3>

      {/* ETF badge — Yahoo Finance standard */}
      {etf_symbol && (
        <div className={`flex items-center gap-2 px-2 py-0.5 rounded border text-[10px] font-mono shrink-0 ${colorCls}`}>
          <span className="font-bold">{etf_symbol}</span>
          {etf_price != null && (
            <span className="text-gray-400">${etf_price.toFixed(2)}</span>
          )}
          <span className={`font-semibold ${etf_change_pct != null && etf_change_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
            {fmtPct(etf_change_pct)}
          </span>
          {etf_prev_close != null && (
            <span className="text-gray-600">prev ${etf_prev_close.toFixed(2)}</span>
          )}
        </div>
      )}

      <div className="flex-1 h-px bg-gray-800" />
      <span className="text-[10px] text-gray-700 shrink-0">
        {sector.stocks.length} stocks
      </span>
    </div>
  );
}

// ── Legend ────────────────────────────────────────────────────────────────────

const LEGEND_ITEMS = [
  { label: "≥+5%", cls: "bg-emerald-600 text-white" },
  { label: "+3–5%", cls: "bg-green-600 text-white" },
  { label: "+1–3%", cls: "bg-green-700 text-white" },
  { label: "0–1%", cls: "bg-green-900/80 text-green-300" },
  { label: "-1–0%", cls: "bg-red-900/80 text-red-300" },
  { label: "-3–-1%", cls: "bg-red-700 text-white" },
  { label: "≤-3%", cls: "bg-red-600 text-white" },
];

// ── Main ──────────────────────────────────────────────────────────────────────

interface SectorHeatmapProps {
  onAnalyze?: (symbol: string) => void;
}

export function SectorHeatmap({ onAnalyze }: SectorHeatmapProps) {
  const [data, setData] = useState<MomentumSectorsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    getMomentumSectors(20)
      .then((r) => {
        setData(r);
        setLastUpdated(new Date());
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load sector data"))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  if (loading && !data) {
    return (
      <div className="space-y-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 w-52 bg-gray-800 rounded animate-pulse" />
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 10 }).map((_, j) => (
                <div key={j} className="w-[76px] h-[52px] bg-gray-800 rounded animate-pulse" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
        {error}
      </p>
    );
  }

  if (!data?.sectors.length) {
    return <p className="text-xs text-gray-600">No sector data available.</p>;
  }

  const totalStocks = data.sectors.reduce((n, s) => n + s.stocks.length, 0);

  return (
    <div className="space-y-5">
      {/* Meta row */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-500">Day change (regular session):</span>
          {LEGEND_ITEMS.map(({ label, cls }) => (
            <span key={label} className={`px-2 py-0.5 rounded text-[10px] font-mono ${cls}`}>
              {label}
            </span>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-3 text-xs text-gray-600">
          {lastUpdated && <span>Updated {lastUpdated.toLocaleTimeString()}</span>}
          <span>{data.sectors.length} sectors · {totalStocks} stocks</span>
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="px-2 py-1 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-400 rounded transition-colors disabled:opacity-40"
          >
            {loading ? "…" : "↻"}
          </button>
        </div>
      </div>

      {/* Sector rows */}
      {data.sectors.map((sector) => (
        <div key={sector.sector}>
          <SectorHeader sector={sector} />
          <div className="flex flex-wrap gap-2">
            {sector.stocks.map((stock) => (
              <StockCell
                key={stock.symbol}
                stock={stock}
                onAnalyze={onAnalyze ?? (() => {})}
              />
            ))}
          </div>
        </div>
      ))}

      <p className="text-[10px] text-gray-700 italic border-t border-gray-800/50 pt-3">
        Sector ETF (SPDR Select) + stock day change % vs prior regular-session close — same methodology as Yahoo Finance &amp; Bloomberg.
        15-min delayed. Not investment advice.
      </p>
    </div>
  );
}
