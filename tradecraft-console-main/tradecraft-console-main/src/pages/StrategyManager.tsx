import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChevronLeft,
  RefreshCw,
  Plus,
  Edit,
  Trash2,
  Copy,
  Power,
  PowerOff,
  CheckCircle,
  XCircle,
  AlertCircle,
  Settings
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from '@/hooks/use-toast';
import { apiCall } from '@/lib/api';

interface Strategy {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  symbol: string;
  timeframe: string;
  sessions: string[];
  indicators: {
    ema?: { fast: number; slow: number };
    rsi?: { period: number; overbought: number; oversold: number };
    macd?: { fast: number; slow: number; signal: number };
    atr?: { period: number; multiplier: number };
  };
  conditions: {
    entry: string[];
    exit?: string[];
    strong?: string[];
    weak?: string[];
  };
  strategy: {
    direction: 'long' | 'short' | 'both';
    min_rr: number;
    news_embargo_minutes: number;
    invalidations?: string[];
    max_risk_pct?: number;
  };
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface StrategyListResponse {
  items: Strategy[];
  total: number;
  enabled_count: number;
  disabled_count: number;
}

const StrategyManager: React.FC = () => {
  const navigate = useNavigate();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [stats, setStats] = useState({ total: 0, enabled: 0, disabled: 0 });
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    loadStrategies(true);
  }, []);

  const loadStrategies = async (showLoader: boolean = false) => {
    if (showLoader) setLoading(true);
    else setRefreshing(true);

    try {
      const response = await apiCall<StrategyListResponse>('/api/strategies');
      setStrategies(response.items);
      setStats({
        total: response.total,
        enabled: response.enabled_count,
        disabled: response.disabled_count
      });
    } catch (error) {
      console.error('Error loading strategies:', error);
      toast({
        title: 'Error',
        description: 'Failed to load strategies',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleToggleStrategy = async (strategy: Strategy) => {
    try {
      await apiCall(`/api/strategies/${strategy.id}/toggle`, {
        method: 'PATCH',
        body: JSON.stringify({ enabled: !strategy.enabled })
      });

      const status = !strategy.enabled ? 'enabled' : 'disabled';
      toast({
        title: 'Success',
        description: `Strategy ${strategy.name} ${status}`
      });

      loadStrategies(false);
    } catch (error) {
      console.error('Error toggling strategy:', error);
      toast({
        title: 'Error',
        description: 'Failed to toggle strategy',
        variant: 'destructive'
      });
    }
  };

  const handleDeleteStrategy = async (strategy: Strategy) => {
    if (!confirm(`Are you sure you want to delete strategy "${strategy.name}"?`)) {
      return;
    }

    try {
      await apiCall(`/api/strategies/${strategy.id}`, {
        method: 'DELETE'
      });

      toast({
        title: 'Success',
        description: `Strategy ${strategy.name} deleted`
      });

      loadStrategies(false);
    } catch (error) {
      console.error('Error deleting strategy:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete strategy',
        variant: 'destructive'
      });
    }
  };

  const handleDuplicateStrategy = async (strategy: Strategy) => {
    const newName = prompt(`Enter name for duplicated strategy:`, `${strategy.name} (Copy)`);
    if (!newName) return;

    try {
      await apiCall(`/api/strategies/${strategy.id}/duplicate`, {
        method: 'POST',
        body: JSON.stringify({ new_name: newName })
      });

      toast({
        title: 'Success',
        description: `Strategy duplicated as ${newName}`
      });

      loadStrategies(false);
    } catch (error) {
      console.error('Error duplicating strategy:', error);
      toast({
        title: 'Error',
        description: 'Failed to duplicate strategy',
        variant: 'destructive'
      });
    }
  };

  const getFilteredStrategies = () => {
    switch (activeTab) {
      case 'enabled':
        return strategies.filter(s => s.enabled);
      case 'disabled':
        return strategies.filter(s => !s.enabled);
      default:
        return strategies;
    }
  };

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'long': return 'text-green-500';
      case 'short': return 'text-red-500';
      case 'both': return 'text-blue-500';
      default: return 'text-gray-400';
    }
  };

  const getDirectionBadge = (direction: string) => {
    switch (direction) {
      case 'long': return <Badge className="bg-green-500/20 text-green-500 border-green-500/30">Long</Badge>;
      case 'short': return <Badge className="bg-red-500/20 text-red-500 border-red-500/30">Short</Badge>;
      case 'both': return <Badge className="bg-blue-500/20 text-blue-500 border-blue-500/30">Both</Badge>;
      default: return <Badge variant="outline">{direction}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white p-6 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Loading strategies...</span>
        </div>
      </div>
    );
  }

  const filteredStrategies = getFilteredStrategies();

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-gray-800 rounded-md transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Settings className="w-6 h-6" />
              Strategy Manager
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Manage trading strategies and EMNR rules
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => loadStrategies(false)}
            variant="outline"
            size="sm"
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={() => setShowCreateModal(true)}
            size="sm"
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Strategy
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card className="bg-[#111111] border-gray-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-400">Total Strategies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">{stats.total}</div>
          </CardContent>
        </Card>

        <Card className="bg-[#111111] border-gray-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-400">Enabled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-500">{stats.enabled}</div>
          </CardContent>
        </Card>

        <Card className="bg-[#111111] border-gray-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-400">Disabled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-500">{stats.disabled}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="mb-6">
        <TabsList className="bg-[#111111] border border-gray-800">
          <TabsTrigger value="all" className="data-[state=active]:bg-gray-800">
            All ({stats.total})
          </TabsTrigger>
          <TabsTrigger value="enabled" className="data-[state=active]:bg-gray-800">
            Enabled ({stats.enabled})
          </TabsTrigger>
          <TabsTrigger value="disabled" className="data-[state=active]:bg-gray-800">
            Disabled ({stats.disabled})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          {filteredStrategies.length === 0 ? (
            <Card className="bg-[#111111] border-gray-800">
              <CardContent className="py-12 text-center">
                <AlertCircle className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">No strategies found</p>
                <Button
                  onClick={() => setShowCreateModal(true)}
                  variant="outline"
                  size="sm"
                  className="mt-4"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Strategy
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredStrategies.map((strategy) => (
                <StrategyCard
                  key={strategy.id}
                  strategy={strategy}
                  onToggle={handleToggleStrategy}
                  onEdit={() => {
                    setSelectedStrategy(strategy);
                    setShowEditModal(true);
                  }}
                  onDelete={handleDeleteStrategy}
                  onDuplicate={handleDuplicateStrategy}
                  getDirectionBadge={getDirectionBadge}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* TODO: Create/Edit Modals */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#111111] border border-gray-800 rounded-lg p-6 max-w-2xl w-full">
            <h2 className="text-xl font-bold mb-4">Create New Strategy</h2>
            <p className="text-gray-400 mb-4">Strategy creation form coming soon...</p>
            <Button onClick={() => setShowCreateModal(false)} variant="outline">
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

// Strategy Card Component
interface StrategyCardProps {
  strategy: Strategy;
  onToggle: (strategy: Strategy) => void;
  onEdit: () => void;
  onDelete: (strategy: Strategy) => void;
  onDuplicate: (strategy: Strategy) => void;
  getDirectionBadge: (direction: string) => JSX.Element;
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  onToggle,
  onEdit,
  onDelete,
  onDuplicate,
  getDirectionBadge
}) => {
  return (
    <Card className="bg-[#111111] border-gray-800 hover:border-gray-700 transition-colors">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-lg font-bold text-white">{strategy.name}</h3>
              {strategy.enabled ? (
                <Badge className="bg-green-500/20 text-green-500 border-green-500/30">
                  <Power className="w-3 h-3 mr-1" />
                  Enabled
                </Badge>
              ) : (
                <Badge className="bg-gray-500/20 text-gray-500 border-gray-500/30">
                  <PowerOff className="w-3 h-3 mr-1" />
                  Disabled
                </Badge>
              )}
            </div>
            {strategy.description && (
              <p className="text-sm text-gray-400 mb-3">{strategy.description}</p>
            )}
            <div className="flex items-center gap-4 text-sm">
              <span className="font-mono text-white font-bold">{strategy.symbol}</span>
              <Badge variant="outline" className="text-xs">{strategy.timeframe}</Badge>
              {getDirectionBadge(strategy.strategy.direction)}
              <span className="text-gray-400">R:R ≥ {strategy.strategy.min_rr}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => onToggle(strategy)}
              variant="outline"
              size="sm"
              title={strategy.enabled ? 'Disable' : 'Enable'}
            >
              {strategy.enabled ? (
                <PowerOff className="w-4 h-4" />
              ) : (
                <Power className="w-4 h-4" />
              )}
            </Button>
            <Button onClick={onEdit} variant="outline" size="sm" title="Edit">
              <Edit className="w-4 h-4" />
            </Button>
            <Button
              onClick={() => onDuplicate(strategy)}
              variant="outline"
              size="sm"
              title="Duplicate"
            >
              <Copy className="w-4 h-4" />
            </Button>
            <Button
              onClick={() => onDelete(strategy)}
              variant="outline"
              size="sm"
              title="Delete"
              className="text-red-500 hover:text-red-400"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Strategy Details */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-800">
          <div>
            <p className="text-xs text-gray-500 mb-1">Sessions</p>
            <div className="flex flex-wrap gap-1">
              {strategy.sessions.map((session) => (
                <Badge key={session} variant="outline" className="text-xs">
                  {session}
                </Badge>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Entry Conditions</p>
            <p className="text-sm text-white">{strategy.conditions.entry.length} rules</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Max Risk</p>
            <p className="text-sm text-white">
              {((strategy.strategy.max_risk_pct || 0.01) * 100).toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">News Embargo</p>
            <p className="text-sm text-white">{strategy.strategy.news_embargo_minutes} min</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StrategyManager;

