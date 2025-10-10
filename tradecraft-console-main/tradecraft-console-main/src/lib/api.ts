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

// ---- Autonomy Loop API ----

export async function startAutonomyLoop(intervalMinutes: number = 15): Promise<any> {
  return apiCall(`/api/ai/autonomy/start?interval_minutes=${intervalMinutes}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function stopAutonomyLoop(): Promise<any> {
  return apiCall(`/api/ai/autonomy/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function getAutonomyStatus(): Promise<any> {
  return apiCall(`/api/ai/autonomy/status`);
}

export async function triggerImmediateEvaluation(): Promise<any> {
  return apiCall(`/api/ai/autonomy/evaluate-now`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
}

// ==================== SETTINGS API ====================

export interface MT5Account {
  id: string;
  name: string;
  login: number;
  server: string;
  is_active: boolean;
  status: 'connected' | 'disconnected' | 'error';
  created_at: string;
  updated_at?: string;
}

export interface AccountTestResult {
  success: boolean;
  connected: boolean;
  error?: string;
  account_info?: {
    balance: number;
    equity: number;
    margin: number;
    margin_free: number;
    margin_level: number;
    leverage: number;
    currency: string;
    name: string;
    server: string;
    login: number;
  };
}

export async function getAccounts(): Promise<{ accounts: MT5Account[]; active_account_id: string | null }> {
  return apiCall('/api/settings/accounts');
}

export async function createAccount(account: {
  name: string;
  login: number;
  password: string;
  server: string;
}): Promise<MT5Account> {
  return apiCall('/api/settings/accounts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(account),
  });
}

export async function updateAccount(
  accountId: string,
  updates: {
    name?: string;
    login?: number;
    password?: string;
    server?: string;
  }
): Promise<MT5Account> {
  return apiCall(`/api/settings/accounts/${accountId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
}

export async function deleteAccount(accountId: string): Promise<{ success: boolean; message: string }> {
  return apiCall(`/api/settings/accounts/${accountId}`, {
    method: 'DELETE',
  });
}

export async function activateAccount(accountId: string): Promise<{ success: boolean; message: string; account: MT5Account }> {
  return apiCall(`/api/settings/accounts/${accountId}/activate`, {
    method: 'POST',
  });
}

export async function testAccountConnection(accountId: string): Promise<AccountTestResult> {
  return apiCall(`/api/settings/accounts/${accountId}/test`, {
    method: 'POST',
  });
}

// ==================== API INTEGRATIONS ====================

export interface APIIntegration {
  id: string;
  name: string;
  type: 'economic_calendar' | 'news' | 'custom';
  base_url?: string;
  config?: Record<string, any>;
  status: 'active' | 'inactive' | 'error';
  last_tested?: string;
  created_at: string;
  updated_at?: string;
  api_key_masked: string;
}

export interface IntegrationTestResult {
  success: boolean;
  connected: boolean;
  error?: string;
  response_data?: Record<string, any>;
}

export async function getAPIIntegrations(): Promise<{ integrations: APIIntegration[] }> {
  return apiCall('/api/settings/integrations');
}

export async function createAPIIntegration(integration: {
  name: string;
  type: 'economic_calendar' | 'news' | 'custom';
  api_key: string;
  base_url?: string;
  config?: Record<string, any>;
}): Promise<APIIntegration> {
  return apiCall('/api/settings/integrations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(integration),
  });
}

export async function updateAPIIntegration(
  integrationId: string,
  updates: {
    name?: string;
    type?: 'economic_calendar' | 'news' | 'custom';
    api_key?: string;
    base_url?: string;
    config?: Record<string, any>;
  }
): Promise<APIIntegration> {
  return apiCall(`/api/settings/integrations/${integrationId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
}

export async function deleteAPIIntegration(integrationId: string): Promise<{ success: boolean; message: string }> {
  return apiCall(`/api/settings/integrations/${integrationId}`, {
    method: 'DELETE',
  });
}

export async function testAPIIntegration(integrationId: string): Promise<IntegrationTestResult> {
  return apiCall(`/api/settings/integrations/${integrationId}/test`, {
    method: 'POST',
  });
}

// ==================== APPEARANCE SETTINGS ====================

export interface AppearanceSettings {
  density: 'compact' | 'normal' | 'comfortable';
  theme: 'dark' | 'light';
  font_size: number;
  accent_color: string;
  show_animations: boolean;
}

export async function getAppearanceSettings(): Promise<AppearanceSettings> {
  return apiCall('/api/settings/appearance');
}

export async function updateAppearanceSettings(settings: AppearanceSettings): Promise<AppearanceSettings> {
  return apiCall('/api/settings/appearance', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
}

// ==================== 3RD PARTY DATA ====================

// Economic Calendar
export interface EconomicEvent {
  id: string;
  time: string;
  currency: string;
  event: string;
  impact: 'high' | 'medium' | 'low';
  forecast?: string;
  previous?: string;
  actual?: string;
}

export interface EconomicCalendarResponse {
  events: EconomicEvent[];
  total: number;
  from_date: string;
  to_date: string;
}

export async function getEconomicCalendar(params?: {
  from_date?: string;
  to_date?: string;
  currencies?: string;
  impact?: string;
}): Promise<EconomicCalendarResponse> {
  const queryParams = new URLSearchParams();
  if (params?.from_date) queryParams.append('from_date', params.from_date);
  if (params?.to_date) queryParams.append('to_date', params.to_date);
  if (params?.currencies) queryParams.append('currencies', params.currencies);
  if (params?.impact) queryParams.append('impact', params.impact);

  const url = `/api/data/economic-calendar${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  return apiCall(url);
}

// Market News
export interface NewsArticle {
  id: string;
  title: string;
  description?: string;
  source: string;
  url: string;
  published_at: string;
  image_url?: string;
  category?: string;
}

export interface NewsResponse {
  articles: NewsArticle[];
  total: number;
  page: number;
  page_size: number;
}

export async function getNews(params?: {
  category?: string;
  query?: string;
  page?: number;
  page_size?: number;
}): Promise<NewsResponse> {
  const queryParams = new URLSearchParams();
  if (params?.category) queryParams.append('category', params.category);
  if (params?.query) queryParams.append('query', params.query);
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

  const url = `/api/data/news${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  return apiCall(url);
}

// RSS Feeds
export interface RSSFeed {
  id: string;
  name: string;
  url: string;
  category?: string;
  enabled: boolean;
  last_fetched?: string;
  created_at: string;
}

export interface RSSArticle {
  id: string;
  feed_id: string;
  feed_name: string;
  title: string;
  summary?: string;
  link: string;
  published: string;
}

export async function getRSSFeeds(): Promise<{ feeds: RSSFeed[] }> {
  return apiCall('/api/data/rss/feeds');
}

export async function addRSSFeed(name: string, url: string, category?: string): Promise<RSSFeed> {
  const queryParams = new URLSearchParams();
  queryParams.append('name', name);
  queryParams.append('url', url);
  if (category) queryParams.append('category', category);

  return apiCall(`/api/data/rss/feeds?${queryParams.toString()}`, {
    method: 'POST',
  });
}

export async function deleteRSSFeed(feedId: string): Promise<{ success: boolean; message: string }> {
  return apiCall(`/api/data/rss/feeds/${feedId}`, {
    method: 'DELETE',
  });
}

export async function getRSSArticles(feedId?: string, limit?: number): Promise<{ articles: RSSArticle[]; total: number }> {
  const queryParams = new URLSearchParams();
  if (feedId) queryParams.append('feed_id', feedId);
  if (limit) queryParams.append('limit', limit.toString());

  const url = `/api/data/rss/articles${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  return apiCall(url);
}

// Technical Indicators
export interface IndicatorData {
  symbol: string;
  timeframe: string;
  timestamp: string;
  indicators: Record<string, any>;
}

export async function getIndicators(symbol: string, timeframe: string = 'H1'): Promise<IndicatorData> {
  return apiCall(`/api/data/indicators/${symbol}?timeframe=${timeframe}`);
}

