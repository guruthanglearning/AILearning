// Client-side technical indicator computation from OHLCV close prices.

export function computeEMA(data: number[], period: number): (number | null)[] {
  if (data.length < period) return Array(data.length).fill(null);
  const k = 2 / (period + 1);
  const result: (number | null)[] = Array(period - 1).fill(null);
  let ema = data.slice(0, period).reduce((a, b) => a + b, 0) / period;
  result.push(ema);
  for (let i = period; i < data.length; i++) {
    ema = data[i] * k + ema * (1 - k);
    result.push(ema);
  }
  return result;
}

export function computeRSI(closes: number[], period = 14): (number | null)[] {
  if (closes.length <= period) return Array(closes.length).fill(null);
  const changes = closes.map((c, i) => (i === 0 ? 0 : c - closes[i - 1]));
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 1; i <= period; i++) {
    avgGain += Math.max(changes[i], 0);
    avgLoss += Math.max(-changes[i], 0);
  }
  avgGain /= period;
  avgLoss /= period;
  const result: (number | null)[] = [null];
  for (let i = 1; i < period; i++) result.push(null);
  result.push(100 - 100 / (1 + (avgLoss === 0 ? Infinity : avgGain / avgLoss)));
  for (let i = period + 1; i < closes.length; i++) {
    const gain = Math.max(changes[i], 0);
    const loss = Math.max(-changes[i], 0);
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    result.push(100 - 100 / (1 + (avgLoss === 0 ? Infinity : avgGain / avgLoss)));
  }
  return result;
}

export interface MACDResult {
  macd: (number | null)[];
  signal: (number | null)[];
  histogram: (number | null)[];
}

export function computeMACD(
  closes: number[],
  fast = 6,
  slow = 13,
  signalPeriod = 9,
): MACDResult {
  const emaFast = computeEMA(closes, fast);
  const emaSlow = computeEMA(closes, slow);
  const macd: (number | null)[] = emaFast.map((f, i) =>
    f == null || emaSlow[i] == null ? null : f - emaSlow[i]!,
  );
  const nonNullMacd = macd.filter((v): v is number => v != null);
  const sigVals = computeEMA(nonNullMacd, signalPeriod);
  const signal: (number | null)[] = Array(macd.length).fill(null);
  let sigIdx = 0;
  for (let i = 0; i < macd.length; i++) {
    if (macd[i] != null) {
      signal[i] = sigVals[sigIdx];
      sigIdx++;
    }
  }
  const histogram: (number | null)[] = macd.map((m, i) =>
    m == null || signal[i] == null ? null : m - signal[i]!,
  );
  return { macd, signal, histogram };
}
