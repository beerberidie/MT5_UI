import React, { useState, useEffect } from 'react';
import { Brain, AlertCircle } from 'lucide-react';
import { getAIStatus } from '@/lib/api';
import type { AIStatus } from '@/lib/ai-types';
import { Link } from 'react-router-dom';

const AIStatusIndicator: React.FC = () => {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  async function loadStatus() {
    try {
      const data = await getAIStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to load AI status:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="px-4 py-3 border-t border-border">
        <div className="flex items-center gap-3 text-text-muted">
          <Brain className="w-5 h-5 animate-pulse" />
          <div className="text-sm">Loading...</div>
        </div>
      </div>
    );
  }

  const isEnabled = status?.enabled || false;
  const symbolCount = status?.enabled_symbols?.length || 0;
  const tradeIdeasCount = status?.active_trade_ideas || 0;

  return (
    <Link to="/ai" className="block px-4 py-3 border-t border-border hover:bg-panel-dark transition-colors">
      <div className="flex items-center gap-3">
        {/* AI Icon with Status Indicator */}
        <div className="relative">
          <Brain className={`w-5 h-5 ${isEnabled ? 'text-primary' : 'text-text-muted'}`} />
          {isEnabled && (
            <div className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          )}
        </div>

        {/* Status Text */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium ${isEnabled ? 'text-text-primary' : 'text-text-muted'}`}>
              AI Trading
            </span>
            {!isEnabled && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                OFF
              </span>
            )}
          </div>
          
          {isEnabled && (
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-text-muted">
                {symbolCount} {symbolCount === 1 ? 'symbol' : 'symbols'}
              </span>
              {tradeIdeasCount > 0 && (
                <>
                  <span className="text-xs text-text-muted">•</span>
                  <span className="text-xs text-primary font-medium">
                    {tradeIdeasCount} {tradeIdeasCount === 1 ? 'idea' : 'ideas'}
                  </span>
                </>
              )}
            </div>
          )}
        </div>

        {/* Badge for Trade Ideas */}
        {tradeIdeasCount > 0 && (
          <div className="flex-shrink-0">
            <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
              {tradeIdeasCount > 9 ? '9+' : tradeIdeasCount}
            </div>
          </div>
        )}
      </div>
    </Link>
  );
};

export default AIStatusIndicator;

