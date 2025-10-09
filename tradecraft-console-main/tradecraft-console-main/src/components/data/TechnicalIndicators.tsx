import React, { useState, useEffect } from 'react';
import { TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { getSymbols, getIndicators, type IndicatorData } from '@/lib/api';

const TechnicalIndicators: React.FC = () => {
  const [symbols, setSymbols] = useState<any[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState('H1');
  const [indicatorData, setIndicatorData] = useState<IndicatorData | null>(null);
  const [loading, setLoading] = useState(true);

  const timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'];

  useEffect(() => {
    loadSymbols();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      loadIndicators();
    }
  }, [selectedSymbol, selectedTimeframe]);

  const loadSymbols = async () => {
    try {
      const data = await getSymbols();
      setSymbols(data);
      if (data.length > 0 && !selectedSymbol) {
        setSelectedSymbol(data[0].symbol);
      }
    } catch (error: any) {
      toast.error(`Failed to load symbols: ${error.message}`);
    }
  };

  const loadIndicators = async () => {
    setLoading(true);
    try {
      const data = await getIndicators(selectedSymbol, selectedTimeframe);
      setIndicatorData(data);
    } catch (error: any) {
      toast.error(`Failed to load indicators: ${error.message}`);
      setIndicatorData(null);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value: any): string => {
    if (typeof value === 'number') {
      return value.toFixed(5);
    }
    return String(value);
  };

  const getIndicatorColor = (name: string, value: number): string => {
    // RSI coloring
    if (name.toLowerCase().includes('rsi')) {
      if (value > 70) return 'text-red-500';
      if (value < 30) return 'text-green-500';
      return 'text-yellow-500';
    }

    // MACD coloring
    if (name.toLowerCase().includes('macd')) {
      return value > 0 ? 'text-green-500' : 'text-red-500';
    }

    return 'text-text-primary';
  };

  const renderIndicatorValue = (name: string, value: any) => {
    const formattedValue = formatValue(value);
    const color = typeof value === 'number' ? getIndicatorColor(name, value) : 'text-text-primary';

    return (
      <div className="flex items-center justify-between p-3 bg-panel-alt rounded">
        <span className="text-sm text-text-muted">{name}</span>
        <span className={`text-sm font-mono font-medium ${color}`}>{formattedValue}</span>
      </div>
    );
  };

  const renderIndicatorSection = (title: string, indicators: Record<string, any>) => {
    const entries = Object.entries(indicators);
    if (entries.length === 0) return null;

    return (
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-text-primary mb-3">{title}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {entries.map(([key, value]) => (
            <div key={key}>{renderIndicatorValue(key, value)}</div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold">Technical Indicators</h2>
        </div>
        <Button variant="outline" size="sm" onClick={loadIndicators} disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Symbol & Timeframe Selection */}
      <div className="bg-panel rounded-lg border border-border p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Symbol */}
          <div>
            <label className="text-xs text-text-muted mb-1 block">Symbol</label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded"
            >
              {symbols.map((symbol) => (
                <option key={symbol.symbol} value={symbol.symbol}>
                  {symbol.symbol}
                </option>
              ))}
            </select>
          </div>

          {/* Timeframe */}
          <div>
            <label className="text-xs text-text-muted mb-1 block">Timeframe</label>
            <div className="flex flex-wrap gap-1">
              {timeframes.map((tf) => (
                <button
                  key={tf}
                  onClick={() => setSelectedTimeframe(tf)}
                  className={`px-3 py-2 text-xs rounded transition-colors ${
                    selectedTimeframe === tf
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-panel-alt text-text-secondary hover:bg-panel-dark'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Indicators Display */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : !indicatorData ? (
          <Alert>
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              No indicator data available for {selectedSymbol}. Try selecting a different symbol or timeframe.
            </AlertDescription>
          </Alert>
        ) : (
          <div>
            {/* Header Info */}
            <div className="bg-panel rounded-lg border border-border p-4 mb-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-lg font-semibold text-text-primary">{indicatorData.symbol}</div>
                  <div className="text-xs text-text-muted">
                    Timeframe: {indicatorData.timeframe} • Updated:{' '}
                    {new Date(indicatorData.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Indicators */}
            {indicatorData.indicators && (
              <div>
                {/* Moving Averages */}
                {(indicatorData.indicators.ema_fast !== undefined ||
                  indicatorData.indicators.ema_slow !== undefined) && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-text-primary mb-3">Moving Averages</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {indicatorData.indicators.ema_fast !== undefined &&
                        renderIndicatorValue('EMA Fast', indicatorData.indicators.ema_fast)}
                      {indicatorData.indicators.ema_slow !== undefined &&
                        renderIndicatorValue('EMA Slow', indicatorData.indicators.ema_slow)}
                    </div>
                  </div>
                )}

                {/* Momentum Indicators */}
                {indicatorData.indicators.rsi !== undefined && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-text-primary mb-3">Momentum</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {renderIndicatorValue('RSI', indicatorData.indicators.rsi)}
                    </div>
                  </div>
                )}

                {/* MACD */}
                {(indicatorData.indicators.macd !== undefined ||
                  indicatorData.indicators.macd_signal !== undefined ||
                  indicatorData.indicators.macd_hist !== undefined) && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-text-primary mb-3">MACD</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {indicatorData.indicators.macd !== undefined &&
                        renderIndicatorValue('MACD', indicatorData.indicators.macd)}
                      {indicatorData.indicators.macd_signal !== undefined &&
                        renderIndicatorValue('MACD Signal', indicatorData.indicators.macd_signal)}
                      {indicatorData.indicators.macd_hist !== undefined &&
                        renderIndicatorValue('MACD Histogram', indicatorData.indicators.macd_hist)}
                    </div>
                  </div>
                )}

                {/* Volatility */}
                {(indicatorData.indicators.atr !== undefined ||
                  indicatorData.indicators.atr_median !== undefined) && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-text-primary mb-3">Volatility</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {indicatorData.indicators.atr !== undefined &&
                        renderIndicatorValue('ATR', indicatorData.indicators.atr)}
                      {indicatorData.indicators.atr_median !== undefined &&
                        renderIndicatorValue('ATR Median', indicatorData.indicators.atr_median)}
                    </div>
                  </div>
                )}

                {/* Other Indicators */}
                {Object.keys(indicatorData.indicators).length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-text-primary mb-3">All Indicators</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {Object.entries(indicatorData.indicators).map(([key, value]) => (
                        <div key={key}>{renderIndicatorValue(key.toUpperCase(), value)}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TechnicalIndicators;

