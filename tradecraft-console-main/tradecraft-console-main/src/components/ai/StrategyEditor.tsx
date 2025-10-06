import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Save, RefreshCw, AlertCircle } from 'lucide-react';
import { getStrategy, saveStrategy } from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { EMNRStrategy } from '@/lib/ai-types';

interface StrategyEditorProps {
  symbol: string;
  onSave?: () => void;
}

const StrategyEditor: React.FC<StrategyEditorProps> = ({ symbol, onSave }) => {
  const [strategy, setStrategy] = useState<EMNRStrategy | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStrategy();
  }, [symbol]);

  async function loadStrategy() {
    setLoading(true);
    setError(null);
    try {
      const data = await getStrategy(symbol);
      setStrategy(data);
    } catch (error: any) {
      console.error('Failed to load strategy:', error);

      // Check if it's a 404 error (strategy not found)
      if (error.message && error.message.includes('404')) {
        setError(`No strategy found for ${symbol}. Create one to get started.`);
        setStrategy(null);
      } else {
        setError(`Failed to load strategy: ${error.message || 'Unknown error'}`);
        toast({
          title: 'Error',
          description: `Failed to load strategy for ${symbol}`,
          variant: 'destructive',
        });
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!strategy) return;

    setSaving(true);
    try {
      await saveStrategy(symbol, strategy);
      toast({
        title: 'Strategy Saved',
        description: `Strategy for ${symbol} has been saved successfully`,
      });
      if (onSave) onSave();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save strategy',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="trading-panel">
        <div className="trading-header">
          <h3 className="font-medium">Strategy Editor - {symbol}</h3>
        </div>
        <div className="trading-content">
          <div className="animate-pulse text-sm text-text-muted">Loading strategy...</div>
        </div>
      </div>
    );
  }

  if (!strategy) {
    return (
      <div className="trading-panel">
        <div className="trading-header flex items-center justify-between">
          <h3 className="font-medium">Strategy Editor - {symbol}</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={loadStrategy}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Retry
          </Button>
        </div>
        <div className="trading-content">
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertCircle className="w-12 h-12 text-yellow-500 opacity-50 mb-3" />
            <p className="text-sm text-text-primary font-medium mb-2">
              {error || `No strategy found for ${symbol}`}
            </p>
            <p className="text-xs text-text-muted mt-2 max-w-md">
              To create a strategy for {symbol}, add a file at:<br />
              <code className="text-xs bg-panel-dark px-2 py-1 rounded mt-1 inline-block">
                config/ai/strategies/{symbol}_H1.json
              </code>
            </p>
            <p className="text-xs text-text-muted mt-3">
              You can copy the EURUSD_H1.json file as a template and modify the parameters.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="trading-panel">
      <div className="trading-header flex items-center justify-between">
        <h3 className="font-medium">Strategy Editor - {symbol}</h3>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={loadStrategy}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handleSave}
            disabled={saving}
            className="gap-2"
          >
            <Save className="w-4 h-4" />
            Save
          </Button>
        </div>
      </div>

      <div className="trading-content space-y-4">
        {/* Basic Info */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="strategy-symbol" className="text-xs text-text-muted mb-1 block">Symbol</label>
            <input
              id="strategy-symbol"
              type="text"
              value={strategy.symbol}
              disabled
              aria-label="Strategy symbol"
              className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
            />
          </div>
          <div>
            <label htmlFor="strategy-timeframe" className="text-xs text-text-muted mb-1 block">Timeframe</label>
            <input
              id="strategy-timeframe"
              type="text"
              value={strategy.timeframe}
              disabled
              aria-label="Strategy timeframe"
              className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
            />
          </div>
        </div>

        {/* Indicator Parameters */}
        <div className="border-t border-border pt-4">
          <h4 className="text-sm font-medium text-text-secondary mb-3">Indicator Parameters</h4>
          
          {/* EMA */}
          {strategy.indicators.ema && (
            <div className="mb-4">
              <div className="text-xs text-text-muted mb-2">EMA (Exponential Moving Average)</div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Fast Period</label>
                  <input
                    type="number"
                    value={strategy.indicators.ema.fast}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      indicators: {
                        ...strategy.indicators,
                        ema: { ...strategy.indicators.ema!, fast: parseInt(e.target.value) }
                      }
                    })}
                    className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
                  />
                </div>
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Slow Period</label>
                  <input
                    type="number"
                    value={strategy.indicators.ema.slow}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      indicators: {
                        ...strategy.indicators,
                        ema: { ...strategy.indicators.ema!, slow: parseInt(e.target.value) }
                      }
                    })}
                    className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
                  />
                </div>
              </div>
            </div>
          )}

          {/* RSI */}
          {strategy.indicators.rsi && (
            <div className="mb-4">
              <div className="text-xs text-text-muted mb-2">RSI (Relative Strength Index)</div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Period</label>
                  <input
                    type="number"
                    value={strategy.indicators.rsi.period}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      indicators: {
                        ...strategy.indicators,
                        rsi: { ...strategy.indicators.rsi!, period: parseInt(e.target.value) }
                      }
                    })}
                    className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
                  />
                </div>
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Overbought</label>
                  <input
                    type="number"
                    value={strategy.indicators.rsi.overbought}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      indicators: {
                        ...strategy.indicators,
                        rsi: { ...strategy.indicators.rsi!, overbought: parseInt(e.target.value) }
                      }
                    })}
                    className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
                  />
                </div>
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Oversold</label>
                  <input
                    type="number"
                    value={strategy.indicators.rsi.oversold}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      indicators: {
                        ...strategy.indicators,
                        rsi: { ...strategy.indicators.rsi!, oversold: parseInt(e.target.value) }
                      }
                    })}
                    className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ATR */}
          {strategy.indicators.atr && (
            <div className="mb-4">
              <div className="text-xs text-text-muted mb-2">ATR (Average True Range)</div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Period</label>
                  <input
                    type="number"
                    value={strategy.indicators.atr.period}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      indicators: {
                        ...strategy.indicators,
                        atr: { ...strategy.indicators.atr!, period: parseInt(e.target.value) }
                      }
                    })}
                    className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
                  />
                </div>
                <div>
                  <label className="text-xs text-text-muted mb-1 block">Multiplier</label>
                  <input
                    type="number"
                    step="0.1"
                    value={strategy.indicators.atr.multiplier}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      indicators: {
                        ...strategy.indicators,
                        atr: { ...strategy.indicators.atr!, multiplier: parseFloat(e.target.value) }
                      }
                    })}
                    className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Strategy Settings */}
        <div className="border-t border-border pt-4">
          <h4 className="text-sm font-medium text-text-secondary mb-3">Strategy Settings</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="strategy-direction" className="text-xs text-text-muted mb-1 block">Direction</label>
              <select
                id="strategy-direction"
                value={strategy.strategy.direction}
                onChange={(e) => setStrategy({
                  ...strategy,
                  strategy: { ...strategy.strategy, direction: e.target.value as any }
                })}
                aria-label="Trading direction"
                className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
              >
                <option value="long">Long Only</option>
                <option value="short">Short Only</option>
                <option value="both">Both</option>
              </select>
            </div>
            <div>
              <label htmlFor="strategy-min-rr" className="text-xs text-text-muted mb-1 block">Min RR Ratio</label>
              <input
                id="strategy-min-rr"
                type="number"
                step="0.1"
                value={strategy.strategy.min_rr}
                onChange={(e) => setStrategy({
                  ...strategy,
                  strategy: { ...strategy.strategy, min_rr: parseFloat(e.target.value) }
                })}
                aria-label="Minimum risk-reward ratio"
                className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
              />
            </div>
          </div>
        </div>

        {/* Info Note */}
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-blue-400">
              <p className="font-medium">Advanced Configuration</p>
              <p className="mt-1 opacity-80">
                For advanced EMNR condition editing, modify the strategy JSON file directly at:
                config/ai/strategies/{symbol}_{strategy.timeframe}.json
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyEditor;

