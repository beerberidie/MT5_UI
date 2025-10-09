import React, { useState, useEffect } from 'react';
import {
  MT5Account,
  getAccounts,
  createAccount,
  deleteAccount,
  activateAccount,
  testAccountConnection,
} from '@/lib/api';
import { AccountCard } from './AccountCard';
import { AddAccountDialog } from './AddAccountDialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Plus, AlertCircle, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export const AccountsSection: React.FC = () => {
  const [accounts, setAccounts] = useState<MT5Account[]>([]);
  const [activeAccountId, setActiveAccountId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Load accounts on mount
  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const data = await getAccounts();
      setAccounts(data.accounts);
      setActiveAccountId(data.active_account_id);
    } catch (error: any) {
      toast.error(`Failed to load accounts: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAccount = async (account: {
    name: string;
    login: number;
    password: string;
    server: string;
  }) => {
    await createAccount(account);
    await loadAccounts(); // Reload accounts
  };

  const handleActivateAccount = async (accountId: string) => {
    await activateAccount(accountId);
    await loadAccounts(); // Reload to update active status
  };

  const handleRemoveAccount = async (accountId: string) => {
    await deleteAccount(accountId);
    await loadAccounts(); // Reload accounts
  };

  const handleTestConnection = async (accountId: string) => {
    const result = await testAccountConnection(accountId);

    if (result.connected) {
      toast.success(
        <div>
          <div className="font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            Connection Successful
          </div>
          {result.account_info && (
            <div className="text-sm mt-1">
              Balance: {result.account_info.balance} {result.account_info.currency}
              <br />
              Equity: {result.account_info.equity} {result.account_info.currency}
              <br />
              Leverage: 1:{result.account_info.leverage}
            </div>
          )}
        </div>
      );
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
          <h3 className="text-lg font-semibold">MT5 Accounts</h3>
          <p className="text-sm text-muted-foreground">
            Manage your MetaTrader 5 trading accounts
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Account
        </Button>
      </div>

      {/* Info Alert */}
      {accounts.length === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No MT5 accounts configured. Add your first account to get started.
          </AlertDescription>
        </Alert>
      )}

      {accounts.length > 0 && !activeAccountId && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No active account selected. Please activate an account to enable trading.
          </AlertDescription>
        </Alert>
      )}

      {/* Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {accounts.map((account) => (
          <AccountCard
            key={account.id}
            account={account}
            isActive={account.id === activeAccountId}
            onActivate={() => handleActivateAccount(account.id)}
            onRemove={() => handleRemoveAccount(account.id)}
            onTest={() => handleTestConnection(account.id)}
          />
        ))}
      </div>

      {/* Add Account Dialog */}
      <AddAccountDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleAddAccount}
      />

      {/* Security Notice */}
      <Alert className="mt-6">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Security Notice:</strong> Your account passwords are encrypted using AES-128
          encryption before storage. Passwords are never transmitted or displayed in plaintext.
          Only one account can be active at a time.
        </AlertDescription>
      </Alert>
    </div>
  );
};

