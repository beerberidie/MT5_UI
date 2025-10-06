import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Brain,
  TrendingUp,
  Settings as SettingsIcon,
  History,
  Play,
  AlertCircle
} from 'lucide-react';
import AIControlPanel from '@/components/ai/AIControlPanel';
import TradeIdeaCard from '@/components/ai/TradeIdeaCard';
import TradeIdeaApprovalDialog from '@/components/ai/TradeIdeaApprovalDialog';
import StrategyEditor from '@/components/ai/StrategyEditor';
import {
  getSymbols,
  evaluateSymbol,
  enableAI,
  disableAI,
  getAIDecisions,
  approveTradeIdea,
  rejectTradeIdea,
  executeTradeIdea,
  getAccount
} from '@/lib/api';
import { toast } from '@/hooks/use-toast';
import type { TradeIdea, AIDecision } from '@/lib/ai-types';

const AI: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'strategies' | 'history'>('overview');
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [tradeIdeas, setTradeIdeas] = useState<TradeIdea[]>([]);
  const [decisions, setDecisions] = useState<AIDecision[]>([]);
  const [evaluating, setEvaluating] = useState(false);
  const [enablingSymbol, setEnablingSymbol] = useState<string | null>(null);

  // Dialog state
  const [selectedTradeIdea, setSelectedTradeIdea] = useState<TradeIdea | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [accountBalance, setAccountBalance] = useState<number>(10000);

  useEffect(() => {
    loadSymbols();
    loadDecisions();
    loadAccountBalance();
  }, []);

  async function loadAccountBalance() {
    try {
      const account = await getAccount();
      setAccountBalance(account.balance || 10000);
    } catch (error) {
      console.error('Failed to load account balance:', error);
    }
  }

  async function loadSymbols() {
    try {
      const data = await getSymbols(false);
      // Defensive check: ensure data is an array before calling .map()
      if (!Array.isArray(data)) {
        console.error('getSymbols returned non-array data:', data);
        setSymbols([]);
        return;
      }
      const symbolNames = data.map(s => s.symbol).filter(Boolean);
      setSymbols(symbolNames);
      if (symbolNames.length > 0 && !selectedSymbol) {
        setSelectedSymbol(symbolNames[0]);
      }
    } catch (error) {
      console.error('Failed to load symbols:', error);
      setSymbols([]); // Ensure symbols is always an array
      toast({
        title: 'Failed to Load Symbols',
        description: 'Could not load symbol list. Please refresh the page.',
        variant: 'destructive',
      });
    }
  }

  async function loadDecisions() {
    try {
      const data = await getAIDecisions(50);
      // Defensive check: ensure data is an array
      if (!Array.isArray(data)) {
        console.error('getAIDecisions returned non-array data:', data);
        setDecisions([]);
        return;
      }
      setDecisions(data);
    } catch (error) {
      console.error('Failed to load decisions:', error);
      setDecisions([]); // Ensure decisions is always an array
    }
  }

  async function handleEvaluate() {
    if (!selectedSymbol) {
      toast({
        title: 'No Symbol Selected',
        description: 'Please select a symbol to evaluate',
        variant: 'destructive',
      });
      return;
    }

    setEvaluating(true);
    try {
      const result = await evaluateSymbol(selectedSymbol, 'H1', false);

      if (result.trade_idea) {
        setTradeIdeas(prev => [result.trade_idea, ...prev]);
        toast({
          title: 'Evaluation Complete',
          description: `Trade idea generated for ${selectedSymbol} with ${result.confidence}% confidence`,
        });
      } else {
        toast({
          title: 'No Trade Idea',
          description: result.message || 'Conditions not met for trade idea',
        });
      }

      loadDecisions(); // Refresh decision history
    } catch (error: any) {
      toast({
        title: 'Evaluation Failed',
        description: error.message || 'Failed to evaluate symbol',
        variant: 'destructive',
      });
    } finally {
      setEvaluating(false);
    }
  }

  async function handleEnableAI(symbol: string) {
    setEnablingSymbol(symbol);
    try {
      await enableAI(symbol, 'H1', false);
      toast({
        title: 'AI Enabled',
        description: `AI monitoring enabled for ${symbol}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to enable AI for ${symbol}`,
        variant: 'destructive',
      });
    } finally {
      setEnablingSymbol(null);
    }
  }

  async function handleDisableAI(symbol: string) {
    try {
      await disableAI(symbol);
      toast({
        title: 'AI Disabled',
        description: `AI monitoring disabled for ${symbol}`,
        variant: 'destructive',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to disable AI for ${symbol}`,
        variant: 'destructive',
      });
    }
  }

  function handleReviewTradeIdea(tradeIdea: TradeIdea) {
    setSelectedTradeIdea(tradeIdea);
    setDialogOpen(true);
  }

  async function handleApproveTradeIdea(id: string) {
    try {
      await approveTradeIdea(id);
      // Update local state
      setTradeIdeas(prev => prev.map(idea =>
        idea.id === id ? { ...idea, status: 'approved' as const } : idea
      ));
      // Refresh account balance
      loadAccountBalance();
    } catch (error: any) {
      throw new Error(error.message || 'Failed to approve trade idea');
    }
  }

  async function handleRejectTradeIdea(id: string, reason: string) {
    try {
      await rejectTradeIdea(id, reason);
      // Update local state
      setTradeIdeas(prev => prev.map(idea =>
        idea.id === id ? { ...idea, status: 'rejected' as const } : idea
      ));
    } catch (error: any) {
      throw new Error(error.message || 'Failed to reject trade idea');
    }
  }

  async function handleExecuteTradeIdea(id: string, volume: number) {
    try {
      await executeTradeIdea(id, accountBalance, volume);
      // Update local state
      setTradeIdeas(prev => prev.map(idea =>
        idea.id === id ? { ...idea, status: 'executed' as const } : idea
      ));
      // Refresh account balance
      loadAccountBalance();
    } catch (error: any) {
      throw new Error(error.message || 'Failed to execute trade idea');
    }
  }

  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Header */}
      <div className="h-header bg-panel border-b border-border flex items-center px-4">
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-primary" />
          <h1 className="text-lg font-semibold">AI Trading</h1>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">
        {/* Tabs */}
        <div className="flex gap-2 mb-4 border-b border-border">
          <button
            type="button"
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'overview'
                ? 'border-primary text-primary'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Overview
            </div>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('strategies')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'strategies'
                ? 'border-primary text-primary'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            <div className="flex items-center gap-2">
              <SettingsIcon className="w-4 h-4" />
              Strategies
            </div>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'history'
                ? 'border-primary text-primary'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            <div className="flex items-center gap-2">
              <History className="w-4 h-4" />
              Decision History
            </div>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Left Column - Control Panel */}
            <div className="lg:col-span-1">
              <AIControlPanel />

              {/* Manual Evaluation */}
              <div className="trading-panel mt-4">
                <div className="trading-header">
                  <h3 className="font-medium">Manual Evaluation</h3>
                </div>
                <div className="trading-content space-y-3">
                  <div>
                    <label htmlFor="symbol-select" className="text-xs text-text-muted mb-1 block">Select Symbol</label>
                    <select
                      id="symbol-select"
                      value={selectedSymbol}
                      onChange={(e) => setSelectedSymbol(e.target.value)}
                      className="w-full px-3 py-2 bg-panel-dark border border-border rounded text-sm text-text-primary"
                      aria-label="Select symbol for AI evaluation"
                    >
                      {symbols.map(sym => (
                        <option key={sym} value={sym}>{sym}</option>
                      ))}
                    </select>
                  </div>
                  <Button
                    onClick={handleEvaluate}
                    disabled={evaluating || !selectedSymbol}
                    className="w-full gap-2"
                  >
                    <Play className="w-4 h-4" />
                    {evaluating ? 'Evaluating...' : 'Evaluate Now'}
                  </Button>
                  <div className="text-xs text-text-muted">
                    Manually trigger AI evaluation for the selected symbol
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column - Trade Ideas */}
            <div className="lg:col-span-2">
              <div className="trading-panel">
                <div className="trading-header">
                  <h3 className="font-medium">Active Trade Ideas</h3>
                </div>
                <div className="trading-content">
                  {tradeIdeas.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <AlertCircle className="w-16 h-16 text-text-muted opacity-30 mb-4" />
                      <p className="text-sm text-text-muted">No active trade ideas</p>
                      <p className="text-xs text-text-muted mt-2">
                        Enable AI for symbols or trigger manual evaluation to generate trade ideas
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {tradeIdeas.map(idea => (
                        <TradeIdeaCard
                          key={idea.id}
                          tradeIdea={idea}
                          onReview={handleReviewTradeIdea}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'strategies' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Symbol Selection */}
            <div className="lg:col-span-1">
              <div className="trading-panel">
                <div className="trading-header">
                  <h3 className="font-medium">Symbol Selection</h3>
                </div>
                <div className="trading-content space-y-2">
                  {symbols.map(sym => (
                    <button
                      key={sym}
                      type="button"
                      onClick={() => setSelectedSymbol(sym)}
                      className={`w-full px-3 py-2 rounded text-left text-sm transition-colors ${
                        selectedSymbol === sym
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-panel-dark hover:bg-panel-dark/70 text-text-primary'
                      }`}
                      aria-label={`Select ${sym} for strategy editing`}
                    >
                      {sym}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Strategy Editor */}
            <div className="lg:col-span-2">
              {selectedSymbol ? (
                <StrategyEditor symbol={selectedSymbol} />
              ) : (
                <div className="trading-panel">
                  <div className="trading-content">
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <SettingsIcon className="w-16 h-16 text-text-muted opacity-30 mb-4" />
                      <p className="text-sm text-text-muted">Select a symbol to edit its strategy</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="trading-panel">
            <div className="trading-header">
              <h3 className="font-medium">AI Decision History</h3>
            </div>
            <div className="trading-content">
              {decisions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <History className="w-16 h-16 text-text-muted opacity-30 mb-4" />
                  <p className="text-sm text-text-muted">No decision history</p>
                  <p className="text-xs text-text-muted mt-2">
                    AI decisions will appear here once evaluations are performed
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="trading-table w-full text-xs">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Symbol</th>
                        <th>TF</th>
                        <th>Confidence</th>
                        <th>Action</th>
                        <th>Direction</th>
                        <th>Entry</th>
                        <th>SL</th>
                        <th>TP</th>
                        <th>RR</th>
                        <th>EMNR</th>
                      </tr>
                    </thead>
                    <tbody>
                      {decisions.map((decision, idx) => (
                        <tr key={idx}>
                          <td className="text-xs">{new Date(decision.timestamp).toLocaleString()}</td>
                          <td className="font-medium">{decision.symbol}</td>
                          <td>{decision.timeframe}</td>
                          <td className="text-right">
                            <span className={decision.confidence >= 75 ? 'text-green-400' : decision.confidence >= 60 ? 'text-yellow-500' : 'text-text-muted'}>
                              {decision.confidence}
                            </span>
                          </td>
                          <td className="text-xs">{decision.action}</td>
                          <td className={decision.direction === 'long' ? 'text-green-400' : 'text-red-400'}>
                            {decision.direction.toUpperCase()}
                          </td>
                          <td className="text-right font-mono">{decision.entry_price.toFixed(5)}</td>
                          <td className="text-right font-mono text-red-400">{decision.stop_loss.toFixed(5)}</td>
                          <td className="text-right font-mono text-green-400">{decision.take_profit.toFixed(5)}</td>
                          <td className="text-right">{decision.rr_ratio.toFixed(2)}</td>
                          <td className="text-xs">
                            <span className={decision.emnr_entry ? 'text-green-400' : 'text-text-muted'}>E</span>
                            <span className={decision.emnr_strong ? 'text-blue-400' : 'text-text-muted'}>S</span>
                            <span className={decision.emnr_weak ? 'text-orange-400' : 'text-text-muted'}>W</span>
                            <span className={decision.emnr_exit ? 'text-red-400' : 'text-text-muted'}>X</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Trade Idea Approval Dialog */}
      <TradeIdeaApprovalDialog
        tradeIdea={selectedTradeIdea}
        open={dialogOpen}
        accountBalance={accountBalance}
        onClose={() => {
          setDialogOpen(false);
          setSelectedTradeIdea(null);
        }}
        onApprove={handleApproveTradeIdea}
        onReject={handleRejectTradeIdea}
        onExecute={handleExecuteTradeIdea}
      />
    </div>
  );
};

export default AI;
