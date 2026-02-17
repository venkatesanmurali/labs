/**
 * Thin HTTP client for the IncomePilot backend.
 * All calls go through the Vite dev-server proxy (/api → localhost:8000).
 */

import type {
  Holding,
  HoldingCreate,
  CSVImportResult,
  RecommendationResponse,
  RollRequest,
  RollDecision,
  JournalEntry,
  JournalEntryCreate,
  AnalyticsDashboard,
  StrategyConfig,
  Quote,
} from "../types";

const BASE = "/api";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

/* ── Holdings ─────────────────────────────────────────────────────────── */

export const holdingsApi = {
  list: () => request<Holding[]>("/holdings"),

  create: (data: HoldingCreate) =>
    request<Holding>("/holdings", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: number, data: Partial<HoldingCreate>) =>
    request<Holding>(`/holdings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  remove: (id: number) =>
    request<void>(`/holdings/${id}`, { method: "DELETE" }),

  importCSV: async (file: File): Promise<CSVImportResult> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/holdings/import-csv`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  loadDemo: () =>
    request<Holding[]>("/holdings/demo", { method: "POST" }),
};

/* ── Market Data ──────────────────────────────────────────────────────── */

export const marketApi = {
  quote: (symbol: string) => request<Quote>(`/market/quote/${symbol}`),
};

/* ── Recommendations ──────────────────────────────────────────────────── */

export const recommendationsApi = {
  get: (symbol: string, strategyType: "CC" | "CSP" = "CC") =>
    request<RecommendationResponse>(`/recommendations/${symbol}?strategy_type=${strategyType}`),
};

/* ── Roll ──────────────────────────────────────────────────────────────── */

export const rollApi = {
  evaluate: (data: RollRequest) =>
    request<RollDecision>("/roll", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

/* ── Journal ──────────────────────────────────────────────────────────── */

export const journalApi = {
  list: (symbol?: string) =>
    request<JournalEntry[]>(
      `/journal${symbol ? `?symbol=${symbol}` : ""}`
    ),

  create: (data: JournalEntryCreate) =>
    request<JournalEntry>("/journal", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: number, data: Partial<JournalEntry>) =>
    request<JournalEntry>(`/journal/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  remove: (id: number) =>
    request<void>(`/journal/${id}`, { method: "DELETE" }),

  dashboard: (symbol?: string) =>
    request<AnalyticsDashboard>(
      `/journal/analytics/dashboard${symbol ? `?symbol=${symbol}` : ""}`
    ),
};

/* ── Settings ─────────────────────────────────────────────────────────── */

export const settingsApi = {
  get: () => request<StrategyConfig>("/settings"),

  update: (data: Partial<StrategyConfig>) =>
    request<StrategyConfig>("/settings", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};
