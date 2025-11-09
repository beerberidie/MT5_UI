import React, { useState } from 'react';
import { X, CheckCircle, XCircle, TrendingUp, TrendingDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';

interface TradeIdea {
  id: string;
  timestamp: string;
  symbol: string;
  timeframe: string;
  confidence: number;
  action: string;
  direction?: string;
  entry_price?: number;
  stop_loss?: number;
  take_profit?: number;
  volume?: number;
  rr_ratio?: number;
  status: string;
  source?: string;
  notes?: string;
  emnr_flags?: {
    entry?: boolean;
    exit?: boolean;
    strong?: boolean;
    weak?: boolean;
  };
  indicators?: Record<string, any>;
  execution_plan?: Record<string, any>;
  approval_status?: string;
  approved_by?: string;
  approved_at?: string;
  rejected_by?: string;
  rejected_at?: string;
  rejection_reason?: string;
  manual_overrides?: Record<string, any>;
}

interface TradeIdeaDetailModalProps {
  tradeIdea: TradeIdea;
  onClose: () => void;
  onSave: (tradeIdea: TradeIdea, overrides?: Record<string, any>) => void;
  onApprove: (tradeIdea: TradeIdea) => void;
  onReject: (tradeIdea: TradeIdea, reason: string) => void;
}

const TradeIdeaDetailModal: React.FC<TradeIdeaDetailModalProps> = ({
  tradeIdea,
  onClose,
  onSave,
  onApprove,
  onReject
}) => {
  // Editable fields
  const [entryPrice, setEntryPrice] = useState(tradeIdea.entry_price?.toString() || '');
  const [stopLoss, setStopLoss] = useState(tradeIdea.stop_loss?.toString() || '');
  const [takeProfit, setTakeProfit] = useState(tradeIdea.take_profit?.toString() || '');
  const [volume, setVolume] = useState(tradeIdea.volume?.toString() || '');
  const [notes, setNotes] = useState(tradeIdea.notes || '');
  const [rejectionReason, setRejectionReason] = useState('');
  
  // Track if any changes were made
  const hasChanges = () => {
    return (
      entryPrice !== (tradeIdea.entry_price?.toString() || '') ||
      stopLoss !== (tradeIdea.stop_loss?.toString() || '') ||
      takeProfit !== (tradeIdea.take_profit?.toString() || '') ||
      volume !== (tradeIdea.volume?.toString() || '') ||
      notes !== (tradeIdea.notes || '')
    );
  };

  // Calculate R:R ratio
  const calculateRR = () => {
    const entry = parseFloat(entryPrice);
    const sl = parseFloat(stopLoss);
    const tp = parseFloat(takeProfit);
    
    if (entry && sl && tp) {
      const risk = Math.abs(entry - sl);
      const reward = Math.abs(tp - entry);
      if (risk > 0) {
        return (reward / risk).toFixed(2);
      }
    }
    return tradeIdea.rr_ratio?.toFixed(2) || 'N/A';
  };

  // Handle approve with overrides
  const handleApproveWithOverrides = () => {
    if (hasChanges()) {
      const overrides: Record<string, any> = {};
      
      if (entryPrice !== (tradeIdea.entry_price?.toString() || '')) {
        overrides.entry_price = parseFloat(entryPrice);
      }
      if (stopLoss !== (tradeIdea.stop_loss?.toString() || '')) {
        overrides.stop_loss = parseFloat(stopLoss);
      }
      if (takeProfit !== (tradeIdea.take_profit?.toString() || '')) {
        overrides.take_profit = parseFloat(takeProfit);
      }
      if (volume !== (tradeIdea.volume?.toString() || '')) {
        overrides.volume = parseFloat(volume);
      }
      if (notes !== (tradeIdea.notes || '')) {
        overrides.notes = notes;
      }
      
      onSave(tradeIdea, overrides);
    } else {
      onApprove(tradeIdea);
    }
  };

  // Handle reject
  const handleReject = () => {
    if (!rejectionReason.trim()) {
      alert('Please provide a rejection reason');
      return;
    }
    onReject(tradeIdea, rejectionReason);
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  const isPending = !tradeIdea.approval_status || tradeIdea.approval_status === 'pending';

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#111111] border border-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-[#111111] border-b border-gray-800 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {tradeIdea.direction && (
              tradeIdea.direction.toLowerCase() === 'long' || tradeIdea.direction.toLowerCase() === 'buy'
                ? <TrendingUp className="w-6 h-6 text-green-500" />
                : <TrendingDown className="w-6 h-6 text-red-500" />
            )}
            <h2 className="text-2xl font-bold font-mono">{tradeIdea.symbol}</h2>
            <Badge variant="outline" className="border-gray-700">
              {tradeIdea.timeframe}
            </Badge>
            <Badge className={`${
              tradeIdea.confidence >= 80 ? 'bg-green-500/20 text-green-400 border-green-500/30' :
              tradeIdea.confidence >= 60 ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
              'bg-red-500/20 text-red-400 border-red-500/30'
            } border`}>
              {tradeIdea.confidence}% Confidence
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Trade ID:</span>
              <span className="ml-2 font-mono text-xs">{tradeIdea.id}</span>
            </div>
            <div>
              <span className="text-gray-400">Timestamp:</span>
              <span className="ml-2">{formatTimestamp(tradeIdea.timestamp)}</span>
            </div>
            <div>
              <span className="text-gray-400">Action:</span>
              <span className="ml-2 font-bold">{tradeIdea.action}</span>
            </div>
            <div>
              <span className="text-gray-400">Direction:</span>
              <span className="ml-2 font-bold capitalize">{tradeIdea.direction || 'N/A'}</span>
            </div>
          </div>

          {/* Editable Parameters */}
          <div className="border border-gray-800 rounded-lg p-4 space-y-4">
            <h3 className="text-lg font-bold mb-4">Trade Parameters</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="entry_price" className="text-gray-400">Entry Price</Label>
                <Input
                  id="entry_price"
                  type="number"
                  step="0.00001"
                  value={entryPrice}
                  onChange={(e) => setEntryPrice(e.target.value)}
                  disabled={!isPending}
                  className="bg-[#0a0a0a] border-gray-700 mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="volume" className="text-gray-400">Volume (Lots)</Label>
                <Input
                  id="volume"
                  type="number"
                  step="0.01"
                  value={volume}
                  onChange={(e) => setVolume(e.target.value)}
                  disabled={!isPending}
                  className="bg-[#0a0a0a] border-gray-700 mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="stop_loss" className="text-gray-400">Stop Loss</Label>
                <Input
                  id="stop_loss"
                  type="number"
                  step="0.00001"
                  value={stopLoss}
                  onChange={(e) => setStopLoss(e.target.value)}
                  disabled={!isPending}
                  className="bg-[#0a0a0a] border-gray-700 mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="take_profit" className="text-gray-400">Take Profit</Label>
                <Input
                  id="take_profit"
                  type="number"
                  step="0.00001"
                  value={takeProfit}
                  onChange={(e) => setTakeProfit(e.target.value)}
                  disabled={!isPending}
                  className="bg-[#0a0a0a] border-gray-700 mt-1"
                />
              </div>
            </div>
            
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-400">Calculated R:R Ratio:</span>
              <span className="text-xl font-bold text-blue-400">{calculateRR()}</span>
            </div>
          </div>

          {/* Notes */}
          <div>
            <Label htmlFor="notes" className="text-gray-400">Notes</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={!isPending}
              className="bg-[#0a0a0a] border-gray-700 mt-1 min-h-[80px]"
              placeholder="Add notes about this trade idea..."
            />
          </div>

          {/* EMNR Flags */}
          {tradeIdea.emnr_flags && (
            <div>
              <h3 className="text-sm font-bold text-gray-400 mb-2">EMNR Flags</h3>
              <div className="flex gap-2">
                {tradeIdea.emnr_flags.entry && (
                  <Badge variant="outline" className="border-green-500/30 text-green-400">
                    Entry
                  </Badge>
                )}
                {tradeIdea.emnr_flags.exit && (
                  <Badge variant="outline" className="border-red-500/30 text-red-400">
                    Exit
                  </Badge>
                )}
                {tradeIdea.emnr_flags.strong && (
                  <Badge variant="outline" className="border-blue-500/30 text-blue-400">
                    Strong
                  </Badge>
                )}
                {tradeIdea.emnr_flags.weak && (
                  <Badge variant="outline" className="border-yellow-500/30 text-yellow-400">
                    Weak
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* Indicators */}
          {tradeIdea.indicators && Object.keys(tradeIdea.indicators).length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-gray-400 mb-2">Technical Indicators</h3>
              <div className="grid grid-cols-3 gap-2 text-sm">
                {Object.entries(tradeIdea.indicators).map(([key, value]) => (
                  <div key={key} className="bg-[#0a0a0a] border border-gray-800 rounded p-2">
                    <span className="text-gray-400 text-xs uppercase">{key.replace('_', ' ')}:</span>
                    <span className="ml-2 font-mono">{typeof value === 'number' ? value.toFixed(5) : value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rejection Reason (for pending items) */}
          {isPending && (
            <div>
              <Label htmlFor="rejection_reason" className="text-gray-400">Rejection Reason (if rejecting)</Label>
              <Textarea
                id="rejection_reason"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="bg-[#0a0a0a] border-gray-700 mt-1 min-h-[60px]"
                placeholder="Provide a reason for rejection..."
              />
            </div>
          )}

          {/* Approval/Rejection Info */}
          {tradeIdea.approved_at && (
            <div className="bg-green-500/10 border border-green-500/30 rounded p-3 text-sm">
              <strong className="text-green-400">Approved</strong> by {tradeIdea.approved_by} on {formatTimestamp(tradeIdea.approved_at)}
            </div>
          )}
          
          {tradeIdea.rejected_at && (
            <div className="bg-red-500/10 border border-red-500/30 rounded p-3 text-sm">
              <strong className="text-red-400">Rejected</strong> by {tradeIdea.rejected_by} on {formatTimestamp(tradeIdea.rejected_at)}
              {tradeIdea.rejection_reason && (
                <div className="mt-2 text-gray-400">
                  <strong>Reason:</strong> {tradeIdea.rejection_reason}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {isPending && (
          <div className="sticky bottom-0 bg-[#111111] border-t border-gray-800 p-4 flex items-center justify-end gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="border-gray-700 hover:bg-gray-800"
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={handleReject}
              className="border-red-500/30 text-red-400 hover:bg-red-500/10"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Reject
            </Button>
            <Button
              variant="outline"
              onClick={handleApproveWithOverrides}
              className="border-green-500/30 text-green-400 hover:bg-green-500/10"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              {hasChanges() ? 'Approve with Overrides' : 'Approve'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradeIdeaDetailModal;

