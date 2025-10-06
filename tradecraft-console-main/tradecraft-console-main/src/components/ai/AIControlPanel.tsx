import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, Power, PowerOff, RefreshCw } from 'lucide-react';
import { getAIStatus, triggerKillSwitch } from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { AIStatus } from '@/lib/ai-types';

const AIControlPanel: React.FC = () => {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  async function loadStatus() {
    try {
      const data = await getAIStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to load AI status:', error);
      toast({
        title: 'Error',
        description: 'Failed to load AI status',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  async function handleKillSwitch() {
    if (!confirm('⚠️ Are you sure you want to disable ALL AI trading?\n\nThis will:\n- Stop all AI evaluations\n- Disable AI for all symbols\n- Cancel pending trade ideas\n\nThis action cannot be undone.')) {
      return;
    }

    try {
      await triggerKillSwitch('Manual kill switch activation from UI');
      toast({
        title: 'AI Trading Disabled',
        description: 'All AI trading has been stopped.',
        variant: 'destructive',
      });
      loadStatus();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to trigger kill switch',
        variant: 'destructive',
      });
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    await loadStatus();
  }

  if (loading) {
    return (
      <div className="trading-panel">
        <div className="trading-header">
          <h3 className="font-medium">AI Control Panel</h3>
        </div>
        <div className="trading-content">
          <div className="animate-pulse text-sm text-text-muted">Loading AI status...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="trading-panel">
      <div className="trading-header flex items-center justify-between">
        <h3 className="font-medium">AI Control Panel</h3>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleKillSwitch}
            className="gap-2"
            disabled={!status?.enabled}
          >
            <PowerOff className="w-4 h-4" />
            KILL SWITCH
          </Button>
        </div>
      </div>

      <div className="trading-content space-y-4">
        {/* Status Indicator */}
        <div className="flex items-center justify-between p-3 bg-panel-dark rounded border border-border">
          <span className="text-sm font-medium">Engine Status:</span>
          <div className="flex items-center gap-2">
            {status?.enabled ? (
              <>
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-sm text-green-400 font-medium">ACTIVE</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-sm text-red-400 font-medium">DISABLED</span>
              </>
            )}
          </div>
        </div>

        {/* Mode */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-text-secondary">Mode:</span>
          <span className="text-sm text-text-primary uppercase font-mono">
            {status?.mode || 'N/A'}
          </span>
        </div>

        {/* Active Trade Ideas */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-text-secondary">Active Trade Ideas:</span>
          <span className="text-sm font-mono text-text-primary">
            {status?.active_trade_ideas || 0}
          </span>
        </div>

        {/* Autonomy Loop */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-text-secondary">Autonomy Loop:</span>
          <div className="flex items-center gap-2">
            {status?.autonomy_loop_running ? (
              <>
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                <span className="text-xs text-blue-400">Running</span>
              </>
            ) : (
              <span className="text-xs text-text-muted">Stopped</span>
            )}
          </div>
        </div>

        {/* Enabled Symbols */}
        <div className="border-t border-border pt-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-text-secondary">Enabled Symbols:</span>
            <span className="text-xs text-text-muted">
              {status?.enabled_symbols?.length || 0} active
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {!status?.enabled_symbols || status.enabled_symbols.length === 0 ? (
              <div className="w-full text-center py-4">
                <AlertCircle className="w-8 h-8 mx-auto mb-2 text-text-muted opacity-50" />
                <p className="text-xs text-text-muted">No symbols enabled</p>
                <p className="text-xs text-text-muted mt-1">
                  Enable AI for symbols below to start monitoring
                </p>
              </div>
            ) : (
              status.enabled_symbols.map((sym) => (
                <span
                  key={sym}
                  className="px-3 py-1.5 bg-primary/20 text-primary text-xs rounded font-medium border border-primary/30"
                >
                  {sym}
                </span>
              ))
            )}
          </div>
        </div>

        {/* Warning Message */}
        {!status?.enabled && (
          <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-yellow-500">
                <p className="font-medium">AI Trading is currently disabled</p>
                <p className="mt-1 opacity-80">
                  Enable AI for specific symbols to start receiving trade ideas
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIControlPanel;

