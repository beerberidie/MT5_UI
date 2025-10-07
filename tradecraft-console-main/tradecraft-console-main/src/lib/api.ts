// Core API client and helpers for Tradecraft frontend integration with FastAPI backend
// Uses global window.CONFIG.API_BASE and window.getAuthHeaders()

export type AccountResponse = {
  balance: number;
  equity: number;
  margin: number;
  margin_free: number;
  margin_level: number;
  leverage?: number;
  currency?: string;
};

export type PositionResponse = any; // backend returns MT5 fields; map defensively

export type SymbolRow = {
  canonical?: string;
  broker_symbol?: string;
  name?: string;
  bid?: number;
  ask?: number;
  spread?: number;
};

export async function apiCall<T = any>(endpoint: string, init: RequestInit = {}): Promise<T> {
  const base = (window as any).CONFIG?.API_BASE || "http://127.0.0.1:5001";
  const url = `${base}${endpoint}`;
  const hdrs = (window as any).getAuthHeaders?.() || {};
  const headers = { ...hdrs, ...(init.headers || {}) } as Record<string, string>;
  const controller = new AbortController();
  const timeout = (window as any).CONFIG?.CONNECTION_TIMEOUT || 10000;
  const tHandle = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, { ...init, headers, signal: controller.signal });
    if (!res.ok) {
      // Try to get error message from response
      let errorMessage = `HTTP ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // If JSON parsing fails, use status text
        errorMessage = `HTTP ${res.status}: ${res.statusText}`;
      }
      throw new Error(errorMessage);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(tHandle);
  }
}

// ---- Reads ----
export async function getSymbols(live = true): Promise<{ symbol: string; bid: number; ask: number; spread: number; change: number; changePercent: number }[]> {
  const rows = await apiCall<SymbolRow[]>(`/api/symbols?live=${live ? "true" : "false"}`);
  // Defensive check: ensure rows is an array
  if (!Array.isArray(rows)) {
    console.error('getSymbols: API returned non-array data:', rows);
    return [];
  }
  return rows
    .map((r) => ({
      symbol: (r.canonical as string) || (r.broker_symbol as string) || (r.name as string) || "",
      bid: Number(r.bid ?? 0),
      ask: Number(r.ask ?? 0),
      spread: Number(r.spread ?? 0),
      change: 0,
      changePercent: 0,
    }))
    .filter((r) => r.symbol);
}

export async function getPrioritySymbols(limit = 5): Promise<{ symbol: string; bid: number; ask: number; spread: number; change: number; changePercent: number }[]> {
  const rows = await apiCall<any[]>(`/api/symbols/priority?limit=${limit}`);
  // Defensive check: ensure rows is an array
  if (!Array.isArray(rows)) {
    console.error('getPrioritySymbols: API returned non-array data:', rows);
    return [];
  }
  return rows
    .map((r) => ({
      symbol: (r.symbol as string) || (r.canonical as string) || (r.name as string) || "",
      bid: Number(r.bid ?? 0),
      ask: Number(r.ask ?? 0),
      spread: Number(r.spread ?? 0),
      change: Number(r.change ?? 0),
      changePercent: Number(r.changePercent ?? r.win_rate ?? 0),
    }))
    .filter((r) => r.symbol);
}

export async function getAccount(): Promise<{
  balance: number; equity: number; margin: number; freeMargin: number; marginLevel: number; currency?: string;
}> {
  const a = await apiCall<AccountResponse>(`/api/account`);
  return {
    balance: Number(a.balance || 0),
    equity: Number(a.equity || 0),
    margin: Number(a.margin || 0),
    freeMargin: Number(a.margin_free || 0),
    marginLevel: Number(a.margin_level || 0),
    currency: a.currency,
  };
}

export async function getPositions(): Promise<{
  ticket?: number; symbol?: string; type?: string | number; volume?: number; profit?: number;
}[]> {
  const rows = await apiCall<PositionResponse[]>(`/api/positions`);
  // Defensive check: ensure rows is an array
  if (!Array.isArray(rows)) {
    console.error('getPositions: API returned non-array data:', rows);
    return [];
  }
  return rows.map((p: any) => ({
    ticket: p.ticket ?? p.position ?? undefined,
    symbol: p.symbol,
    type: p.type,
    volume: Number(p.volume || 0),
    profit: Number(p.profit || 0),
  }));
}

// ---- Reads: history & activity ----
export async function getHistoricalBars(opts: { symbol: string; timeframe: string; date_from?: string; date_to?: string; count?: number; }) {
  const q = new URLSearchParams();
  q.set('symbol', opts.symbol);
  q.set('timeframe', opts.timeframe);
  if (opts.date_from) q.set('date_from', opts.date_from);
  if (opts.date_to) q.set('date_to', opts.date_to);
  if (opts.count != null) q.set('count', String(opts.count));
  return apiCall<any[]>(`/api/history/bars?${q.toString()}`);
}

export async function getDeals(opts: { date_from?: string; date_to?: string; symbol?: string; }) {
  const q = new URLSearchParams();
  if (opts.date_from) q.set('date_from', opts.date_from);
  if (opts.date_to) q.set('date_to', opts.date_to);
  if (opts.symbol) q.set('symbol', opts.symbol);
  const res = await apiCall<any>(`/api/history/deals?${q.toString()}`);
  return Array.isArray(res) ? res : (res?.deals ?? []);
}

export async function getOrdersHistory(opts: { date_from?: string; date_to?: string; symbol?: string; }) {
  const q = new URLSearchParams();
  if (opts.date_from) q.set('date_from', opts.date_from);
  if (opts.date_to) q.set('date_to', opts.date_to);
  if (opts.symbol) q.set('symbol', opts.symbol);
  const res = await apiCall<any>(`/api/history/orders?${q.toString()}`);
  return Array.isArray(res) ? res : (res?.orders ?? res?.data ?? []);
}

// Pending orders
export async function getPendingOrders() {
  return apiCall<any[]>(`/api/orders`);
}
export async function createPendingOrder(payload: any) {
  return apiCall(`/api/orders/pending`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
export async function cancelPendingOrder(ticket: number | string) {
  return apiCall(`/api/orders/${ticket}`, { method: 'DELETE' });
}

export async function modifyPendingOrder(ticket: number | string, payload: { price?: number; sl?: number; tp?: number; expiration?: number; }) {
  return apiCall(`/api/orders/${ticket}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}


