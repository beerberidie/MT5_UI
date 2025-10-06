import React, { useMemo, useState } from 'react';
import { useSettings, RiskSettings } from '@/lib/settings-context';

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

const Settings: React.FC = () => {
  const { risk, setRisk, resetDefaults } = useSettings();
  const [tab, setTab] = useState<'ACCOUNTS' | 'APIS' | 'APPEARANCE' | 'RISK'>('RISK');
  const [local, setLocal] = useState<RiskSettings>(risk);
  const [error, setError] = useState<string>('');
  const [saved, setSaved] = useState<boolean>(false);

  const canSave = useMemo(() => {
    if (local.maxRiskPercent < 0.1 || local.maxRiskPercent > 10) return false;
    if (local.defaultRiskPercent < 0.1 || local.defaultRiskPercent > 10) return false;
    if (local.rrTarget <= 0.5 || local.rrTarget > 5) return false;
    return true;
  }, [local]);

  const onSave = () => {
    if (!canSave) {
      setError('Please correct validation errors.');
      setSaved(false);
      return;
    }
    setError('');
    setSaved(true);
    setRisk(local);
    setTimeout(() => setSaved(false), 1200);
  };

  const onReset = () => {
    resetDefaults();
    setLocal({ ...risk });
  };

  const RiskTab = (
    <div className="p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="maxRisk" className="block text-xs font-medium text-text-secondary mb-1">Maximum risk % (0.1 - 10)</label>
          <input
            id="risk-max"
            aria-label="Maximum risk %"
            type="number"
            className="trading-input w-full"
            step="0.1"
            min={0.1}
            max={10}
            value={local.maxRiskPercent}
            onChange={(e) => {
              const v = clamp(parseFloat(e.target.value || '0'), 0.1, 10);
              setLocal({ ...local, maxRiskPercent: v });
            }}
          />
        </div>
        <div>
          <label htmlFor="defaultRisk" className="block text-xs font-medium text-text-secondary mb-1">Default risk % for new orders</label>
          <input
            id="risk-default"
            aria-label="Default risk %"
            type="number"
            className="trading-input w-full"
            step="0.1"
            min={0.1}
            max={10}
            value={local.defaultRiskPercent}
            onChange={(e) => {
              const v = clamp(parseFloat(e.target.value || '0'), 0.1, 10);
              setLocal({ ...local, defaultRiskPercent: v });
            }}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">SL/TP Scaling strategy</label>
          <select
            id="risk-strategy"
            aria-label="SL/TP scaling strategy"
            className="trading-input w-full"
            value={local.sltpStrategy}
            onChange={(e) => setLocal({ ...local, sltpStrategy: e.target.value as any })}
          >
            <option value="ATR">ATR-based</option>
            <option value="PIPS">Pips-based</option>
            <option value="PERCENT">Percentage-based</option>
          </select>
        </div>
        <div>
          <label htmlFor="rrTarget" className="block text-xs font-medium text-text-secondary mb-1">Risk-reward ratio target</label>
          <input
            id="risk-rr"
            aria-label="Risk-reward target"
            type="number"
            className="trading-input w-full"
            step="0.1"
            min={0.5}
            max={5}
            value={local.rrTarget}
            onChange={(e) => {
              const v = clamp(parseFloat(e.target.value || '0'), 0.5, 5);
              setLocal({ ...local, rrTarget: v });
            }}
          />
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <button id="settings-save" type="button" onClick={onSave} className="btn-secondary">Save</button>
        <button id="settings-reset" type="button" onClick={onReset} className="btn-secondary">Reset to defaults</button>
        {saved && <span className="text-xs text-text-secondary ml-2">Saved</span>}
        {error && <span className="text-xs text-trading-danger ml-2">{error}</span>}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background text-text-primary">
      <div className="h-header bg-panel border-b border-border flex items-center px-4">
        <h1 className="text-lg font-semibold">Settings</h1>
      </div>

      <div className="max-w-5xl mx-auto p-4">
        <div className="border-b border-border mb-3">
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => setTab('ACCOUNTS')}
              className={`px-3 py-1.5 text-sm rounded ${tab==='ACCOUNTS' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}`}
            >
              Accounts
            </button>
            <button
              type="button"
              onClick={() => setTab('APIS')}
              className={`px-3 py-1.5 text-sm rounded ${tab==='APIS' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}`}
            >
              API Integrations
            </button>
            <button
              type="button"
              onClick={() => setTab('APPEARANCE')}
              className={`px-3 py-1.5 text-sm rounded ${tab==='APPEARANCE' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}`}
            >
              Appearance
            </button>
            <button
              type="button"
              onClick={() => setTab('RISK')}
              className={`px-3 py-1.5 text-sm rounded ${tab==='RISK' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}`}
            >
              Risk Management
            </button>
          </div>
        </div>

        <div className="trading-panel">
          <div className="trading-header">
            <h3 className="font-medium">{tab === 'RISK' ? 'Risk Management' : tab === 'APPEARANCE' ? 'Appearance' : tab === 'APIS' ? 'API Integrations' : 'Accounts'}</h3>
          </div>
          <div className="trading-content">
            {tab === 'RISK' && RiskTab}
            {tab === 'ACCOUNTS' && (
              <div className="text-sm text-text-secondary">Accounts management placeholder (add/remove MT5 accounts).</div>
            )}
            {tab === 'APIS' && (
              <div className="text-sm text-text-secondary">API keys / credentials placeholders.</div>
            )}
            {tab === 'APPEARANCE' && (
              <div className="text-sm text-text-secondary">Appearance customization placeholders (density/scale previews).</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;

