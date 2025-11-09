import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  TrendingUp, 
  TrendingDown,
  Clock,
  Server,
  Shield,
  BarChart3,
  RefreshCw
} from 'lucide-react';
import { apiCall } from '@/lib/api';
import { toast } from 'sonner';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  issues: string[];
  directories: {
    data_dir_exists: boolean;
    log_dir_exists: boolean;
    data_dir_size_mb: number;
    log_dir_size_mb: number;
  };
  application: {
    uptime_hours: number;
    requests: {
      total: number;
      errors: number;
      error_rate: number;
    };
    trading: {
      orders_placed: number;
      orders_failed: number;
      order_success_rate: number;
      positions_opened: number;
      positions_closed: number;
    };
    system: {
      mt5_connected: boolean;
      mt5_connection_failures: number;
    };
  };
  trading: {
    today: {
      orders_total: number;
      orders_successful: number;
      orders_failed: number;
      deals_total: number;
      pnl: number;
    };
  };
  errors: {
    recent_errors: number;
    errors_by_scope: Record<string, number>;
  };
  security: {
    recent_events: number;
    invalid_api_key_attempts: number;
  };
}

interface Alert {
  severity: 'critical' | 'warning' | 'info';
  category: string;
  message: string;
  timestamp: string;
}

export default function Monitoring() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchMonitoringData = async () => {
    try {
      const data = await apiCall('/api/monitoring/dashboard');
      setHealth(data.health);
      setAlerts(data.alerts || []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch monitoring data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchMonitoringData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'unhealthy':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'destructive';
      case 'warning':
        return 'default';
      case 'info':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p className="text-muted-foreground">Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">No monitoring data available</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Monitoring</h1>
          <p className="text-muted-foreground">Real-time system health and performance metrics</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchMonitoringData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Now
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            {getStatusIcon(health.status)}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{health.status}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {health.issues.length} active issue{health.issues.length !== 1 ? 's' : ''}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">MT5 Connection</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health.application.system.mt5_connected ? 'Connected' : 'Disconnected'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {health.application.system.mt5_connection_failures} failure{health.application.system.mt5_connection_failures !== 1 ? 's' : ''}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health.application.uptime_hours.toFixed(1)}h
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {health.application.requests.total} requests
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(health.application.requests.error_rate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {health.application.requests.errors} errors
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Active Alerts ({alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.map((alert, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant={getSeverityColor(alert.severity) as any}>
                      {alert.severity}
                    </Badge>
                    <div>
                      <p className="font-medium">{alert.message}</p>
                      <p className="text-xs text-muted-foreground">{alert.category}</p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detailed Metrics */}
      <Tabs defaultValue="trading" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="trading">Trading</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="trading" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Today's Orders</CardTitle>
                <CardDescription>Order execution statistics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total:</span>
                    <span className="font-bold">{health.trading.today.orders_total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Successful:</span>
                    <span className="font-bold text-green-500">{health.trading.today.orders_successful}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Failed:</span>
                    <span className="font-bold text-red-500">{health.trading.today.orders_failed}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Positions</CardTitle>
                <CardDescription>Position management</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Opened:</span>
                    <span className="font-bold">{health.application.trading.positions_opened}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Closed:</span>
                    <span className="font-bold">{health.application.trading.positions_closed}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Today's P&L</CardTitle>
                <CardDescription>Profit and loss</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  {health.trading.today.pnl >= 0 ? (
                    <TrendingUp className="h-5 w-5 text-green-500" />
                  ) : (
                    <TrendingDown className="h-5 w-5 text-red-500" />
                  )}
                  <span className={`text-2xl font-bold ${health.trading.today.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    ${health.trading.today.pnl.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {health.trading.today.deals_total} deals
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Request Statistics</CardTitle>
              <CardDescription>API request performance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Requests:</span>
                  <span className="font-bold">{health.application.requests.total}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Errors:</span>
                  <span className="font-bold">{health.application.requests.errors}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Error Rate:</span>
                  <span className="font-bold">{(health.application.requests.error_rate * 100).toFixed(2)}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Security Events
              </CardTitle>
              <CardDescription>Last 24 hours</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Events:</span>
                  <span className="font-bold">{health.security.recent_events}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Invalid API Key Attempts:</span>
                  <span className="font-bold text-red-500">{health.security.invalid_api_key_attempts}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Storage</CardTitle>
              <CardDescription>Disk usage</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Data Directory:</span>
                  <span className="font-bold">{health.directories.data_dir_size_mb.toFixed(2)} MB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Log Directory:</span>
                  <span className="font-bold">{health.directories.log_dir_size_mb.toFixed(2)} MB</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

