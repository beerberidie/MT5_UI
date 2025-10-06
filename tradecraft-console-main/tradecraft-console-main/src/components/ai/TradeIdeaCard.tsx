import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  TrendingDown, 
  CheckCircle, 
  XCircle, 
  Clock,
  Target,
  Shield,
  Activity
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import type { TradeIdea } from '@/lib/ai-types';
import { getConfidenceColor, getActionLabel, getActionColor } from '@/lib/ai-types';

interface TradeIdeaCardProps {
  tradeIdea: TradeIdea;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
}

const TradeIdeaCard: React.FC<TradeIdeaCardProps> = ({ tradeIdea, onApprove, onReject }) => {
  const [processing, setProcessing] = useState(false);

  const handleApprove = async () => {
    if (!onApprove) return;
    setProcessing(true);
    try {
      await onApprove(tradeIdea.id);
      toast({
        title: 'Trade Idea Approved',
        description: `${tradeIdea.symbol} ${tradeIdea.direction.toUpperCase()} trade approved`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to approve trade idea',
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!onReject) return;
    setProcessing(true);
    try {
      await onReject(tradeIdea.id);
      toast({
        title: 'Trade Idea Rejected',
        description: `${tradeIdea.symbol} trade idea rejected`,
        variant: 'destructive',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to reject trade idea',
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  const isLong = tradeIdea.direction === 'long';
  const DirectionIcon = isLong ? TrendingUp : TrendingDown;
  const directionColor = isLong ? 'text-green-500' : 'text-red-500';
  const directionBg = isLong ? 'bg-green-500/10' : 'bg-red-500/10';
  const directionBorder = isLong ? 'border-green-500/30' : 'border-red-500/30';

  return (
    <div className="trading-panel border-l-4" style={{ borderLeftColor: isLong ? '#22c55e' : '#ef4444' }}>
      {/* Header */}
      <div className="trading-header flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded ${directionBg} ${directionBorder} border`}>
            <DirectionIcon className={`w-5 h-5 ${directionColor}`} />
          </div>
          <div>
            <h3 className="font-medium text-lg">{tradeIdea.symbol}</h3>
            <p className="text-xs text-text-muted">{tradeIdea.timeframe} • {new Date(tradeIdea.timestamp).toLocaleString()}</p>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-2xl font-bold ${getConfidenceColor(tradeIdea.confidence)}`}>
            {tradeIdea.confidence}
          </div>
          <div className="text-xs text-text-muted">Confidence</div>
        </div>
      </div>

      <div className="trading-content space-y-4">
        {/* Direction & Action */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-text-muted mb-1">Direction</div>
            <div className={`text-sm font-medium ${directionColor} uppercase`}>
              {tradeIdea.direction}
            </div>
          </div>
          <div>
            <div className="text-xs text-text-muted mb-1">Action</div>
            <div className={`text-sm font-medium ${getActionColor(tradeIdea.action)}`}>
              {getActionLabel(tradeIdea.action)}
            </div>
          </div>
        </div>

        {/* Price Levels */}
        <div className="grid grid-cols-3 gap-3 p-3 bg-panel-dark rounded border border-border">
          <div>
            <div className="text-xs text-text-muted mb-1 flex items-center gap-1">
              <Target className="w-3 h-3" />
              Entry
            </div>
            <div className="text-sm font-mono text-text-primary">
              {tradeIdea.entry_price.toFixed(5)}
            </div>
          </div>
          <div>
            <div className="text-xs text-text-muted mb-1 flex items-center gap-1">
              <Shield className="w-3 h-3" />
              Stop Loss
            </div>
            <div className="text-sm font-mono text-red-400">
              {tradeIdea.stop_loss.toFixed(5)}
            </div>
          </div>
          <div>
            <div className="text-xs text-text-muted mb-1 flex items-center gap-1">
              <Activity className="w-3 h-3" />
              Take Profit
            </div>
            <div className="text-sm font-mono text-green-400">
              {tradeIdea.take_profit.toFixed(5)}
            </div>
          </div>
        </div>

        {/* Trade Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-text-muted">Volume:</span>
            <span className="font-mono text-text-primary">{tradeIdea.volume.toFixed(2)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-muted">RR Ratio:</span>
            <span className={`font-mono ${tradeIdea.rr_ratio >= 2 ? 'text-green-400' : 'text-yellow-500'}`}>
              {tradeIdea.rr_ratio.toFixed(2)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-muted">Risk %:</span>
            <span className="font-mono text-text-primary">
              {(tradeIdea.execution_plan.riskPct * 100).toFixed(2)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-muted">Status:</span>
            <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-500 border border-yellow-500/30">
              {tradeIdea.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        </div>

        {/* EMNR Flags */}
        <div className="border-t border-border pt-3">
          <div className="text-xs text-text-muted mb-2">EMNR Conditions</div>
          <div className="grid grid-cols-4 gap-2">
            <div className={`text-center p-2 rounded border ${tradeIdea.emnr_flags.entry ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-panel-dark border-border text-text-muted'}`}>
              <div className="text-xs font-medium">Entry</div>
              <div className="text-lg">{tradeIdea.emnr_flags.entry ? '✓' : '✗'}</div>
            </div>
            <div className={`text-center p-2 rounded border ${tradeIdea.emnr_flags.strong ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : 'bg-panel-dark border-border text-text-muted'}`}>
              <div className="text-xs font-medium">Strong</div>
              <div className="text-lg">{tradeIdea.emnr_flags.strong ? '✓' : '✗'}</div>
            </div>
            <div className={`text-center p-2 rounded border ${tradeIdea.emnr_flags.weak ? 'bg-orange-500/10 border-orange-500/30 text-orange-400' : 'bg-panel-dark border-border text-text-muted'}`}>
              <div className="text-xs font-medium">Weak</div>
              <div className="text-lg">{tradeIdea.emnr_flags.weak ? '✓' : '✗'}</div>
            </div>
            <div className={`text-center p-2 rounded border ${tradeIdea.emnr_flags.exit ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-panel-dark border-border text-text-muted'}`}>
              <div className="text-xs font-medium">Exit</div>
              <div className="text-lg">{tradeIdea.emnr_flags.exit ? '✓' : '✗'}</div>
            </div>
          </div>
        </div>

        {/* Indicators */}
        <div className="border-t border-border pt-3">
          <div className="text-xs text-text-muted mb-2">Technical Indicators</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span className="text-text-muted">EMA Fast:</span>
              <span className="font-mono text-text-primary">{tradeIdea.indicators.ema_fast.toFixed(5)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">EMA Slow:</span>
              <span className="font-mono text-text-primary">{tradeIdea.indicators.ema_slow.toFixed(5)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">RSI:</span>
              <span className="font-mono text-text-primary">{tradeIdea.indicators.rsi.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">MACD:</span>
              <span className="font-mono text-text-primary">{tradeIdea.indicators.macd.toFixed(5)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">ATR:</span>
              <span className="font-mono text-text-primary">{tradeIdea.indicators.atr.toFixed(5)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">ATR Median:</span>
              <span className="font-mono text-text-primary">{tradeIdea.indicators.atr_median.toFixed(5)}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        {tradeIdea.status === 'pending_approval' && (
          <div className="flex gap-3 pt-3 border-t border-border">
            <Button
              onClick={handleApprove}
              disabled={processing}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Approve & Execute
            </Button>
            <Button
              onClick={handleReject}
              disabled={processing}
              variant="destructive"
              className="flex-1 gap-2"
            >
              <XCircle className="w-4 h-4" />
              Reject
            </Button>
          </div>
        )}

        {tradeIdea.status === 'approved' && (
          <div className="flex items-center justify-center gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded text-green-400">
            <CheckCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Approved - Awaiting Execution</span>
          </div>
        )}

        {tradeIdea.status === 'executed' && (
          <div className="flex items-center justify-center gap-2 p-3 bg-blue-500/10 border border-blue-500/30 rounded text-blue-400">
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium">Executed</span>
          </div>
        )}

        {tradeIdea.status === 'rejected' && (
          <div className="flex items-center justify-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded text-red-400">
            <XCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Rejected</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradeIdeaCard;

