import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SettingsProvider } from '@/lib/settings-context';

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <SettingsProvider>{children}</SettingsProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };

// Mock data generators
export const mockTradeIdea = (overrides = {}) => ({
  id: 'test-idea-123',
  timestamp: '2025-10-10T10:00:00Z',
  symbol: 'EURUSD',
  timeframe: 'H1',
  confidence: 85,
  action: 'open_or_scale',
  direction: 'long' as const,
  entry_price: 1.1000,
  stop_loss: 1.0950,
  take_profit: 1.1100,
  volume: 0.1,
  rr_ratio: 2.0,
  emnr_flags: {
    entry: true,
    strong: true,
    weak: false,
    exit: false,
    align: true,
  },
  indicators: {
    ema_fast: 1.0995,
    ema_slow: 1.0980,
    rsi: 65,
    macd: 0.0005,
    macd_signal: 0.0003,
    atr: 0.0015,
    atr_median: 0.0014,
    bb_upper: 1.1020,
    bb_middle: 1.1000,
    bb_lower: 1.0980,
  },
  execution_plan: {
    action: 'open_or_scale',
    riskPct: 0.01,
  },
  status: 'pending_approval' as const,
  notes: 'Test trade idea',
  ...overrides,
});

export const mockAIStatus = (overrides = {}) => ({
  enabled: true,
  mode: 'semi-auto',
  enabled_symbols: ['EURUSD', 'GBPUSD'],
  active_trade_ideas: 2,
  autonomy_loop_running: false,
  ...overrides,
});

export const mockAutonomyStatus = (overrides = {}) => ({
  running: false,
  interval_minutes: 15,
  enabled_symbols_count: 2,
  evaluation_count: 10,
  error_count: 0,
  last_evaluation_time: '2025-10-10T10:00:00Z',
  next_run_time: null,
  ...overrides,
});

export const mockSymbol = (overrides = {}) => ({
  symbol: 'EURUSD',
  bid: 1.1000,
  ask: 1.1002,
  spread: 2,
  change: 0.0010,
  changePercent: 0.09,
  ...overrides,
});

export const mockAccount = (overrides = {}) => ({
  balance: 10000,
  equity: 10050,
  margin: 100,
  margin_free: 9950,
  margin_level: 10050,
  leverage: 100,
  currency: 'USD',
  ...overrides,
});

export const mockPosition = (overrides = {}) => ({
  ticket: 12345,
  symbol: 'EURUSD',
  type: 0, // 0 = buy, 1 = sell
  volume: 0.1,
  openPrice: 1.1000,
  currentPrice: 1.1010,
  profit: 10.0,
  swap: 0.0,
  commission: 0.0,
  ...overrides,
});

export const mockAPIIntegration = (overrides = {}) => ({
  id: 'test-integration-123',
  name: 'Test API',
  type: 'custom' as const,
  base_url: 'https://api.example.com',
  config: {},
  status: 'active' as const,
  last_tested: '2025-10-10T10:00:00Z',
  created_at: '2025-10-10T09:00:00Z',
  ...overrides,
});

// Mock fetch responses
export const mockFetchSuccess = (data: any) => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(data),
    } as Response)
  );
};

export const mockFetchError = (status: number, message: string) => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: false,
      status,
      json: () => Promise.resolve({ detail: message }),
    } as Response)
  );
};

// Wait for async updates
export const waitForAsync = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

