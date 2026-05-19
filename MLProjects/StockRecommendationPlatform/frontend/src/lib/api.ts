import type {
  AlertCreate,
  AlertResponse,
  AnalysisHistoryItem,
  AnalysisRunRequest,
  ApiKeyResponse,
  BatchJobRequest,
  BatchJobResponse,
  SupervisorVerdict,
  WatchlistCreate,
  WatchlistResponse,
  WatchlistSymbolAdd,
  WatchlistSymbolResponse,
} from "@/types/api";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

export class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function headers(apiKey: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
  };
}

async function checkResponse(res: Response): Promise<void> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail);
  }
}

// ─── Analysis ────────────────────────────────────────────────────────────────

export async function runAnalysis(
  apiKey: string,
  req: AnalysisRunRequest
): Promise<SupervisorVerdict> {
  const res = await fetch(`${API_URL}/v1/analysis/run`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify(req),
  });
  await checkResponse(res);
  return res.json();
}

export async function getAnalysis(
  apiKey: string,
  symbol: string,
  portfolioValue?: number,
  maxRiskPct?: number
): Promise<SupervisorVerdict> {
  const params = new URLSearchParams();
  if (portfolioValue != null) params.set("portfolio_value_usd", String(portfolioValue));
  if (maxRiskPct != null) params.set("max_risk_per_trade_pct", String(maxRiskPct));
  const qs = params.toString() ? `?${params}` : "";
  const res = await fetch(`${API_URL}/v1/analysis/run/${encodeURIComponent(symbol)}${qs}`, {
    headers: headers(apiKey),
  });
  await checkResponse(res);
  return res.json();
}

export async function getAnalysisHistory(
  apiKey: string,
  symbol: string,
  limit = 20
): Promise<AnalysisHistoryItem[]> {
  const res = await fetch(
    `${API_URL}/v1/analysis/history/${encodeURIComponent(symbol)}?limit=${limit}`,
    { headers: headers(apiKey) }
  );
  await checkResponse(res);
  return res.json();
}

// ─── Batch ────────────────────────────────────────────────────────────────────

export async function startBatch(
  apiKey: string,
  req: BatchJobRequest
): Promise<BatchJobResponse> {
  const res = await fetch(`${API_URL}/v1/analysis/batch`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify(req),
  });
  await checkResponse(res);
  return res.json();
}

export async function getBatchStatus(
  apiKey: string,
  jobId: string
): Promise<BatchJobResponse> {
  const res = await fetch(`${API_URL}/v1/analysis/batch/${jobId}`, {
    headers: headers(apiKey),
  });
  await checkResponse(res);
  return res.json();
}

// ─── API Keys ─────────────────────────────────────────────────────────────────

export async function createApiKey(name: string): Promise<ApiKeyResponse> {
  const res = await fetch(`${API_URL}/v1/auth/keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  await checkResponse(res);
  return res.json();
}

export async function listApiKeys(apiKey: string): Promise<ApiKeyResponse[]> {
  const res = await fetch(`${API_URL}/v1/auth/keys`, {
    headers: headers(apiKey),
  });
  await checkResponse(res);
  return res.json();
}

export async function revokeApiKey(
  apiKey: string,
  keyId: string
): Promise<void> {
  const res = await fetch(`${API_URL}/v1/auth/keys/${keyId}`, {
    method: "DELETE",
    headers: headers(apiKey),
  });
  await checkResponse(res);
}

// ─── Watchlists ───────────────────────────────────────────────────────────────

export async function listWatchlists(apiKey: string): Promise<WatchlistResponse[]> {
  const res = await fetch(`${API_URL}/v1/watchlists`, {
    headers: headers(apiKey),
  });
  await checkResponse(res);
  return res.json();
}

export async function createWatchlist(
  apiKey: string,
  req: WatchlistCreate
): Promise<WatchlistResponse> {
  const res = await fetch(`${API_URL}/v1/watchlists`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify(req),
  });
  await checkResponse(res);
  return res.json();
}

export async function deleteWatchlist(
  apiKey: string,
  watchlistId: string
): Promise<void> {
  const res = await fetch(`${API_URL}/v1/watchlists/${watchlistId}`, {
    method: "DELETE",
    headers: headers(apiKey),
  });
  await checkResponse(res);
}

export async function listWatchlistSymbols(
  apiKey: string,
  watchlistId: string
): Promise<WatchlistSymbolResponse[]> {
  const res = await fetch(`${API_URL}/v1/watchlists/${watchlistId}/symbols`, {
    headers: headers(apiKey),
  });
  await checkResponse(res);
  return res.json();
}

export async function addWatchlistSymbol(
  apiKey: string,
  watchlistId: string,
  req: WatchlistSymbolAdd
): Promise<WatchlistSymbolResponse> {
  const res = await fetch(`${API_URL}/v1/watchlists/${watchlistId}/symbols`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify(req),
  });
  await checkResponse(res);
  return res.json();
}

export async function removeWatchlistSymbol(
  apiKey: string,
  watchlistId: string,
  symbol: string
): Promise<void> {
  const res = await fetch(
    `${API_URL}/v1/watchlists/${watchlistId}/symbols/${encodeURIComponent(symbol)}`,
    { method: "DELETE", headers: headers(apiKey) }
  );
  await checkResponse(res);
}

// ─── Alerts ───────────────────────────────────────────────────────────────────

export async function listAlerts(apiKey: string): Promise<AlertResponse[]> {
  const res = await fetch(`${API_URL}/v1/alerts`, {
    headers: headers(apiKey),
  });
  await checkResponse(res);
  return res.json();
}

export async function listTriggeredAlerts(apiKey: string): Promise<AlertResponse[]> {
  const res = await fetch(`${API_URL}/v1/alerts/triggered`, {
    headers: headers(apiKey),
  });
  await checkResponse(res);
  return res.json();
}

export async function createAlert(
  apiKey: string,
  req: AlertCreate
): Promise<AlertResponse> {
  const res = await fetch(`${API_URL}/v1/alerts`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify(req),
  });
  await checkResponse(res);
  return res.json();
}

export async function deleteAlert(
  apiKey: string,
  alertId: string
): Promise<void> {
  const res = await fetch(`${API_URL}/v1/alerts/${alertId}`, {
    method: "DELETE",
    headers: headers(apiKey),
  });
  await checkResponse(res);
}
