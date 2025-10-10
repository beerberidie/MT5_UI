import React, { useState, useEffect } from 'react';
import { Calendar, Filter, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { getEconomicCalendar, type EconomicEvent } from '@/lib/api';

const EconomicCalendar: React.FC = () => {
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [fromDate, setFromDate] = useState(new Date().toISOString().split('T')[0]);
  const [toDate, setToDate] = useState(
    new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [selectedCurrencies, setSelectedCurrencies] = useState<string[]>([]);
  const [selectedImpact, setSelectedImpact] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [configurationError, setConfigurationError] = useState<string | null>(null);

  const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD'];
  const impacts = ['high', 'medium', 'low'];

  useEffect(() => {
    loadEvents();
  }, [fromDate, toDate, selectedCurrencies, selectedImpact]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(loadEvents, 60000); // Refresh every minute
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fromDate, toDate, selectedCurrencies, selectedImpact]);

  const loadEvents = async () => {
    setLoading(true);
    setConfigurationError(null);
    try {
      const params: any = {
        from_date: fromDate,
        to_date: toDate,
      };

      if (selectedCurrencies.length > 0) {
        params.currencies = selectedCurrencies.join(',');
      }

      if (selectedImpact) {
        params.impact = selectedImpact;
      }

      const data = await getEconomicCalendar(params);
      setEvents(data.events);
    } catch (error: any) {
      // Check if it's a configuration error (404)
      if (error.message && error.message.includes('No active economic calendar integration')) {
        setConfigurationError(error.message);
      } else {
        toast.error(`Failed to load economic calendar: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const toggleCurrency = (currency: string) => {
    setSelectedCurrencies((prev) =>
      prev.includes(currency)
        ? prev.filter((c) => c !== currency)
        : [...prev, currency]
    );
  };

  const getImpactColor = (impact: string) => {
    switch (impact.toLowerCase()) {
      case 'high':
        return 'text-red-500 bg-red-500/10 border-red-500/30';
      case 'medium':
        return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
      case 'low':
        return 'text-green-500 bg-green-500/10 border-green-500/30';
      default:
        return 'text-gray-500 bg-gray-500/10 border-gray-500/30';
    }
  };

  const formatTime = (timeStr: string) => {
    try {
      const date = new Date(timeStr);
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
    } catch {
      return timeStr;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold">Economic Calendar</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={loadEvents} disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-panel rounded-lg border border-border p-4 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-text-muted" />
          <span className="text-sm font-medium">Filters</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Date Range */}
          <div>
            <label className="text-xs text-text-muted mb-1 block">Date Range</label>
            <div className="flex gap-2">
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="flex-1 px-2 py-1 text-sm bg-background border border-border rounded"
              />
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="flex-1 px-2 py-1 text-sm bg-background border border-border rounded"
              />
            </div>
          </div>

          {/* Currencies */}
          <div>
            <label className="text-xs text-text-muted mb-1 block">Currencies</label>
            <div className="flex flex-wrap gap-1">
              {currencies.map((currency) => (
                <button
                  key={currency}
                  onClick={() => toggleCurrency(currency)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    selectedCurrencies.includes(currency)
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-panel-alt text-text-secondary hover:bg-panel-dark'
                  }`}
                >
                  {currency}
                </button>
              ))}
            </div>
          </div>

          {/* Impact */}
          <div>
            <label className="text-xs text-text-muted mb-1 block">Impact Level</label>
            <div className="flex gap-1">
              <button
                onClick={() => setSelectedImpact('')}
                className={`px-3 py-1 text-xs rounded transition-colors ${
                  selectedImpact === ''
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-panel-alt text-text-secondary hover:bg-panel-dark'
                }`}
              >
                All
              </button>
              {impacts.map((impact) => (
                <button
                  key={impact}
                  onClick={() => setSelectedImpact(impact)}
                  className={`px-3 py-1 text-xs rounded transition-colors capitalize ${
                    selectedImpact === impact
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-panel-alt text-text-secondary hover:bg-panel-dark'
                  }`}
                >
                  {impact}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Configuration Error */}
      {configurationError && (
        <Alert className="mb-4 border-yellow-500/50 bg-yellow-500/10">
          <AlertCircle className="w-4 h-4 text-yellow-500" />
          <AlertDescription className="text-yellow-500">
            <div className="font-medium mb-1">Economic Calendar Not Configured</div>
            <div className="text-sm text-text-muted">
              {configurationError}
            </div>
            <div className="text-sm text-text-muted mt-2">
              Go to <strong>Settings → API Integrations</strong> to configure an Econdb API integration.
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Events List */}
      <div className="flex-1 overflow-auto">
        {loading && events.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : configurationError ? (
          <Alert>
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Please configure an Economic Calendar API integration in Settings to view events.
            </AlertDescription>
          </Alert>
        ) : events.length === 0 ? (
          <Alert>
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              No economic events found for the selected filters. Try adjusting your date range or currency selection.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-2">
            {events.map((event) => (
              <div
                key={event.id}
                className="bg-panel rounded-lg border border-border p-3 hover:bg-panel-dark transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-text-muted">
                        {formatTime(event.time)}
                      </span>
                      <span className="px-2 py-0.5 text-xs font-medium rounded bg-primary/20 text-primary">
                        {event.currency}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded border capitalize ${getImpactColor(
                          event.impact
                        )}`}
                      >
                        {event.impact}
                      </span>
                    </div>
                    <div className="text-sm font-medium text-text-primary mb-2">
                      {event.event}
                    </div>
                    <div className="flex gap-4 text-xs">
                      {event.previous && (
                        <div>
                          <span className="text-text-muted">Previous: </span>
                          <span className="text-text-secondary font-mono">{event.previous}</span>
                        </div>
                      )}
                      {event.forecast && (
                        <div>
                          <span className="text-text-muted">Forecast: </span>
                          <span className="text-text-secondary font-mono">{event.forecast}</span>
                        </div>
                      )}
                      {event.actual && (
                        <div>
                          <span className="text-text-muted">Actual: </span>
                          <span className="text-primary font-mono font-medium">{event.actual}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {events.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="text-xs text-text-muted">
            Showing {events.length} event{events.length !== 1 ? 's' : ''} from {fromDate} to {toDate}
          </div>
        </div>
      )}
    </div>
  );
};

export default EconomicCalendar;

