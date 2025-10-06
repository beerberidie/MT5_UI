import React, { useEffect, useMemo, useState } from 'react';
import { useSettings } from '@/lib/settings-context';
import {
  getAccount,
  getPositions,
  getDeals,
  getOrdersHistory,
  getPrioritySymbols,
  getHistoricalBars,
} from '@/lib/api';

// Simple types inferred from api responses
interface Account { balance?: number; equity?: number; profit?: number; }
interface Position { symbol: string; volume: number; profit?: number; side?: 'buy' | 'sell'; }
interface Deal { symbol: string; profit?: number; time?: string; volume?: number; }
interface SymbolInfo { symbol: string; bid?: number; ask?: number; change?: number; trend?: 'up' | 'down' | 'flat'; }

const Analysis: React.FC = () => {
  const { risk } = useSettings();

  const [account, setAccount] = useState<Account | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [ordersSummary, setOrdersSummary] = useState<any[]>([]);
  const [symbols, setSymbols] = useState<SymbolInfo[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [bars, setBars] = useState<any[]>([]);
  const [barsLoading, setBarsLoading] = useState(false);
  const [barsError, setBarsError] = useState<string | null>(null);

  async function refreshAll() {
    try {
      setLoading(true);
      setError(null);
      const [acct, poss, dls, syms] = await Promise.all([
        getAccount(),
        getPositions(),
        getDeals({}),
        getPrioritySymbols(),
      ]);
      setAccount(acct || {});
      setPositions(Array.isArray(poss) ? poss : []);
      setDeals(Array.isArray(dls) ? dls : []);
      setSymbols(Array.isArray(syms) ? syms : []);
      setSelectedSymbol((prev) => prev || (Array.isArray(syms) && syms[0]?.symbol) || '');

      // Optional orders history summary (last day)
      try {
        const end = new Date();
        const start = new Date(end.getTime() - 24 * 3600 * 1000);
        const orders = await getOrdersHistory({
          date_from: start.toISOString(),
          date_to: end.toISOString()
        });
        setOrdersSummary(Array.isArray(orders) ? orders : []);
      } catch (e) {
        // non-fatal
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load analysis data');
    } finally {
      setLoading(false);
    }
  }

  async function loadBars(sym: string) {
    if (!sym) return;
    try {
      setBarsLoading(true);
      setBarsError(null);
      // Try count-first
      let arr: any[] = [];
      try {
        const resCount = await getHistoricalBars({ symbol: sym, timeframe: 'H1', count: 120 });
        arr = Array.isArray(resCount) ? resCount : (resCount as any)?.bars || [];
      } catch {}
      if (!arr || arr.length === 0) {
        const end = new Date();
        const start = new Date(end.getTime() - 48 * 3600 * 1000);
        const resRange = await getHistoricalBars({ symbol: sym, timeframe: 'H1', date_from: start.toISOString(), date_to: end.toISOString() });
        arr = Array.isArray(resRange) ? resRange : (resRange as any)?.bars || [];
      }
      setBars(arr);
    } catch (e: any) {
      setBarsError(e?.message || 'Failed to load bars');
    } finally {
      setBarsLoading(false);
    }
  }

  useEffect(() => {
    refreshAll();
    const id = setInterval(refreshAll, 5000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (selectedSymbol) loadBars(selectedSymbol);
  }, [selectedSymbol]);

  const perf = useMemo(() => {
    let wins = 0, losses = 0, profitSum = 0;
    for (const d of deals) {
      const p = Number(d?.profit || 0);
      profitSum += p;
      if (p > 0) wins++; else if (p < 0) losses++;
    }
    const total = wins + losses;
    const winRate = total > 0 ? (wins / total) * 100 : 0;
    return { wins, losses, profitSum, winRate: Number(winRate.toFixed(1)) };
  }, [deals]);

  const riskExposure = useMemo(() => {
    const vol = positions.reduce((s, p) => s + Number(p.volume || 0), 0);
    const floating = positions.reduce((s, p) => s + Number(p.profit || 0), 0);
    return { totalVolume: vol, floatingPL: floating };
  }, [positions]);

  return (
    <div className="min-h-screen bg-background text-text-primary">
      <div className="h-header bg-panel border-b border-border flex items-center px-4">
        <h1 className="text-lg font-semibold">Analysis & Performance</h1>
        <div className="ml-auto text-xs text-text-muted">
          {loading && <span className="animate-pulse">Refreshing...</span>}
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Market Overview */}
        <div className="trading-panel">
          <div className="trading-header">
            <h3 className="font-medium text-base">📊 Market Overview</h3>
            <p className="text-xs text-text-muted mt-1">Top priority symbols from your watchlist</p>
          </div>
          <div className="trading-content">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                  <div className="text-sm text-text-muted">Loading market data...</div>
                </div>
              </div>
            ) : error ? (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                <div className="text-sm text-red-400">⚠️ {error}</div>
              </div>
            ) : symbols.length === 0 ? (
              <div className="text-center py-8 text-text-muted">
                <div className="text-4xl mb-2">📈</div>
                <div className="text-sm">No symbols available</div>
                <div className="text-xs mt-1">Add symbols to your MT5 Market Watch</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {symbols.slice(0, 9).map((s) => (
                  <div key={s.symbol} className="flex items-center justify-between bg-card border border-border rounded-lg p-3 hover:border-primary/50 transition-colors">
                    <div className="flex items-center gap-2">
                      <div className="font-semibold text-base">{s.symbol}</div>
                      <div className="text-xs text-text-muted">{(s as any).trend || '—'}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono tabular-nums text-sm">{Number((s as any).bid ?? 0).toFixed(5)}</div>
                      <div className={"text-xs font-medium " + ((s as any).change > 0 ? 'text-green-400' : (s as any).change < 0 ? 'text-red-400' : 'text-text-muted')}>
                        {(s as any).change > 0 ? '+' : ''}{Number((s as any).change || 0).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Performance Analytics */}
        <div className="trading-panel">
          <div className="trading-header">
            <h3 className="font-medium text-base">💰 Performance Analytics</h3>
            <p className="text-xs text-text-muted mt-1">Account performance and trading statistics</p>
          </div>
          <div className="trading-content">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors">
                <div className="text-xs text-text-secondary uppercase tracking-wide mb-1">Balance</div>
                <div className="font-mono text-xl font-semibold">${Number(account?.balance || 0).toFixed(2)}</div>
              </div>
              <div className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors">
                <div className="text-xs text-text-secondary uppercase tracking-wide mb-1">Equity</div>
                <div className="font-mono text-xl font-semibold">${Number(account?.equity || 0).toFixed(2)}</div>
              </div>
              <div className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors">
                <div className="text-xs text-text-secondary uppercase tracking-wide mb-1">Total Profit</div>
                <div className={"font-mono text-xl font-semibold " + ((perf.profitSum || 0) >= 0 ? 'text-green-400' : 'text-red-400')}>
                  {(perf.profitSum || 0) >= 0 ? '+' : ''}${perf.profitSum.toFixed(2)}
                </div>
              </div>
              <div className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors">
                <div className="text-xs text-text-secondary uppercase tracking-wide mb-1">Win Rate</div>
                <div className={"font-mono text-xl font-semibold " + (perf.winRate >= 50 ? 'text-green-400' : 'text-yellow-400')}>
                  {perf.winRate}%
                </div>
                <div className="text-xs text-text-muted mt-1">{perf.wins}W / {perf.losses}L</div>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Analysis */}
        <div className="trading-panel">
          <div className="trading-header">
            <h3 className="font-medium text-base">⚠️ Risk Analysis</h3>
            <p className="text-xs text-text-muted mt-1">Risk management settings and current exposure</p>
          </div>
          <div className="trading-content space-y-4">
            <div>
              <div className="text-xs text-text-secondary uppercase tracking-wide mb-2">Risk Settings</div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-card border border-border rounded-lg p-3">
                  <div className="text-xs text-text-secondary mb-1">Default Risk %</div>
                  <div className="font-mono text-lg font-semibold">{risk.defaultRiskPercent}%</div>
                </div>
                <div className="bg-card border border-border rounded-lg p-3">
                  <div className="text-xs text-text-secondary mb-1">Max Risk %</div>
                  <div className="font-mono text-lg font-semibold text-yellow-400">{risk.maxRiskPercent}%</div>
                </div>
                <div className="bg-card border border-border rounded-lg p-3">
                  <div className="text-xs text-text-secondary mb-1">R/R Target</div>
                  <div className="font-mono text-lg font-semibold text-blue-400">{risk.rrTarget}x</div>
                </div>
              </div>
            </div>
            <div>
              <div className="text-xs text-text-secondary uppercase tracking-wide mb-2">Current Exposure</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="bg-card border border-border rounded-lg p-3">
                  <div className="text-xs text-text-secondary mb-1">Open Volume (lots)</div>
                  <div className="font-mono text-lg font-semibold">{riskExposure.totalVolume.toFixed(2)}</div>
                  <div className="text-xs text-text-muted mt-1">{positions.length} open position{positions.length !== 1 ? 's' : ''}</div>
                </div>
                <div className="bg-card border border-border rounded-lg p-3">
                  <div className="text-xs text-text-secondary mb-1">Floating P/L</div>
                  <div className={"font-mono text-lg font-semibold " + (riskExposure.floatingPL >= 0 ? 'text-green-400' : 'text-red-400')}>
                    {riskExposure.floatingPL >= 0 ? '+' : ''}${riskExposure.floatingPL.toFixed(2)}
                  </div>
                  <div className="text-xs text-text-muted mt-1">Unrealized profit/loss</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Historical Data Visualization */}
        <div className="trading-panel">
          <div className="trading-header">
            <h3 className="font-medium text-base">📜 Trading History</h3>
            <p className="text-xs text-text-muted mt-1">Recent closed deals and transactions</p>
          </div>
          <div className="trading-content space-y-3">
            {deals.length === 0 ? (
              <div className="text-center py-8 text-text-muted">
                <div className="text-4xl mb-2">📋</div>
                <div className="text-sm">No trading history available</div>
                <div className="text-xs mt-1">Execute some trades to see your history here</div>
              </div>
            ) : (
              <>
                <div className="text-xs text-text-secondary uppercase tracking-wide">Recent Deals (Latest 10)</div>
                <div className="overflow-auto border border-border rounded-lg">
                  <table className="w-full text-sm">
                    <thead className="bg-card border-b border-border">
                      <tr>
                        <th className="text-left p-3 font-medium">Time</th>
                        <th className="text-left p-3 font-medium">Symbol</th>
                        <th className="text-right p-3 font-medium">Volume</th>
                        <th className="text-right p-3 font-medium">Profit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {deals.slice(0, 10).map((d, idx) => (
                        <tr key={idx} className="border-b border-border/50 hover:bg-card/50 transition-colors">
                          <td className="p-3 text-xs text-text-secondary">{d.time || '—'}</td>
                          <td className="p-3 font-medium">{d.symbol}</td>
                          <td className="p-3 text-right font-mono">{Number(d.volume || 0).toFixed(2)}</td>
                          <td className={'p-3 text-right font-mono font-semibold ' + (Number(d.profit || 0) >= 0 ? 'text-green-400' : 'text-red-400')}>
                            {Number(d.profit || 0) >= 0 ? '+' : ''}${Number(d.profit || 0).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Symbol Analysis */}
        <div className="trading-panel">
          <div className="trading-header">
            <h3 className="font-medium text-base">📈 Symbol Analysis</h3>
            <p className="text-xs text-text-muted mt-1">Historical price data and candlestick patterns</p>
          </div>
          <div className="trading-content space-y-4">
            <div className="flex items-center gap-3 bg-card border border-border rounded-lg p-3">
              <label htmlFor="analysis-symbol-select" className="text-sm font-medium text-text-secondary">Select Symbol:</label>
              <select
                id="analysis-symbol-select"
                aria-label="Select symbol for analysis"
                className="bg-panel border border-border rounded-lg px-3 py-2 text-sm font-medium hover:border-primary/50 transition-colors flex-1 max-w-xs"
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
              >
                {symbols.length === 0 ? (
                  <option value="">No symbols available</option>
                ) : (
                  symbols.map((s) => (
                    <option key={s.symbol} value={s.symbol}>{s.symbol}</option>
                  ))
                )}
              </select>
              {selectedSymbol && (
                <div className="text-xs text-text-muted">
                  Showing H1 bars (last 120)
                </div>
              )}
            </div>

            {barsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                  <div className="text-sm text-text-muted">Loading price data...</div>
                </div>
              </div>
            ) : barsError ? (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                <div className="text-sm text-red-400">⚠️ {barsError}</div>
              </div>
            ) : bars.length === 0 ? (
              <div className="text-center py-8 text-text-muted">
                <div className="text-4xl mb-2">📊</div>
                <div className="text-sm">No historical data available</div>
                <div className="text-xs mt-1">Select a symbol to view price history</div>
              </div>
            ) : (
              <>
                <div className="text-xs text-text-secondary uppercase tracking-wide">
                  Historical Bars (Latest 30 of {bars.length})
                </div>
                <div className="overflow-auto border border-border rounded-lg max-h-96">
                  <table className="w-full text-sm">
                    <thead className="bg-card border-b border-border sticky top-0">
                      <tr>
                        <th className="text-left p-3 font-medium">Time</th>
                        <th className="text-right p-3 font-medium">Open</th>
                        <th className="text-right p-3 font-medium">High</th>
                        <th className="text-right p-3 font-medium">Low</th>
                        <th className="text-right p-3 font-medium">Close</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bars.slice(0, 30).map((b, i) => {
                        const open = Number(b?.open ?? 0);
                        const close = Number(b?.close ?? 0);
                        const isBullish = close >= open;
                        return (
                          <tr key={i} className="border-b border-border/50 hover:bg-card/50 transition-colors">
                            <td className="p-3 text-xs text-text-secondary">{b?.time || '—'}</td>
                            <td className="p-3 text-right font-mono">{open.toFixed(5)}</td>
                            <td className="p-3 text-right font-mono text-green-400">{Number(b?.high ?? 0).toFixed(5)}</td>
                            <td className="p-3 text-right font-mono text-red-400">{Number(b?.low ?? 0).toFixed(5)}</td>
                            <td className={"p-3 text-right font-mono font-semibold " + (isBullish ? 'text-green-400' : 'text-red-400')}>
                              {close.toFixed(5)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;

