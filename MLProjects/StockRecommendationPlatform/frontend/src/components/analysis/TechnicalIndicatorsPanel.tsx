"use client";

import type { TechnicalsSnapshot } from "@/types/api";

const fmt = (v: number | null, decimals = 2, prefix = "") =>
  v == null ? "—" : `${prefix}${v.toFixed(decimals)}`;

const fmtPrice = (v: number | null) => fmt(v, 2, "$");
const fmtPct   = (v: number | null) => v == null ? "—" : `${v.toFixed(2)}%`;
const fmtObv   = (v: number | null) => {
  if (v == null) return "—";
  const abs = Math.abs(v);
  if (abs >= 1e9) return `${(v / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(v / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
  return v.toFixed(0);
};

function rsiColor(v: number | null): string {
  if (v == null) return "text-gray-500";
  if (v >= 70) return "text-red-400";
  if (v <= 30) return "text-green-400";
  return "text-gray-200";
}

function macdColor(v: number | null): string {
  if (v == null) return "text-gray-500";
  return v >= 0 ? "text-green-400" : "text-red-400";
}

function trendColor(trend: string | null): string {
  if (!trend) return "text-gray-400";
  if (trend === "bullish") return "text-green-400";
  if (trend === "bearish") return "text-red-400";
  return "text-amber-400";
}

interface RowProps {
  label: string;
  value: string;
  color?: string;
  note?: string;
}

function Row({ label, value, color = "text-gray-200", note }: RowProps) {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-gray-800 last:border-0">
      <span className="text-xs text-gray-500">{label}</span>
      <div className="text-right">
        <span className={`text-xs font-mono ${color}`}>{value}</span>
        {note && <span className="ml-2 text-xs text-gray-600">{note}</span>}
      </div>
    </div>
  );
}

interface GroupProps {
  title: string;
  children: React.ReactNode;
}

function Group({ title, children }: GroupProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">{title}</h3>
      {children}
    </div>
  );
}

export function TechnicalIndicatorsPanel({ tech }: { tech: TechnicalsSnapshot }) {
  // 52-week range position
  const w52h = tech.week_52_high;
  const w52l = tech.week_52_low;
  const rangePct =
    w52h != null && w52l != null && w52h > w52l
      ? (((w52h - w52l) / w52l) * 100).toFixed(1)
      : null;

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-gray-400">Technical Indicators</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">

        {/* Moving Averages */}
        <Group title="Moving Averages">
          <Row label="DMA 20  (SMA)"  value={fmtPrice(tech.sma_20)} />
          <Row label="DMA 50  (SMA)"  value={fmtPrice(tech.sma_50)} />
          <Row label="DMA 200 (SMA)"  value={fmtPrice(tech.sma_200)} />
          <Row label="EMA 20"         value={fmtPrice(tech.ema_20)} />
          <Row label="EMA 200"        value={fmtPrice(tech.ema_200)} />
        </Group>

        {/* RSI */}
        <Group title="RSI (Relative Strength Index)">
          <Row
            label="RSI 7"
            value={fmt(tech.rsi_7, 1)}
            color={rsiColor(tech.rsi_7)}
            note={tech.rsi_7 != null ? (tech.rsi_7 >= 70 ? "overbought" : tech.rsi_7 <= 30 ? "oversold" : "neutral") : undefined}
          />
          <Row
            label="RSI 14"
            value={fmt(tech.rsi_14, 1)}
            color={rsiColor(tech.rsi_14)}
            note={tech.rsi_14 != null ? (tech.rsi_14 >= 70 ? "overbought" : tech.rsi_14 <= 30 ? "oversold" : "neutral") : undefined}
          />
          <Row
            label="RSI 200"
            value={fmt(tech.rsi_200, 1)}
            color={rsiColor(tech.rsi_200)}
            note={tech.rsi_200 != null ? (tech.rsi_200 >= 70 ? "overbought" : tech.rsi_200 <= 30 ? "oversold" : "neutral") : undefined}
          />
        </Group>

        {/* MACD 6/13 */}
        <Group title="MACD (6 / 13 / 9)">
          <Row
            label="MACD Line"
            value={fmt(tech.macd_6_13, 4)}
            color={macdColor(tech.macd_6_13)}
          />
          <Row
            label="Signal Line"
            value={fmt(tech.macd_6_13_signal, 4)}
            color="text-gray-300"
          />
          <Row
            label="Histogram"
            value={fmt(tech.macd_6_13_hist, 4)}
            color={macdColor(tech.macd_6_13_hist)}
            note={
              tech.macd_6_13 != null && tech.macd_6_13_signal != null
                ? tech.macd_6_13 > tech.macd_6_13_signal
                  ? "bullish crossover"
                  : "bearish crossover"
                : undefined
            }
          />
        </Group>

        {/* ATR */}
        <Group title="ATR % (Average True Range)">
          <Row
            label="ATR 14 %"
            value={fmtPct(tech.atr_pct_14)}
            color={
              tech.atr_pct_14 == null ? "text-gray-500"
              : tech.atr_pct_14 > 3 ? "text-red-400"
              : tech.atr_pct_14 > 1.5 ? "text-amber-400"
              : "text-green-400"
            }
            note={
              tech.atr_pct_14 == null ? undefined
              : tech.atr_pct_14 > 3 ? "high volatility"
              : tech.atr_pct_14 > 1.5 ? "moderate"
              : "low volatility"
            }
          />
          <Row
            label="ATR 50 %"
            value={fmtPct(tech.atr_pct_50)}
            color={
              tech.atr_pct_50 == null ? "text-gray-500"
              : tech.atr_pct_50 > 3 ? "text-red-400"
              : tech.atr_pct_50 > 1.5 ? "text-amber-400"
              : "text-green-400"
            }
          />
        </Group>

        {/* OBV */}
        <Group title="Volume">
          <Row
            label="OBV (cumulative)"
            value={fmtObv(tech.obv)}
            color="text-gray-300"
          />
          <Row
            label="OBV 20d Trend"
            value={tech.obv_slope == null ? "—" : tech.obv_slope > 0 ? "Rising ↑" : tech.obv_slope < 0 ? "Falling ↓" : "Flat →"}
            color={tech.obv_slope == null ? "text-gray-500" : tech.obv_slope > 0 ? "text-green-400" : tech.obv_slope < 0 ? "text-red-400" : "text-gray-400"}
            note={tech.obv_slope != null ? (tech.obv_slope > 0 ? "accumulation" : tech.obv_slope < 0 ? "distribution" : "neutral") : undefined}
          />
        </Group>

        {/* 52-Week Range */}
        <Group title="52-Week Range">
          <Row label="52W High" value={fmtPrice(tech.week_52_high)} color="text-green-400" />
          <Row label="52W Low"  value={fmtPrice(tech.week_52_low)}  color="text-red-400" />
          {rangePct && (
            <Row label="Range Width" value={`${rangePct}%`} color="text-gray-300" note="high vs low" />
          )}
          {/* Trend summary */}
          <Row
            label="Trend"
            value={(tech.trend_hint ?? "mixed").charAt(0).toUpperCase() + (tech.trend_hint ?? "mixed").slice(1)}
            color={trendColor(tech.trend_hint)}
          />
        </Group>

      </div>
    </div>
  );
}
