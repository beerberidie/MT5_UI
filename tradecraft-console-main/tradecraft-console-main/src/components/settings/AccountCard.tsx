import React, { useState } from 'react';
import { MT5Account } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, XCircle, Loader2, Trash2, Power, TestTube } from 'lucide-react';
import { toast } from 'sonner';

interface AccountCardProps {
  account: MT5Account;
  isActive: boolean;
  onActivate: () => Promise<void>;
  onRemove: () => Promise<void>;
  onTest: () => Promise<void>;
}

export const AccountCard: React.FC<AccountCardProps> = ({
  account,
  isActive,
  onActivate,
  onRemove,
  onTest,
}) => {
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);

  const handleActivate = async () => {
    if (isActive) return; // Already active
    
    setLoading(true);
    try {
      await onActivate();
      toast.success(`Account "${account.name}" activated`);
    } catch (error: any) {
      toast.error(`Failed to activate account: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async () => {
    if (isActive) {
      toast.error('Cannot remove active account. Please activate another account first.');
      return;
    }

    if (!confirm(`Are you sure you want to remove account "${account.name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      await onRemove();
      toast.success(`Account "${account.name}" removed`);
    } catch (error: any) {
      toast.error(`Failed to remove account: ${error.message}`);
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
    if (account.status === 'connected') {
      return (
        <Badge variant="default" className="bg-green-600 hover:bg-green-700">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Connected
        </Badge>
      );
    } else if (account.status === 'error') {
      return (
        <Badge variant="destructive">
          <XCircle className="w-3 h-3 mr-1" />
          Error
        </Badge>
      );
    } else {
      return (
        <Badge variant="secondary">
          <XCircle className="w-3 h-3 mr-1" />
          Disconnected
        </Badge>
      );
    }
  };

  return (
    <Card className={`${isActive ? 'border-primary border-2' : ''}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              {account.name}
              {isActive && (
                <Badge variant="default" className="bg-blue-600 hover:bg-blue-700">
                  Active
                </Badge>
              )}
            </CardTitle>
            <CardDescription className="mt-1">
              Login: {account.login} • Server: {account.server}
            </CardDescription>
          </div>
          <div>{getStatusBadge()}</div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          {!isActive && (
            <Button
              onClick={handleActivate}
              disabled={loading}
              variant="default"
              size="sm"
              className="flex-1"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Activating...
                </>
              ) : (
                <>
                  <Power className="w-4 h-4 mr-2" />
                  Activate
                </>
              )}
            </Button>
          )}
          
          <Button
            onClick={handleTest}
            disabled={testing || loading}
            variant="outline"
            size="sm"
            className={isActive ? 'flex-1' : ''}
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

          {!isActive && (
            <Button
              onClick={handleRemove}
              disabled={loading}
              variant="destructive"
              size="sm"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          )}
        </div>

        <div className="mt-3 text-xs text-muted-foreground">
          Created: {new Date(account.created_at).toLocaleDateString()}
        </div>
      </CardContent>
    </Card>
  );
};

