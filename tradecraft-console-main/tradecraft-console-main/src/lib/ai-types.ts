// TypeScript type definitions for AI Trading System

export interface EMNRFlags {
  entry: boolean;
  exit: boolean;
  strong: boolean;
  weak: boolean;
}

export interface IndicatorValues {
  ema_fast: number;
  ema_slow: number;
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_hist: number;
  atr: number;
  atr_median: number;
}

export interface ExecutionPlan {
  action: 'observe' | 'pending_only' | 'wait_rr' | 'open_or_scale';
  riskPct: number;
}

export interface TradeIdea {
  id: string;
  timestamp: string;
  symbol: string;
  timeframe: string;
  confidence: number;
  action: 'observe' | 'pending_only' | 'wait_rr' | 'open_or_scale';
  direction: 'long' | 'short';
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  volume: number;
  rr_ratio: number;
  emnr_flags: EMNRFlags;
  indicators: IndicatorValues;
  execution_plan: ExecutionPlan;
  status: 'pending_approval' | 'approved' | 'rejected' | 'executed' | 'cancelled';
}

export interface AIStatus {
  enabled: boolean;
  mode: 'semi-auto' | 'full-auto' | 'manual';
  enabled_symbols: string[];
  active_trade_ideas: number;
  autonomy_loop_running: boolean;
}

export interface IndicatorConfig {
  ema?: {
    fast: number;
    slow: number;
  };
  rsi?: {
    period: number;
    overbought: number;
    oversold: number;
  };
  macd?: {
    fast: number;
    slow: number;
    signal: number;
  };
  atr?: {
    period: number;
    multiplier: number;
  };
}

export interface EMNRConditions {
  entry: string[];
  exit: string[];
  strong: string[];
  weak: string[];
}

export interface StrategySettings {
  direction: 'long' | 'short' | 'both';
  min_rr: number;
  news_embargo_minutes: number;
  invalidations?: string[];
}

export interface EMNRStrategy {
  symbol: string;
  timeframe: string;
  sessions: string[];
  indicators: IndicatorConfig;
  conditions: EMNRConditions;
  strategy: StrategySettings;
}

export interface SymbolProfile {
  symbol: string;
  bestSessions: string[];
  bestTimeframes: string[];
  externalDrivers?: string[];
  style: {
    bias: string;
    rrTarget: number;
    maxRiskPct: number;
  };
  management: {
    breakevenAfterRR: number;
    partialAtRR: number;
    trailUsingATR: boolean;
    atrMultiplier: number;
  };
  invalidations?: string[];
}

export interface AIDecision {
  timestamp: string;
  symbol: string;
  timeframe: string;
  confidence: number;
  action: string;
  direction: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  rr_ratio: number;
  emnr_entry: boolean;
  emnr_exit: boolean;
  emnr_strong: boolean;
  emnr_weak: boolean;
}

// Helper type for confidence level classification
export type ConfidenceLevel = 'very-low' | 'low' | 'medium' | 'high' | 'very-high';

export function getConfidenceLevel(confidence: number): ConfidenceLevel {
  if (confidence < 20) return 'very-low';
  if (confidence < 40) return 'low';
  if (confidence < 60) return 'medium';
  if (confidence < 80) return 'high';
  return 'very-high';
}

export function getConfidenceColor(confidence: number): string {
  const level = getConfidenceLevel(confidence);
  switch (level) {
    case 'very-low': return 'text-red-500';
    case 'low': return 'text-orange-500';
    case 'medium': return 'text-yellow-500';
    case 'high': return 'text-green-500';
    case 'very-high': return 'text-emerald-500';
  }
}

export function getActionLabel(action: string): string {
  switch (action) {
    case 'observe': return 'Observe';
    case 'pending_only': return 'Pending Only';
    case 'wait_rr': return 'Wait for RR';
    case 'open_or_scale': return 'Execute';
    default: return action;
  }
}

export function getActionColor(action: string): string {
  switch (action) {
    case 'observe': return 'text-text-muted';
    case 'pending_only': return 'text-yellow-500';
    case 'wait_rr': return 'text-orange-500';
    case 'open_or_scale': return 'text-green-500';
    default: return 'text-text-secondary';
  }
}