// ---- Writes ----
export async function postOrder(payload: {
  canonical: string;
  side: 'buy' | 'sell';
  volume: number;
  deviation?: number;
  sl?: number | null;
  tp?: number | null;
  comment?: string;
  magic?: number;
}): Promise<any> {
  return apiCall(`/api/order`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function closePosition(ticket: number | string): Promise<any> {
  return apiCall(`/api/positions/${ticket}/close`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
}

// ---- AI Trading API ----

export async function getAIStatus(): Promise<any> {
  return apiCall(`/api/ai/status`);
}

export async function evaluateSymbol(symbol: string, timeframe: string = 'H1', force: boolean = false): Promise<any> {
  return apiCall(`/api/ai/evaluate/${symbol}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ timeframe, force }),
  });
}

export async function enableAI(symbol: string, timeframe: string = 'H1', autoExecute: boolean = false): Promise<any> {
  return apiCall(`/api/ai/enable/${symbol}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ timeframe, auto_execute: autoExecute }),
  });
}

export async function disableAI(symbol: string): Promise<any> {
  return apiCall(`/api/ai/disable/${symbol}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function triggerKillSwitch(reason: string): Promise<any> {
  return apiCall(`/api/ai/kill-switch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
}

export async function getAIDecisions(limit: number = 50): Promise<any[]> {
  const data = await apiCall<any[]>(`/api/ai/decisions?limit=${limit}`);
  // Defensive check: ensure data is an array
  if (!Array.isArray(data)) {
    console.error('getAIDecisions: API returned non-array data:', data);
    return [];
  }
  return data;
}

export async function getStrategies(): Promise<any[]> {
  return apiCall(`/api/ai/strategies`);
}

export async function getStrategy(symbol: string): Promise<any> {
  return apiCall(`/api/ai/strategies/${symbol}`);
}

export async function saveStrategy(symbol: string, strategy: any): Promise<any> {
  return apiCall(`/api/ai/strategies/${symbol}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(strategy),
  });
}

// ---- Trade Idea Execution ----

export async function getPendingTradeIdeas(): Promise<any[]> {
  const response = await apiCall<any>(`/api/ai/trade-ideas/pending`);
  // Backend returns { trade_ideas: [...], count: number }
  const data = response?.trade_ideas || response;
  // Defensive check: ensure data is an array
  if (!Array.isArray(data)) {
    console.error('getPendingTradeIdeas: API returned non-array data:', data);
    return [];
  }
  return data;
}

export async function getTradeIdeaHistory(): Promise<any[]> {
  const response = await apiCall<any>(`/api/ai/trade-ideas/history`);
  // Backend returns { trade_ideas: [...], count: number }
  const data = response?.trade_ideas || response;
  // Defensive check: ensure data is an array
  if (!Array.isArray(data)) {
    console.error('getTradeIdeaHistory: API returned non-array data:', data);
    return [];
  }
  return data;
}

export async function approveTradeIdea(ideaId: string): Promise<any> {
  return apiCall(`/api/ai/trade-ideas/${ideaId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function rejectTradeIdea(ideaId: string, reason: string): Promise<any> {
  return apiCall(`/api/ai/trade-ideas/${ideaId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
}

export async function executeTradeIdea(ideaId: string, accountBalance: number, volume?: number): Promise<any> {
  const body: any = { account_balance: accountBalance };
  if (volume !== undefined) {
    body.volume = volume;
  }
  return apiCall(`/api/ai/trade-ideas/${ideaId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

