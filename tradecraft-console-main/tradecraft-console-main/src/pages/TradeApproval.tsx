import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChevronLeft,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Edit,
  Trash2,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from '@/hooks/use-toast';
import { apiCall } from '@/lib/api';
import TradeIdeaDetailModal from '@/components/TradeIdeaDetailModal';

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

const TradeApproval: React.FC = () => {
  const navigate = useNavigate();
  
  // State
  const [tradeIdeas, setTradeIdeas] = useState<TradeIdea[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('pending');
  const [selectedTradeIdea, setSelectedTradeIdea] = useState<TradeIdea | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  
  // Counts
  const [pendingCount, setPendingCount] = useState(0);
  const [approvedCount, setApprovedCount] = useState(0);
  const [rejectedCount, setRejectedCount] = useState(0);

  // Load trade ideas
  const loadTradeIdeas = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    else setRefreshing(true);
    
    try {
      const response = await apiCall<{
        items: TradeIdea[];
        total: number;
        pending_count: number;
        approved_count: number;
        rejected_count: number;
      }>('/api/trade-approval');
      
      setTradeIdeas(response.items);
      setPendingCount(response.pending_count);
      setApprovedCount(response.approved_count);
      setRejectedCount(response.rejected_count);
      
    } catch (error) {
      console.error('Error loading trade ideas:', error);
      toast({
        title: 'Error',
        description: 'Failed to load trade ideas',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadTradeIdeas();
  }, []);

  // Refresh handler
  const handleRefresh = () => {
    loadTradeIdeas(false);
  };

  // Approve trade idea
  const handleApprove = async (tradeIdea: TradeIdea) => {
    try {
      await apiCall('/api/trade-approval/approve', {
        method: 'POST',
        body: JSON.stringify({
          trade_idea_id: tradeIdea.id,
          approved_by: 'user'
        })
      });
      
      toast({
        title: 'Success',
        description: `Trade idea ${tradeIdea.symbol} approved`,
      });
      
      loadTradeIdeas(false);
    } catch (error) {
      console.error('Error approving trade idea:', error);
      toast({
        title: 'Error',
        description: 'Failed to approve trade idea',
        variant: 'destructive'
      });
    }
  };

  // Reject trade idea
  const handleReject = async (tradeIdea: TradeIdea, reason: string) => {
    try {
      await apiCall('/api/trade-approval/reject', {
        method: 'POST',
        body: JSON.stringify({
          trade_idea_id: tradeIdea.id,
          rejected_by: 'user',
          rejection_reason: reason
        })
      });
      
      toast({
        title: 'Success',
        description: `Trade idea ${tradeIdea.symbol} rejected`,
      });
      
      loadTradeIdeas(false);
    } catch (error) {
      console.error('Error rejecting trade idea:', error);
      toast({
        title: 'Error',
        description: 'Failed to reject trade idea',
        variant: 'destructive'
      });
    }
  };

  // Cancel trade idea
  const handleCancel = async (tradeIdea: TradeIdea) => {
    try {
      await apiCall(`/api/trade-approval/${tradeIdea.id}`, {
        method: 'DELETE'
      });
      
      toast({
        title: 'Success',
        description: `Trade idea ${tradeIdea.symbol} cancelled`,
      });
      
      loadTradeIdeas(false);
    } catch (error) {
      console.error('Error cancelling trade idea:', error);
      toast({
        title: 'Error',
        description: 'Failed to cancel trade idea',
        variant: 'destructive'
      });
    }
  };

  // Open detail modal
  const handleViewDetails = (tradeIdea: TradeIdea) => {
    setSelectedTradeIdea(tradeIdea);
    setShowDetailModal(true);
  };

  // Close detail modal
  const handleCloseModal = () => {
    setShowDetailModal(false);
    setSelectedTradeIdea(null);
  };

  // Handle modal save (approve with overrides)
  const handleModalSave = async (tradeIdea: TradeIdea, overrides?: Record<string, any>) => {
    try {
      await apiCall('/api/trade-approval/approve', {
        method: 'POST',
        body: JSON.stringify({
          trade_idea_id: tradeIdea.id,
          approved_by: 'user',
          manual_overrides: overrides
        })
      });
      
      toast({
        title: 'Success',
        description: `Trade idea ${tradeIdea.symbol} approved with overrides`,
      });
      
      handleCloseModal();
      loadTradeIdeas(false);
    } catch (error) {
      console.error('Error approving with overrides:', error);
      toast({
        title: 'Error',
        description: 'Failed to approve trade idea',
        variant: 'destructive'
      });
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  // Get direction icon
  const getDirectionIcon = (direction?: string) => {
    if (!direction) return null;
    return direction.toLowerCase() === 'long' || direction.toLowerCase() === 'buy'
      ? <TrendingUp className="w-5 h-5 text-green-500" />
      : <TrendingDown className="w-5 h-5 text-red-500" />;
  };

  // Filter trade ideas by tab
  const getFilteredTradeIdeas = () => {
    switch (activeTab) {
      case 'pending':
        return tradeIdeas.filter(ti => !ti.approval_status || ti.approval_status === 'pending');
      case 'approved':
        return tradeIdeas.filter(ti => ti.approval_status === 'approved');
      case 'rejected':
        return tradeIdeas.filter(ti => ti.approval_status === 'rejected');
      default:
        return tradeIdeas;
    }
  };

  const filteredTradeIdeas = getFilteredTradeIdeas();

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
                <h1 className="text-2xl font-bold">Trade Approval</h1>
                <p className="text-sm text-gray-400">Review and approve AI-generated trade ideas</p>
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card className="bg-[#111111] border-gray-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
                <Clock className="w-4 h-4 text-yellow-500" />
                Pending Approval
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-500">{pendingCount}</div>
            </CardContent>
          </Card>
          
          <Card className="bg-[#111111] border-gray-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Approved
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-500">{approvedCount}</div>
            </CardContent>
          </Card>
          
          <Card className="bg-[#111111] border-gray-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-400 flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-500" />
                Rejected
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-500">{rejectedCount}</div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Card className="bg-[#111111] border-gray-800">
          <CardHeader>
            <CardTitle>Trade Ideas</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="bg-[#0a0a0a] border border-gray-800">
                <TabsTrigger value="pending" className="data-[state=active]:bg-gray-800">
                  Pending ({pendingCount})
                </TabsTrigger>
                <TabsTrigger value="approved" className="data-[state=active]:bg-gray-800">
                  Approved ({approvedCount})
                </TabsTrigger>
                <TabsTrigger value="rejected" className="data-[state=active]:bg-gray-800">
                  Rejected ({rejectedCount})
                </TabsTrigger>
              </TabsList>

              {loading ? (
                <div className="flex items-center justify-center py-12 mt-4">
                  <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
                </div>
              ) : filteredTradeIdeas.length === 0 ? (
                <div className="text-center py-12 mt-4 text-gray-400">
                  <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No {activeTab} trade ideas</p>
                </div>
              ) : (
                <div className="mt-4 space-y-3">
                  {filteredTradeIdeas.map((tradeIdea) => (
                    <div
                      key={tradeIdea.id}
                      className="p-4 bg-[#0a0a0a] border border-gray-800 rounded-lg hover:border-gray-700 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          {/* Header */}
                          <div className="flex items-center gap-3 mb-3">
                            {getDirectionIcon(tradeIdea.direction)}
                            <span className="font-mono font-bold text-xl">{tradeIdea.symbol}</span>
                            <Badge variant="outline" className="border-gray-700">
                              {tradeIdea.timeframe}
                            </Badge>
                            <Badge variant="outline" className="border-gray-700">
                              {tradeIdea.action}
                            </Badge>
                            <span className="text-sm text-gray-400">{formatTimestamp(tradeIdea.timestamp)}</span>
                          </div>

                          {/* Details Grid */}
                          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm mb-3">
                            <div>
                              <span className="text-gray-400">Confidence:</span>
                              <span className={`ml-2 font-bold ${
                                tradeIdea.confidence >= 80 ? 'text-green-400' :
                                tradeIdea.confidence >= 60 ? 'text-yellow-400' :
                                'text-red-400'
                              }`}>
                                {tradeIdea.confidence}%
                              </span>
                            </div>

                            {tradeIdea.entry_price && (
                              <div>
                                <span className="text-gray-400">Entry:</span>
                                <span className="ml-2 font-mono">{tradeIdea.entry_price.toFixed(5)}</span>
                              </div>
                            )}

                            {tradeIdea.stop_loss && (
                              <div>
                                <span className="text-gray-400">SL:</span>
                                <span className="ml-2 font-mono">{tradeIdea.stop_loss.toFixed(5)}</span>
                              </div>
                            )}

                            {tradeIdea.take_profit && (
                              <div>
                                <span className="text-gray-400">TP:</span>
                                <span className="ml-2 font-mono">{tradeIdea.take_profit.toFixed(5)}</span>
                              </div>
                            )}

                            {tradeIdea.rr_ratio && (
                              <div>
                                <span className="text-gray-400">R:R:</span>
                                <span className="ml-2 font-bold text-blue-400">{tradeIdea.rr_ratio.toFixed(2)}</span>
                              </div>
                            )}
                          </div>

                          {/* Notes */}
                          {tradeIdea.notes && (
                            <div className="text-sm text-gray-400 italic mb-3">
                              {tradeIdea.notes}
                            </div>
                          )}

                          {/* Manual Overrides Badge */}
                          {tradeIdea.manual_overrides && (
                            <Badge variant="outline" className="border-blue-500/30 text-blue-400 mb-3">
                              Manual Overrides Applied
                            </Badge>
                          )}

                          {/* Rejection Reason */}
                          {tradeIdea.rejection_reason && (
                            <div className="text-sm text-red-400 mb-3">
                              <strong>Rejection Reason:</strong> {tradeIdea.rejection_reason}
                            </div>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2 ml-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleViewDetails(tradeIdea)}
                            className="border-gray-700 hover:bg-gray-800"
                          >
                            <Edit className="w-4 h-4 mr-1" />
                            Details
                          </Button>

                          {activeTab === 'pending' && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleApprove(tradeIdea)}
                                className="border-green-500/30 text-green-400 hover:bg-green-500/10"
                              >
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Approve
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleReject(tradeIdea, 'Rejected by user')}
                                className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                              >
                                <XCircle className="w-4 h-4 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}

                          {activeTab === 'approved' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleCancel(tradeIdea)}
                              className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                            >
                              <Trash2 className="w-4 h-4 mr-1" />
                              Cancel
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Tabs>
          </CardContent>
        </Card>
      </div>

      {/* Detail Modal */}
      {showDetailModal && selectedTradeIdea && (
        <TradeIdeaDetailModal
          tradeIdea={selectedTradeIdea}
          onClose={handleCloseModal}
          onSave={handleModalSave}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
    </div>
  );
};

export default TradeApproval;

