import React, { useState, useEffect } from 'react';
import { AppearanceSettings, getAppearanceSettings, updateAppearanceSettings } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export const AppearanceSection: React.FC = () => {
  const [settings, setSettings] = useState<AppearanceSettings>({
    density: 'normal',
    theme: 'dark',
    font_size: 14,
    accent_color: '#3b82f6',
    show_animations: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await getAppearanceSettings();
      setSettings(data);
    } catch (error: any) {
      toast.error(`Failed to load appearance settings: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateAppearanceSettings(settings);
      toast.success('Appearance settings saved successfully');
    } catch (error: any) {
      toast.error(`Failed to save settings: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    const defaultSettings: AppearanceSettings = {
      density: 'normal',
      theme: 'dark',
      font_size: 14,
      accent_color: '#3b82f6',
      show_animations: true,
    };
    setSettings(defaultSettings);
    toast.success('Settings reset to defaults');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold">Appearance</h3>
        <p className="text-sm text-muted-foreground">
          Customize the look and feel of the application
        </p>
      </div>

      {/* Density Setting */}
      <div className="space-y-3">
        <Label>UI Density</Label>
        <RadioGroup
          value={settings.density}
          onValueChange={(value: any) => setSettings({ ...settings, density: value })}
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="compact" id="density-compact" />
            <Label htmlFor="density-compact" className="font-normal cursor-pointer">
              Compact - More content, less spacing
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="normal" id="density-normal" />
            <Label htmlFor="density-normal" className="font-normal cursor-pointer">
              Normal - Balanced spacing (recommended)
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="comfortable" id="density-comfortable" />
            <Label htmlFor="density-comfortable" className="font-normal cursor-pointer">
              Comfortable - More spacing, easier to read
            </Label>
          </div>
        </RadioGroup>
      </div>

      {/* Theme Setting */}
      <div className="space-y-3">
        <Label>Theme</Label>
        <RadioGroup
          value={settings.theme}
          onValueChange={(value: any) => setSettings({ ...settings, theme: value })}
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="dark" id="theme-dark" />
            <Label htmlFor="theme-dark" className="font-normal cursor-pointer">
              Dark - Optimized for low-light environments
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="light" id="theme-light" />
            <Label htmlFor="theme-light" className="font-normal cursor-pointer">
              Light - Bright and clean interface
            </Label>
          </div>
        </RadioGroup>
      </div>

      {/* Font Size Setting */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Font Size</Label>
          <span className="text-sm text-muted-foreground">{settings.font_size}px</span>
        </div>
        <Slider
          value={[settings.font_size]}
          onValueChange={(value) => setSettings({ ...settings, font_size: value[0] })}
          min={12}
          max={18}
          step={1}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          Adjust the base font size for better readability
        </p>
      </div>

      {/* Accent Color Setting */}
      <div className="space-y-3">
        <Label htmlFor="accent-color">Accent Color</Label>
        <div className="flex items-center gap-3">
          <input
            id="accent-color"
            type="color"
            value={settings.accent_color}
            onChange={(e) => setSettings({ ...settings, accent_color: e.target.value })}
            className="w-16 h-10 rounded border border-border cursor-pointer"
          />
          <span className="text-sm text-muted-foreground">{settings.accent_color}</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Choose a color for buttons, links, and highlights
        </p>
      </div>

      {/* Animations Setting */}
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <Label htmlFor="show-animations">Show Animations</Label>
          <p className="text-xs text-muted-foreground">
            Enable smooth transitions and animations
          </p>
        </div>
        <Switch
          id="show-animations"
          checked={settings.show_animations}
          onCheckedChange={(checked) => setSettings({ ...settings, show_animations: checked })}
        />
      </div>

      {/* Preview Section */}
      <Alert>
        <CheckCircle2 className="h-4 w-4" />
        <AlertDescription>
          <strong>Preview:</strong> Changes will be applied after saving. Some changes may require a page refresh to take full effect.
        </AlertDescription>
      </Alert>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-4">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Save Changes'
          )}
        </Button>
        <Button onClick={handleReset} variant="outline" disabled={saving}>
          Reset to Defaults
        </Button>
      </div>

      {/* Info Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Note:</strong> Appearance settings are stored globally and will apply to all sessions. Theme and density changes may require a page refresh to fully apply.
        </AlertDescription>
      </Alert>
    </div>
  );
};

