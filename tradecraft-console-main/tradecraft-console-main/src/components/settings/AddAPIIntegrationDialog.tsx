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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

interface AddAPIIntegrationDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (integration: {
    name: string;
    type: 'economic_calendar' | 'news' | 'custom';
    api_key: string;
    base_url?: string;
    config?: Record<string, any>;
  }) => Promise<void>;
}

export const AddAPIIntegrationDialog: React.FC<AddAPIIntegrationDialogProps> = ({
  open,
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState('');
  const [type, setType] = useState<'economic_calendar' | 'news' | 'custom'>('news');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!name.trim()) {
      toast.error('Please enter an integration name');
      return;
    }

    if (!apiKey) {
      toast.error('Please enter an API key');
      return;
    }

    setLoading(true);
    try {
      await onSubmit({
        name: name.trim(),
        type,
        api_key: apiKey,
        base_url: baseUrl.trim() || undefined,
      });

      // Reset form
      setName('');
      setType('news');
      setApiKey('');
      setBaseUrl('');
      setShowApiKey(false);

      toast.success('Integration added successfully');
      onClose();
    } catch (error: any) {
      toast.error(`Failed to add integration: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (loading) return; // Prevent closing while loading
    
    // Reset form
    setName('');
    setType('news');
    setApiKey('');
    setBaseUrl('');
    setShowApiKey(false);
    
    onClose();
  };

  const getDefaultUrl = () => {
    switch (type) {
      case 'economic_calendar':
        return 'https://www.econdb.com/api';
      case 'news':
        return 'https://newsapi.org/v2';
      default:
        return '';
    }
  };

  const getPlaceholderName = () => {
    switch (type) {
      case 'economic_calendar':
        return 'e.g., Econdb Calendar';
      case 'news':
        return 'e.g., NewsAPI';
      default:
        return 'e.g., My Custom API';
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add API Integration</DialogTitle>
          <DialogDescription>
            Add a new third-party API integration. Your API key will be encrypted and stored securely.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {/* Integration Type */}
            <div className="grid gap-2">
              <Label htmlFor="integration-type">Integration Type</Label>
              <Select
                value={type}
                onValueChange={(value: any) => {
                  setType(value);
                  setBaseUrl(getDefaultUrl());
                }}
                disabled={loading}
              >
                <SelectTrigger id="integration-type">
                  <SelectValue placeholder="Select integration type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="economic_calendar">Economic Calendar (Econdb)</SelectItem>
                  <SelectItem value="news">News API</SelectItem>
                  <SelectItem value="custom">Custom Integration</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Integration Name */}
            <div className="grid gap-2">
              <Label htmlFor="integration-name">Integration Name</Label>
              <Input
                id="integration-name"
                placeholder={getPlaceholderName()}
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
                autoFocus
              />
            </div>

            {/* API Key */}
            <div className="grid gap-2">
              <Label htmlFor="integration-api-key">API Key</Label>
              <div className="relative">
                <Input
                  id="integration-api-key"
                  type={showApiKey ? 'text' : 'password'}
                  placeholder="Enter your API key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  disabled={loading}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  disabled={loading}
                >
                  {showApiKey ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Your API key will be encrypted before storage
              </p>
            </div>

            {/* Base URL */}
            <div className="grid gap-2">
              <Label htmlFor="integration-base-url">Base URL (Optional)</Label>
              <Input
                id="integration-base-url"
                placeholder={getDefaultUrl() || 'https://api.example.com'}
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                Leave empty to use default URL for selected type
              </p>
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
                'Add Integration'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

