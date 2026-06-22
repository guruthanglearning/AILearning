"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import {
  createPosition,
  deletePosition,
  getMarketQuotes,
  listPositions,
  updatePosition,
} from "@/lib/api";
import { useApiKey } from "@/contexts/ApiKeyContext";
import type {
  MarketQuoteRow,
  PortfolioPositionCreate,
  PortfolioPositionResponse,
} from "@/types/api";

// ── helpers ───────────────────────────────────────────────────────────────────

function fmt$(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function fmtPct(n: number | null | undefined): string {
  if (n == null) return "—";
  return (n >= 0 ? "+" : "") + n.toFixed(2) + "%";
}

function fmtDate(s: string | null | undefined): string {
  if (!s) return "—";
  return new Date(s).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function pnlClass(n: number | null): string {
  if (n == null) return "text-gray-400";
  return n >= 0 ? "text-emerald-400" : "text-red-400";
}

// ── Add/Edit modal ────────────────────────────────────────────────────────────

interface EditModalProps {
  initial?: PortfolioPositionResponse | null;
  onSave: (data: PortfolioPositionCreate) => Promise<void>;
  onClose: () => void;
}

function EditModal({ initial, onSave, onClose }: EditModalProps) {
  const [symbol, setSymbol] = useState(initial?.symbol ?? "");
  const [shares, setShares] = useState(String(initial?.shares ?? ""));
  const [costBasis, setCostBasis] = useState(String(initial?.cost_basis ?? ""));
  const [entryDate, setEntryDate] = useState(initial?.entry_date ?? "");
  const [notes, setNotes] = useState(initial?.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const sharesNum = parseFloat(shares);
    const costNum = parseFloat(costBasis);
    if (!symbol.trim() || isNaN(sharesNum) || sharesNum <= 0 || isNaN(costNum) || costNum <= 0) {
      setErr("Symbol, shares (> 0), and cost basis (> 0) are required.");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      await onSave({
        symbol: symbol.toUpperCase().trim(),
        shares: sharesNum,
        cost_basis: costNum,
        entry_date: entryDate || null,
        notes: notes || null,
      });
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-5 w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-sm font-semibold text-white mb-4">
          {initial ? "Edit Position" : "Add Position"}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              disabled={!!initial}
              placeholder="AAPL"
              className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-xs text-gray-400 mb-1">Shares</label>
              <input
                type="number"
                step="any"
                min="0"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                placeholder="10"
                className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-gray-400 mb-1">Cost Basis / Share</label>
              <input
                type="number"
                step="any"
                min="0"
                value={costBasis}
                onChange={(e) => setCostBasis(e.target.value)}
                placeholder="150.00"
                className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Entry Date (optional)</label>
            <input
              type="date"
              value={entryDate}
              onChange={(e) => setEntryDate(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Swing trade, earnings play…"
              className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>
          {err && <p className="text-xs text-red-400">{err}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-3 py-1.5 text-xs text-white bg-indigo-600 hover:bg-indigo-500 rounded-md transition-colors disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Summary bar ───────────────────────────────────────────────────────────────

interface SummaryProps {
  positions: PortfolioPositionResponse[];
  quotes: Map<string, MarketQuoteRow>;
}

function Summary({ positions, quotes }: SummaryProps) {
  let totalCost = 0;
  let totalValue = 0;

  for (const p of positions) {
    const q = quotes.get(p.symbol);
    const price = q?.last_price ?? null;
    const cost = p.shares * p.cost_basis;
    totalCost += cost;
    if (price != null) totalValue += p.shares * price;
  }

  const totalPnl = totalValue > 0 ? totalValue - totalCost : null;
  const totalPnlPct = totalCost > 0 && totalPnl != null ? (totalPnl / totalCost) * 100 : null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {[
        { label: "Total Cost", value: fmt$(totalCost) },
        { label: "Market Value", value: totalValue > 0 ? fmt$(totalValue) : "—" },
        {
          label: "Unrealized P&L",
          value: totalPnl != null ? fmt$(totalPnl) : "—",
          color: totalPnl != null ? pnlClass(totalPnl) : "text-gray-400",
        },
        {
          label: "Return",
          value: totalPnlPct != null ? fmtPct(totalPnlPct) : "—",
          color: totalPnlPct != null ? pnlClass(totalPnlPct) : "text-gray-400",
        },
      ].map(({ label, value, color }) => (
        <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg p-3">
          <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
          <p className={`text-base font-semibold font-mono ${color ?? "text-white"}`}>{value}</p>
        </div>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function PortfolioTracker() {
  const { apiKey, hasKey } = useApiKey();
  const router = useRouter();
  const [positions, setPositions] = useState<PortfolioPositionResponse[]>([]);
  const [quotes, setQuotes] = useState<Map<string, MarketQuoteRow>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<PortfolioPositionResponse | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const quotesRef = useRef<Set<string>>(new Set());

  async function reload() {
    if (!hasKey) return;
    setLoading(true);
    setError(null);
    try {
      const rows = await listPositions(apiKey);
      setPositions(rows);
      const seen = new Set<string>();
      const symbols = rows.map((r) => r.symbol).filter((s) => { if (seen.has(s)) return false; seen.add(s); return true; });
      const newSymbols = symbols.filter((s) => !quotesRef.current.has(s));
      if (newSymbols.length > 0) {
        newSymbols.forEach((s) => quotesRef.current.add(s));
        const qRows = await getMarketQuotes(symbols);
        setQuotes((prev) => {
          const next = new Map(prev);
          qRows.forEach((q) => next.set(q.symbol, q));
          return next;
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load portfolio");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, [hasKey]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleAdd(data: PortfolioPositionCreate) {
    await createPosition(apiKey, data);
    quotesRef.current.delete(data.symbol);
    await reload();
  }

  async function handleEdit(data: PortfolioPositionCreate) {
    if (!editTarget) return;
    await updatePosition(apiKey, editTarget.id, {
      shares: data.shares,
      cost_basis: data.cost_basis,
      entry_date: data.entry_date,
      notes: data.notes,
    });
    await reload();
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deletePosition(apiKey, id);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  if (!hasKey) {
    return (
      <div className="text-sm text-gray-500 py-8 text-center">
        Set an API key in{" "}
        <button
          onClick={() => router.push("/keys")}
          className="text-indigo-400 hover:text-indigo-300 underline"
        >
          API Keys
        </button>{" "}
        to use the portfolio tracker.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* header */}
      <div className="flex items-center justify-between">
        <div />
        <button
          onClick={() => setAddOpen(true)}
          className="flex items-center gap-1.5 text-xs text-white bg-indigo-600 hover:bg-indigo-500 px-3 py-1.5 rounded-md transition-colors"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M8 2v12M2 8h12" strokeLinecap="round" />
          </svg>
          Add Position
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 border border-red-900/50 rounded-md px-3 py-2">
          {error}
        </p>
      )}

      {/* summary */}
      {positions.length > 0 && <Summary positions={positions} quotes={quotes} />}

      {/* table */}
      {loading ? (
        <p className="text-xs text-gray-600 py-6 text-center">Loading…</p>
      ) : positions.length === 0 ? (
        <p className="text-xs text-gray-600 py-8 text-center">
          No positions yet. Click &ldquo;Add Position&rdquo; to track your first holding.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-500 uppercase tracking-wider border-b border-gray-800">
                {["Symbol", "Shares", "Cost/Share", "Total Cost", "Price", "Market Value", "P&L $", "P&L %", "Entry", ""].map((h) => (
                  <th key={h} className="text-left py-2 px-2 font-medium first:pl-0 last:pr-0">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => {
                const q = quotes.get(p.symbol);
                const price = q?.last_price ?? null;
                const totalCost = p.shares * p.cost_basis;
                const marketValue = price != null ? p.shares * price : null;
                const pnl = marketValue != null ? marketValue - totalCost : null;
                const pnlPct = pnl != null && totalCost > 0 ? (pnl / totalCost) * 100 : null;
                return (
                  <tr key={p.id} className="border-b border-gray-800/60 hover:bg-gray-800/30">
                    <td className="py-2.5 px-2 pl-0 font-mono font-bold text-white">
                      <button
                        onClick={() => router.push(`/?symbol=${p.symbol}`)}
                        className="hover:text-indigo-400 transition-colors"
                      >
                        {p.symbol}
                      </button>
                    </td>
                    <td className="py-2.5 px-2 font-mono text-gray-300">{p.shares.toLocaleString()}</td>
                    <td className="py-2.5 px-2 font-mono text-gray-300">{fmt$(p.cost_basis)}</td>
                    <td className="py-2.5 px-2 font-mono text-gray-300">{fmt$(totalCost)}</td>
                    <td className="py-2.5 px-2 font-mono text-gray-200">{fmt$(price)}</td>
                    <td className="py-2.5 px-2 font-mono text-gray-200">{fmt$(marketValue)}</td>
                    <td className={`py-2.5 px-2 font-mono font-medium ${pnlClass(pnl)}`}>{fmt$(pnl)}</td>
                    <td className={`py-2.5 px-2 font-mono font-medium ${pnlClass(pnlPct)}`}>{fmtPct(pnlPct)}</td>
                    <td className="py-2.5 px-2 text-gray-500">{fmtDate(p.entry_date)}</td>
                    <td className="py-2.5 px-2 pr-0">
                      <div className="flex items-center gap-1 justify-end">
                        <button
                          onClick={() => setEditTarget(p)}
                          className="text-gray-600 hover:text-gray-300 p-1 rounded hover:bg-gray-700 transition-colors"
                          title="Edit"
                        >
                          <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M11.5 2.5a1.41 1.41 0 0 1 2 2L5 13H2v-3L11.5 2.5Z" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(p.id)}
                          disabled={deletingId === p.id}
                          className="text-gray-600 hover:text-red-400 p-1 rounded hover:bg-red-900/20 transition-colors disabled:opacity-40"
                          title="Delete"
                        >
                          <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M3 5h10M6 5V3h4v2M7 8v4M9 8v4" strokeLinecap="round" />
                            <path d="M4 5l.75 9h6.5L12 5H4Z" strokeLinejoin="round" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {addOpen && (
        <EditModal
          onSave={handleAdd}
          onClose={() => setAddOpen(false)}
        />
      )}

      {editTarget && (
        <EditModal
          initial={editTarget}
          onSave={handleEdit}
          onClose={() => setEditTarget(null)}
        />
      )}
    </div>
  );
}
