import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  Target,
  Shield,
  Activity,
} from 'lucide-react';
import type { TradeIdea } from '@/lib/ai-types';
import { getConfidenceColor } from '@/lib/ai-types';
import { toast } from '@/hooks/use-toast';

interface TradeIdeaApprovalDialogProps {
  tradeIdea: TradeIdea | null;
  open: boolean;
  accountBalance: number;
  onClose: () => void;
  onApprove: (ideaId: string) => Promise<void>;
  onReject: (ideaId: string, reason: string) => Promise<void>;
  onExecute: (ideaId: string, volume: number) => Promise<void>;
}

const TradeIdeaApprovalDialog: React.FC<TradeIdeaApprovalDialogProps> = ({
  tradeIdea,
  open,
  accountBalance,
  onClose,
  onApprove,
  onReject,
  onExecute,
}) => {
  const [volume, setVolume] = useState<string>('0.01');
  const [rejectReason, setRejectReason] = useState<string>('');
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState<'approve' | 'reject' | 'execute' | null>(null);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (open && tradeIdea) {
      setVolume(tradeIdea.volume?.toString() || '0.01');
      setRejectReason('');
      setShowRejectInput(false);
      setLoading(false);
      setAction(null);
    }
  }, [open, tradeIdea]);

  if (!tradeIdea) return null;

  const handleApprove = async () => {
    setLoading(true);
    setAction('approve');
    try {
      await onApprove(tradeIdea.id);
      toast({
        title: 'Trade Idea Approved',
        description: `${tradeIdea.symbol} trade idea has been approved and is ready for execution.`,
      });
      onClose();
    } catch (error: any) {
      toast({
        title: 'Approval Failed',
        description: error.message || 'Failed to approve trade idea',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setAction(null);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      toast({
        title: 'Reason Required',
        description: 'Please provide a reason for rejecting this trade idea.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    setAction('reject');
    try {
      await onReject(tradeIdea.id, rejectReason);
      toast({
        title: 'Trade Idea Rejected',
        description: `${tradeIdea.symbol} trade idea has been rejected.`,
      });
      onClose();
    } catch (error: any) {
      toast({
        title: 'Rejection Failed',
        description: error.message || 'Failed to reject trade idea',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setAction(null);
    }
  };

  const handleExecute = async () => {
    const volumeNum = parseFloat(volume);
    
    // Validation
    if (isNaN(volumeNum) || volumeNum <= 0) {
      toast({
        title: 'Invalid Volume',
        description: 'Please enter a valid volume greater than 0.',
        variant: 'destructive',
      });
      return;
    }

    if (volumeNum < 0.01) {
      toast({
        title: 'Volume Too Small',
        description: 'Minimum volume is 0.01 lots.',
        variant: 'destructive',
      });
      return;
    }

    if (tradeIdea.status !== 'approved') {
      toast({
        title: 'Not Approved',
        description: 'Trade idea must be approved before execution.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    setAction('execute');
    try {
      await onExecute(tradeIdea.id, volumeNum);
      toast({
        title: 'Trade Executed',
        description: `${tradeIdea.symbol} ${tradeIdea.direction} position opened with ${volumeNum} lots.`,
      });
      onClose();
    } catch (error: any) {
      toast({
        title: 'Execution Failed',
        description: error.message || 'Failed to execute trade',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setAction(null);
    }
  };

  // Calculate risk in dollars
  const calculateRisk = () => {
    const volumeNum = parseFloat(volume) || 0;
    const pipValue = tradeIdea.symbol.includes('JPY') ? 0.01 : 0.0001;
    const pips = Math.abs(tradeIdea.entry_price - tradeIdea.stop_loss) / pipValue;
    const riskDollars = pips * volumeNum * 10; // Approximate for standard lot
    return riskDollars;
  };

  const riskDollars = calculateRisk();
  const riskPercent = accountBalance > 0 ? (riskDollars / accountBalance) * 100 : 0;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            {tradeIdea.direction === 'long' ? (
              <TrendingUp className="w-6 h-6 text-green-500" />
            ) : (
              <TrendingDown className="w-6 h-6 text-red-500" />
            )}
            {tradeIdea.symbol} - {tradeIdea.direction.toUpperCase()} Trade Idea
          </DialogTitle>
          <DialogDescription>
            Review and approve this AI-generated trade idea before execution
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Status Badge */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-text-muted">Status:</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              tradeIdea.status === 'pending_approval' ? 'bg-yellow-500/20 text-yellow-500' :
              tradeIdea.status === 'approved' ? 'bg-green-500/20 text-green-500' :
              tradeIdea.status === 'rejected' ? 'bg-red-500/20 text-red-500' :
              tradeIdea.status === 'executed' ? 'bg-blue-500/20 text-blue-500' :
              'bg-gray-500/20 text-gray-500'
            }`}>
              {tradeIdea.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          {/* Confidence Score */}
          <div className="trading-panel">
            <div className="trading-header">
              <h3 className="font-medium flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Confidence Score
              </h3>
            </div>
            <div className="trading-content">
              <div className="flex items-center justify-between">
                <span className={`text-3xl font-bold ${getConfidenceColor(tradeIdea.confidence)}`}>
                  {tradeIdea.confidence}%
                </span>
                <div className="text-right text-sm text-text-muted">
                  <div>Action: {tradeIdea.action.replace('_', ' ')}</div>
                  <div>Timeframe: {tradeIdea.timeframe}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Trade Details */}
          <div className="trading-panel">
            <div className="trading-header">
              <h3 className="font-medium flex items-center gap-2">
                <Target className="w-4 h-4" />
                Trade Details
              </h3>
            </div>
            <div className="trading-content">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-text-muted mb-1">Entry Price</div>
                  <div className="text-lg font-mono font-semibold">{tradeIdea.entry_price.toFixed(5)}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted mb-1">Direction</div>
                  <div className={`text-lg font-semibold ${tradeIdea.direction === 'long' ? 'text-green-500' : 'text-red-500'}`}>
                    {tradeIdea.direction.toUpperCase()}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-text-muted mb-1">Stop Loss</div>
                  <div className="text-lg font-mono font-semibold text-red-500">{tradeIdea.stop_loss.toFixed(5)}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted mb-1">Take Profit</div>
                  <div className="text-lg font-mono font-semibold text-green-500">{tradeIdea.take_profit.toFixed(5)}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted mb-1">RR Ratio</div>
                  <div className="text-lg font-semibold">{tradeIdea.rr_ratio.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted mb-1">Suggested Volume</div>
                  <div className="text-lg font-semibold">{tradeIdea.volume?.toFixed(2) || '0.01'} lots</div>
                </div>
              </div>
            </div>
          </div>

          {/* EMNR Flags */}
          <div className="trading-panel">
            <div className="trading-header">
              <h3 className="font-medium flex items-center gap-2">
                <Shield className="w-4 h-4" />
                EMNR Flags
              </h3>
            </div>
            <div className="trading-content">
              <div className="grid grid-cols-2 gap-2">
                <div className={`flex items-center gap-2 px-3 py-2 rounded ${tradeIdea.emnr_flags.entry ? 'bg-green-500/20 text-green-500' : 'bg-gray-500/20 text-gray-500'}`}>
                  {tradeIdea.emnr_flags.entry ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                  <span className="text-sm font-medium">Entry</span>
                </div>
                <div className={`flex items-center gap-2 px-3 py-2 rounded ${tradeIdea.emnr_flags.strong ? 'bg-green-500/20 text-green-500' : 'bg-gray-500/20 text-gray-500'}`}>
                  {tradeIdea.emnr_flags.strong ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                  <span className="text-sm font-medium">Strong</span>
                </div>
                <div className={`flex items-center gap-2 px-3 py-2 rounded ${!tradeIdea.emnr_flags.exit ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'}`}>
                  {!tradeIdea.emnr_flags.exit ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                  <span className="text-sm font-medium">No Exit</span>
                </div>
                <div className={`flex items-center gap-2 px-3 py-2 rounded ${!tradeIdea.emnr_flags.weak ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'}`}>
                  {!tradeIdea.emnr_flags.weak ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                  <span className="text-sm font-medium">No Weak</span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Calculation */}
          <div className="trading-panel">
            <div className="trading-header">
              <h3 className="font-medium flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Risk Calculation
              </h3>
            </div>
            <div className="trading-content">
              <div className="space-y-3">
                <div>
                  <Label htmlFor="volume">Volume (lots)</Label>
                  <Input
                    id="volume"
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={volume}
                    onChange={(e) => setVolume(e.target.value)}
                    className="mt-1"
                    disabled={tradeIdea.status === 'executed' || loading}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-border">
                  <div>
                    <div className="text-xs text-text-muted mb-1">Risk Amount</div>
                    <div className="text-lg font-semibold text-red-500">${riskDollars.toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-text-muted mb-1">Risk Percentage</div>
                    <div className={`text-lg font-semibold ${riskPercent > 2 ? 'text-red-500' : 'text-green-500'}`}>
                      {riskPercent.toFixed(2)}%
                    </div>
                  </div>
                </div>
                {riskPercent > 2 && (
                  <div className="flex items-center gap-2 p-2 bg-yellow-500/20 text-yellow-500 rounded text-sm">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Risk exceeds 2% of account balance</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Reject Reason Input */}
          {showRejectInput && (
            <div className="space-y-2">
              <Label htmlFor="reject-reason">Rejection Reason</Label>
              <Textarea
                id="reject-reason"
                placeholder="Enter reason for rejecting this trade idea..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>
          )}
        </div>

        <DialogFooter className="flex gap-2">
          {!showRejectInput ? (
            <>
              <Button
                variant="outline"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </Button>
              
              {tradeIdea.status === 'pending_approval' && (
                <>
                  <Button
                    variant="destructive"
                    onClick={() => setShowRejectInput(true)}
                    disabled={loading}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Reject
                  </Button>
                  <Button
                    onClick={handleApprove}
                    disabled={loading}
                  >
                    {loading && action === 'approve' ? 'Approving...' : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Approve
                      </>
                    )}
                  </Button>
                </>
              )}

              {tradeIdea.status === 'approved' && (
                <Button
                  onClick={handleExecute}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {loading && action === 'execute' ? 'Executing...' : (
                    <>
                      <TrendingUp className="w-4 h-4 mr-2" />
                      Execute Trade
                    </>
                  )}
                </Button>
              )}
            </>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={() => {
                  setShowRejectInput(false);
                  setRejectReason('');
                }}
                disabled={loading}
              >
                Back
              </Button>
              <Button
                variant="destructive"
                onClick={handleReject}
                disabled={loading || !rejectReason.trim()}
              >
                {loading && action === 'reject' ? 'Rejecting...' : 'Confirm Rejection'}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default TradeIdeaApprovalDialog;

