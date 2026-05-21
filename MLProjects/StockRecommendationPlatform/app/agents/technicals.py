from __future__ import annotations

import time

import numpy as np
import pandas as pd

from app.agents.base import AgentContext, BaseAgent
from app.schemas.agents import AgentStatus, TechnicalsOutput

# ── Indicator helpers ────────────────────────────────────────────────────────

def _sma(series: pd.Series, period: int) -> float | None:
    if len(series) < period:
        return None
    v = series.rolling(period).mean().iloc[-1]
    return float(v) if pd.notna(v) else None


def _ema(series: pd.Series, period: int) -> float | None:
    if len(series) < period:
        return None
    v = series.ewm(span=period, adjust=False).mean().iloc[-1]
    return float(v) if pd.notna(v) else None


def _rsi(series: pd.Series, period: int) -> float | None:
    if len(series) < period + 1:
        return None
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    v = rsi.iloc[-1]
    return float(v) if pd.notna(v) else None


def _macd(series: pd.Series, fast: int, slow: int, signal: int = 9) -> tuple[float | None, float | None, float | None]:
    if len(series) < slow:
        return None, None, None
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    def _f(s: pd.Series) -> float | None:
        v = s.iloc[-1]
        return float(v) if pd.notna(v) else None
    return _f(line), _f(sig), _f(hist)


def _obv(hist: pd.DataFrame) -> float | None:
    if "Volume" not in hist.columns or hist.empty:
        return None
    close = hist["Close"]
    volume = hist["Volume"]
    direction = np.sign(close.diff())
    direction.iloc[0] = 0
    obv = (direction * volume).cumsum()
    v = obv.iloc[-1]
    return float(v) if pd.notna(v) else None


def _atr_pct(hist: pd.DataFrame, period: int) -> float | None:
    if len(hist) < period + 1:
        return None
    high, low, close = hist["High"], hist["Low"], hist["Close"]
    prev = close.shift(1)
    tr = pd.concat([(high - low), (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    spot = close.iloc[-1]
    if pd.notna(atr) and spot > 0:
        return float(atr / spot * 100)
    return None


def _52w(hist: pd.DataFrame) -> tuple[float | None, float | None]:
    n = min(len(hist), 252)
    window = hist.tail(n)
    if window.empty:
        return None, None
    high = float(window["High"].max()) if pd.notna(window["High"].max()) else None
    low = float(window["Low"].min()) if pd.notna(window["Low"].min()) else None
    return high, low


# ── Agent ────────────────────────────────────────────────────────────────────

class TechnicalsAgent(BaseAgent[TechnicalsOutput]):
    name = "TechnicalsAgent"
    output_model = TechnicalsOutput

    async def run(self, ctx: AgentContext) -> TechnicalsOutput:
        t0 = time.perf_counter()
        try:
            hist = await ctx.provider.get_price_history(ctx.symbol, "1y")
            if hist.empty or len(hist) < 50:
                return TechnicalsOutput(
                    agent_name=self.name,
                    status=AgentStatus.degraded,
                    provenance=self._prov("provider", t0),
                    error_message="Insufficient history",
                    raw_artifact={},
                )

            close = hist["Close"]
            n = len(hist)

            sma20  = _sma(close, 20)
            sma50  = _sma(close, 50)
            sma200 = _sma(close, 200)
            ema20  = _ema(close, 20)
            ema200 = _ema(close, 200)

            rsi7   = _rsi(close, 7)
            rsi14  = _rsi(close, 14)
            rsi200 = _rsi(close, 200) if n >= 201 else None

            macd_line, macd_sig, macd_hist = _macd(close, fast=6, slow=13, signal=9)

            obv = _obv(hist)

            atr14 = _atr_pct(hist, 14)
            atr50 = _atr_pct(hist, 50)

            w52h, w52l = _52w(hist)

            # Trend: SMA20 vs SMA50 + RSI14 primary signal
            if sma20 and sma50 and (rsi14 or 50):
                if sma20 > sma50 and (rsi14 or 50) > 50:
                    trend = "bullish"
                elif sma20 < sma50 and (rsi14 or 50) < 50:
                    trend = "bearish"
                else:
                    trend = "mixed"
            else:
                trend = "mixed"

            return TechnicalsOutput(
                agent_name=self.name,
                status=AgentStatus.complete,
                provenance=self._prov("provider", t0),
                sma_20=sma20,
                sma_50=sma50,
                sma_200=sma200,
                ema_20=ema20,
                ema_200=ema200,
                rsi_7=rsi7,
                rsi_14=rsi14,
                rsi_200=rsi200,
                macd_6_13=macd_line,
                macd_6_13_signal=macd_sig,
                macd_6_13_hist=macd_hist,
                obv=obv,
                atr_pct_14=atr14,
                atr_pct_50=atr50,
                week_52_high=w52h,
                week_52_low=w52l,
                trend_hint=trend,
                raw_artifact={"bars": n},
            )
        except Exception as e:
            return self._fail(TechnicalsOutput, t0, "provider", str(e))
