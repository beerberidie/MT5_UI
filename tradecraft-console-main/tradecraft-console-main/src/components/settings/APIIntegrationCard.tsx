import React, { useState } from 'react';
import { APIIntegration } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, XCircle, Loader2, Trash2, TestTube, Calendar, Newspaper, Code } from 'lucide-react';
import { toast } from 'sonner';

interface APIIntegrationCardProps {
  integration: APIIntegration;
  onRemove: () => Promise<void>;
  onTest: () => Promise<void>;
}

export const APIIntegrationCard: React.FC<APIIntegrationCardProps> = ({
  integration,
  onRemove,
  onTest,
}) => {
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);

  const handleRemove = async () => {
    if (!confirm(`Are you sure you want to remove integration "${integration.name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      await onRemove();
      toast.success(`Integration "${integration.name}" removed`);
    } catch (error: any) {
      toast.error(`Failed to remove integration: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      await onTest();
    } catch (error: any) {
      toast.error(`Connection test failed: ${error.message}`);
    } finally {
      setTesting(false);
    }
  };

  const getStatusBadge = () => {
    if (integration.status === 'active') {
      return (
        <Badge variant="default" className="bg-green-600 hover:bg-green-700">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Active
        </Badge>
      );
    } else if (integration.status === 'error') {
      return (
        <Badge variant="destructive">
          <XCircle className="w-3 h-3 mr-1" />
          Error
        </Badge>
      );
    } else {
      return (
        <Badge variant="secondary">
          Inactive
        </Badge>
      );
    }
  };

  const getTypeIcon = () => {
    switch (integration.type) {
      case 'economic_calendar':
        return <Calendar className="w-4 h-4" />;
      case 'news':
        return <Newspaper className="w-4 h-4" />;
      default:
        return <Code className="w-4 h-4" />;
    }
  };

  const getTypeLabel = () => {
    switch (integration.type) {
      case 'economic_calendar':
        return 'Economic Calendar';
      case 'news':
        return 'News API';
      default:
        return 'Custom';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              {getTypeIcon()}
              {integration.name}
            </CardTitle>
            <CardDescription className="mt-1">
              Type: {getTypeLabel()}
              {integration.base_url && (
                <>
                  <br />
                  URL: {integration.base_url}
                </>
              )}
            </CardDescription>
          </div>
          <div>{getStatusBadge()}</div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* API Key (masked) */}
          <div className="text-xs text-muted-foreground">
            API Key: {integration.api_key_masked}
          </div>

          {/* Last Tested */}
          {integration.last_tested && (
            <div className="text-xs text-muted-foreground">
              Last tested: {new Date(integration.last_tested).toLocaleString()}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              onClick={handleTest}
              disabled={testing || loading}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              {testing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <TestTube className="w-4 h-4 mr-2" />
                  Test Connection
                </>
              )}
            </Button>

            <Button
              onClick={handleRemove}
              disabled={loading}
              variant="destructive"
              size="sm"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>

          {/* Created Date */}
          <div className="text-xs text-muted-foreground">
            Created: {new Date(integration.created_at).toLocaleDateString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

