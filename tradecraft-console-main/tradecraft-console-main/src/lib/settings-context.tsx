import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

export type RiskStrategy = 'ATR' | 'PIPS' | 'PERCENT';

export interface RiskSettings {
  maxRiskPercent: number; // e.g., 1
  defaultRiskPercent: number; // e.g., 1
  rrTarget: number; // e.g., 1.5
  sltpStrategy: RiskStrategy; // 'ATR' | 'PIPS' | 'PERCENT'
}

const LS_KEY = 'riskSettings.v1';

const DEFAULT_SETTINGS: RiskSettings = {
  maxRiskPercent: 1.0,
  defaultRiskPercent: 1.0,
  rrTarget: 1.5,
  sltpStrategy: 'PIPS',
};

interface SettingsContextValue {
  risk: RiskSettings;
  setRisk: (next: RiskSettings) => void;
  resetDefaults: () => void;
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [risk, setRiskState] = useState<RiskSettings>(DEFAULT_SETTINGS);

  // load from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        // shallow validate
        if (
          typeof parsed.maxRiskPercent === 'number' &&
          typeof parsed.defaultRiskPercent === 'number' &&
          typeof parsed.rrTarget === 'number' &&
          (parsed.sltpStrategy === 'ATR' || parsed.sltpStrategy === 'PIPS' || parsed.sltpStrategy === 'PERCENT')
        ) {
          setRiskState(parsed);
        }
      }
    } catch {}
  }, []);

  // persist to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(risk));
    } catch {}
  }, [risk]);

  const setRisk = (next: RiskSettings) => setRiskState(next);
  const resetDefaults = () => setRiskState(DEFAULT_SETTINGS);

  const value = useMemo(() => ({ risk, setRisk, resetDefaults }), [risk]);

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export const useSettings = (): SettingsContextValue => {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider');
  return ctx;
};

