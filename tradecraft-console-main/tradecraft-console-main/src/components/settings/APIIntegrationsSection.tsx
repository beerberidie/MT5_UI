import React, { useState, useEffect } from 'react';
import {
  APIIntegration,
  getAPIIntegrations,
  createAPIIntegration,
  deleteAPIIntegration,
  testAPIIntegration,
} from '@/lib/api';
import { APIIntegrationCard } from './APIIntegrationCard';
import { AddAPIIntegrationDialog } from './AddAPIIntegrationDialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Plus, AlertCircle, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export const APIIntegrationsSection: React.FC = () => {
  const [integrations, setIntegrations] = useState<APIIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Load integrations on mount
  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    setLoading(true);
    try {
      const data = await getAPIIntegrations();
      setIntegrations(data.integrations);
    } catch (error: any) {
      toast.error(`Failed to load integrations: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddIntegration = async (integration: {
    name: string;
    type: 'economic_calendar' | 'news' | 'custom';
    api_key: string;
    base_url?: string;
    config?: Record<string, any>;
  }) => {
    await createAPIIntegration(integration);
    await loadIntegrations(); // Reload integrations
  };

  const handleRemoveIntegration = async (integrationId: string) => {
    await deleteAPIIntegration(integrationId);
    await loadIntegrations(); // Reload integrations
  };

  const handleTestConnection = async (integrationId: string) => {
    const result = await testAPIIntegration(integrationId);

    if (result.connected) {
      toast.success(
        <div>
          <div className="font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            Connection Successful
          </div>
          {result.response_data && (
            <div className="text-sm mt-1">
              {Object.entries(result.response_data).map(([key, value]) => (
                <div key={key}>
                  {key}: {String(value)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
      // Reload to update status
      await loadIntegrations();
    } else {
      toast.error(
        <div>
          <div className="font-semibold">Connection Failed</div>
          <div className="text-sm mt-1">{result.error || 'Unknown error'}</div>
        </div>
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">API Integrations</h3>
          <p className="text-sm text-muted-foreground">
            Manage third-party API integrations for economic data, news, and more
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Integration
        </Button>
      </div>

      {/* Info Alert */}
      {integrations.length === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No API integrations configured. Add your first integration to access economic calendars, news feeds, and other data sources.
          </AlertDescription>
        </Alert>
      )}

      {/* Integrations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {integrations.map((integration) => (
          <APIIntegrationCard
            key={integration.id}
            integration={integration}
            onRemove={() => handleRemoveIntegration(integration.id)}
            onTest={() => handleTestConnection(integration.id)}
          />
        ))}
      </div>

      {/* Add Integration Dialog */}
      <AddAPIIntegrationDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleAddIntegration}
      />

      {/* Security Notice */}
      <Alert className="mt-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Security Notice:</strong> Your API keys are encrypted using AES-128
          encryption before storage. API keys are never transmitted or displayed in plaintext.
          Only the last 4 characters are shown for verification.
        </AlertDescription>
      </Alert>

      {/* Integration Types Info */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Supported Integration Types:</strong>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li><strong>Economic Calendar:</strong> Econdb API for economic indicators and events</li>
            <li><strong>News API:</strong> NewsAPI or Finnhub for market news and sentiment</li>
            <li><strong>Custom:</strong> Any REST API with Bearer token authentication</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
};

