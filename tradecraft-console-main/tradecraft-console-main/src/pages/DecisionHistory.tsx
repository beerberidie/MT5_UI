import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChevronLeft,
  Filter,
  Download,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/hooks/use-toast';
import { apiCall } from '@/lib/api';

interface DecisionHistoryItem {
  id: string;
  timestamp: string;
  symbol: string;
  action: string;
  confidence: number;
  direction?: string;
  entry_price?: number;
  stop_loss?: number;
  take_profit?: number;
  rr_ratio?: number;
  status: string;
  source: string;
  notes?: string;
  emnr_flags?: {
    entry?: boolean;
    exit?: boolean;
    strong?: boolean;
    weak?: boolean;
  };
  indicators?: Record<string, any>;
}

interface DecisionStats {
  total_decisions: number;
  by_action: Record<string, number>;
  by_symbol: Record<string, number>;
  by_status: Record<string, number>;
  avg_confidence: number;
  date_range: {
    earliest: string;
    latest: string;
  };
}

const DecisionHistory: React.FC = () => {
  const navigate = useNavigate();
  
  // State
  const [decisions, setDecisions] = useState<DecisionHistoryItem[]>([]);
  const [stats, setStats] = useState<DecisionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Filters
  const [symbolFilter, setSymbolFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [dateFromFilter, setDateFromFilter] = useState('');
  const [dateToFilter, setDateToFilter] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [total, setTotal] = useState(0);

  // Load decision history
  const loadDecisionHistory = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    else setRefreshing(true);
    
    try {
      // Build query params
      const params = new URLSearchParams();
      if (symbolFilter) params.append('symbol', symbolFilter);
      if (actionFilter) params.append('action', actionFilter);
      if (statusFilter) params.append('status', statusFilter);
      if (sourceFilter) params.append('source', sourceFilter);
      if (dateFromFilter) params.append('date_from', dateFromFilter);
      if (dateToFilter) params.append('date_to', dateToFilter);
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      
      const response = await apiCall<{
        items: DecisionHistoryItem[];
        total: number;
        page: number;
        page_size: number;
      }>(`/api/decision-history?${params.toString()}`);
      
      setDecisions(response.items);
      setTotal(response.total);
      
    } catch (error) {
      console.error('Error loading decision history:', error);
      toast({
        title: 'Error',
        description: 'Failed to load decision history',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Load statistics
  const loadStats = async () => {
    try {
      const params = new URLSearchParams();
      if (dateFromFilter) params.append('date_from', dateFromFilter);
      if (dateToFilter) params.append('date_to', dateToFilter);
      
      const response = await apiCall<DecisionStats>(`/api/decision-history/stats?${params.toString()}`);
      setStats(response);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  // Initial load
  useEffect(() => {
    loadDecisionHistory();
    loadStats();
  }, [page, symbolFilter, actionFilter, statusFilter, sourceFilter, dateFromFilter, dateToFilter]);

  // Refresh handler
  const handleRefresh = () => {
    loadDecisionHistory(false);
    loadStats();
  };

  // Reset filters
  const handleResetFilters = () => {
    setSymbolFilter('');
    setActionFilter('');
    setStatusFilter('');
    setSourceFilter('');
    setDateFromFilter('');
    setDateToFilter('');
    setPage(1);
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

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
      case 'executed':
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'rejected':
      case 'cancelled':
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'pending_approval':
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  // Get direction icon
  const getDirectionIcon = (direction?: string) => {
    if (!direction) return null;
    return direction.toLowerCase() === 'long' || direction.toLowerCase() === 'buy'
      ? <TrendingUp className="w-4 h-4 text-green-500" />
      : <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  // Get source badge color
  const getSourceBadgeColor = (source: string) => {
    switch (source) {
      case 'trade_idea':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'evaluation':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'health_check':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-[#111111]">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/')}
                className="text-gray-400 hover:text-white"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back
              </Button>
              <div>
                <h1 className="text-2xl font-bold">Decision History</h1>
                <p className="text-sm text-gray-400">AI evaluation audit trail and trade ideas</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="border-gray-700 hover:bg-gray-800"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card className="bg-[#111111] border-gray-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-400">Total Decisions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_decisions}</div>
              </CardContent>
            </Card>
            
            <Card className="bg-[#111111] border-gray-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-400">Avg Confidence</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.avg_confidence}%</div>
              </CardContent>
            </Card>
            
            <Card className="bg-[#111111] border-gray-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-400">Symbols Tracked</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Object.keys(stats.by_symbol).length}</div>
              </CardContent>
            </Card>
            
            <Card className="bg-[#111111] border-gray-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-400">Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Object.keys(stats.by_action).length}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <Card className="bg-[#111111] border-gray-800 mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Filter className="w-5 h-5" />
                Filters
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleResetFilters}
                className="text-gray-400 hover:text-white"
              >
                Reset
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <Input
                placeholder="Symbol (e.g., EURUSD)"
                value={symbolFilter}
                onChange={(e) => setSymbolFilter(e.target.value.toUpperCase())}
                className="bg-[#0a0a0a] border-gray-700"
              />
              
              <Select value={actionFilter} onValueChange={setActionFilter}>
                <SelectTrigger className="bg-[#0a0a0a] border-gray-700">
                  <SelectValue placeholder="Action" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Actions</SelectItem>
                  <SelectItem value="observe">Observe</SelectItem>
                  <SelectItem value="open_or_scale">Open/Scale</SelectItem>
                  <SelectItem value="pending_only">Pending Only</SelectItem>
                  <SelectItem value="wait_rr">Wait RR</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="bg-[#0a0a0a] border-gray-700">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Statuses</SelectItem>
                  <SelectItem value="pending_approval">Pending</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="executed">Executed</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={sourceFilter} onValueChange={setSourceFilter}>
                <SelectTrigger className="bg-[#0a0a0a] border-gray-700">
                  <SelectValue placeholder="Source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Sources</SelectItem>
                  <SelectItem value="trade_idea">Trade Ideas</SelectItem>
                  <SelectItem value="evaluation">Evaluations</SelectItem>
                  <SelectItem value="health_check">Health Checks</SelectItem>
                </SelectContent>
              </Select>
              
              <Input
                type="date"
                placeholder="From Date"
                value={dateFromFilter}
                onChange={(e) => setDateFromFilter(e.target.value)}
                className="bg-[#0a0a0a] border-gray-700"
              />
              
              <Input
                type="date"
                placeholder="To Date"
                value={dateToFilter}
                onChange={(e) => setDateToFilter(e.target.value)}
                className="bg-[#0a0a0a] border-gray-700"
              />
            </div>
          </CardContent>
        </Card>

        {/* Decision History Table */}
        <Card className="bg-[#111111] border-gray-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Decision Timeline ({total} total)</CardTitle>
              <Button
                variant="outline"
                size="sm"
                className="border-gray-700 hover:bg-gray-800"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
              </div>
            ) : decisions.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No decision history found</p>
                <p className="text-sm mt-2">Try adjusting your filters</p>
              </div>
            ) : (
              <div className="space-y-2">
                {decisions.map((decision) => (
                  <div
                    key={decision.id}
                    className="p-4 bg-[#0a0a0a] border border-gray-800 rounded-lg hover:border-gray-700 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {getStatusIcon(decision.status)}
                          {getDirectionIcon(decision.direction)}
                          <span className="font-mono font-bold text-lg">{decision.symbol}</span>
                          <Badge className={`${getSourceBadgeColor(decision.source)} border`}>
                            {decision.source.replace('_', ' ')}
                          </Badge>
                          <Badge variant="outline" className="border-gray-700">
                            {decision.action}
                          </Badge>
                          <span className="text-sm text-gray-400">{formatTimestamp(decision.timestamp)}</span>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-400">Confidence:</span>
                            <span className={`ml-2 font-bold ${
                              decision.confidence >= 80 ? 'text-green-400' :
                              decision.confidence >= 60 ? 'text-yellow-400' :
                              'text-red-400'
                            }`}>
                              {decision.confidence}%
                            </span>
                          </div>
                          
                          {decision.entry_price && (
                            <div>
                              <span className="text-gray-400">Entry:</span>
                              <span className="ml-2 font-mono">{decision.entry_price.toFixed(5)}</span>
                            </div>
                          )}
                          
                          {decision.stop_loss && (
                            <div>
                              <span className="text-gray-400">SL:</span>
                              <span className="ml-2 font-mono">{decision.stop_loss.toFixed(5)}</span>
                            </div>
                          )}
                          
                          {decision.take_profit && (
                            <div>
                              <span className="text-gray-400">TP:</span>
                              <span className="ml-2 font-mono">{decision.take_profit.toFixed(5)}</span>
                            </div>
                          )}
                          
                          {decision.rr_ratio && (
                            <div>
                              <span className="text-gray-400">R:R:</span>
                              <span className="ml-2 font-bold text-blue-400">{decision.rr_ratio.toFixed(2)}</span>
                            </div>
                          )}
                        </div>
                        
                        {decision.notes && (
                          <div className="mt-2 text-sm text-gray-400 italic">
                            {decision.notes}
                          </div>
                        )}
                        
                        {decision.emnr_flags && (
                          <div className="mt-2 flex gap-2">
                            {decision.emnr_flags.entry && (
                              <Badge variant="outline" className="border-green-500/30 text-green-400 text-xs">
                                Entry
                              </Badge>
                            )}
                            {decision.emnr_flags.exit && (
                              <Badge variant="outline" className="border-red-500/30 text-red-400 text-xs">
                                Exit
                              </Badge>
                            )}
                            {decision.emnr_flags.strong && (
                              <Badge variant="outline" className="border-blue-500/30 text-blue-400 text-xs">
                                Strong
                              </Badge>
                            )}
                            {decision.emnr_flags.weak && (
                              <Badge variant="outline" className="border-yellow-500/30 text-yellow-400 text-xs">
                                Weak
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {/* Pagination */}
            {total > pageSize && (
              <div className="flex items-center justify-between mt-6 pt-6 border-t border-gray-800">
                <div className="text-sm text-gray-400">
                  Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="border-gray-700 hover:bg-gray-800"
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * pageSize >= total}
                    className="border-gray-700 hover:bg-gray-800"
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DecisionHistory;

