import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

interface AddAccountDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (account: {
    name: string;
    login: number;
    password: string;
    server: string;
  }) => Promise<void>;
}

export const AddAccountDialog: React.FC<AddAccountDialogProps> = ({
  open,
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState('');
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [server, setServer] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!name.trim()) {
      toast.error('Please enter an account name');
      return;
    }

    const loginNum = parseInt(login);
    if (!login || isNaN(loginNum) || loginNum <= 0) {
      toast.error('Please enter a valid login number');
      return;
    }

    if (!password) {
      toast.error('Please enter a password');
      return;
    }

    if (!server.trim()) {
      toast.error('Please enter a server name');
      return;
    }

    setLoading(true);
    try {
      await onSubmit({
        name: name.trim(),
        login: loginNum,
        password,
        server: server.trim(),
      });

      // Reset form
      setName('');
      setLogin('');
      setPassword('');
      setServer('');
      setShowPassword(false);

      toast.success('Account added successfully');
      onClose();
    } catch (error: any) {
      toast.error(`Failed to add account: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (loading) return; // Prevent closing while loading
    
    // Reset form
    setName('');
    setLogin('');
    setPassword('');
    setServer('');
    setShowPassword(false);
    
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add MT5 Account</DialogTitle>
          <DialogDescription>
            Add a new MetaTrader 5 account. Your password will be encrypted and stored securely.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {/* Account Name */}
            <div className="grid gap-2">
              <Label htmlFor="account-name">Account Name</Label>
              <Input
                id="account-name"
                placeholder="e.g., Demo Account, Live Account"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
                autoFocus
              />
            </div>

            {/* Login */}
            <div className="grid gap-2">
              <Label htmlFor="account-login">Login Number</Label>
              <Input
                id="account-login"
                type="number"
                placeholder="e.g., 107030709"
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                disabled={loading}
              />
            </div>

            {/* Password */}
            <div className="grid gap-2">
              <Label htmlFor="account-password">Password</Label>
              <div className="relative">
                <Input
                  id="account-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your MT5 password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  disabled={loading}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Your password will be encrypted before storage
              </p>
            </div>

            {/* Server */}
            <div className="grid gap-2">
              <Label htmlFor="account-server">Server</Label>
              <Input
                id="account-server"
                placeholder="e.g., MetaQuotes-Demo"
                value={server}
                onChange={(e) => setServer(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Adding...
                </>
              ) : (
                'Add Account'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

