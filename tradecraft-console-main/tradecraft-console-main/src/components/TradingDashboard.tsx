import React, { useState, useEffect, useRef } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  BarChart3,
  LineChart,
  Settings,
  Wifi,
  WifiOff,
  Menu,
  DollarSign,
  Target,
  Clock,
  Activity,
  X
} from 'lucide-react';
import { getSymbols, getPrioritySymbols, getAccount, getPositions, postOrder, getHistoricalBars, getDeals, getOrdersHistory, getPendingOrders, createPendingOrder, cancelPendingOrder, modifyPendingOrder, closePosition } from '@/lib/api';
import ErrorBoundary from './ErrorBoundary';
import AIStatusIndicator from './ai/AIStatusIndicator';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { toast } from '@/hooks/use-toast';

import { useSettings } from '@/lib/settings-context';

import { useNavigate } from 'react-router-dom';


// Trading Platform Configuration
declare global {
  interface Window {
    CONFIG: {
      API_BASE: string;
      REFRESH_INTERVAL: number;
      CONNECTION_TIMEOUT: number;
      MAX_RETRIES: number;
    };
    AUGMENT_API_KEY?: string;
    getAuthHeaders: () => Record<string, string>;
  }
}

interface AccountInfo {
  balance: number;
  equity: number;
  margin: number;
  freeMargin: number;
  marginLevel: number;
}

interface Position {
  ticket?: number;
  symbol?: string;
  type?: string | number;
  volume?: number;
  openPrice?: number;
  currentPrice?: number;
  profit?: number;
  swap?: number;
  commission?: number;
}

interface Symbol {
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
  change: number;
  changePercent: number;
}



const TradingDashboard: React.FC = () => {
  const navigate = useNavigate();

  const { risk } = useSettings();
  const [userEditedLevels, setUserEditedLevels] = useState(false);
  const lastSideRef = useRef<'buy' | 'sell'>('buy');

  // Data states (moved above effects to avoid TDZ on dependencies)
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [symbols, setSymbols] = useState<Symbol[]>([]);

  // Close position dialog state
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [positionToClose, setPositionToClose] = useState<Position | null>(null);
  const [closingPosition, setClosingPosition] = useState(false);


  const isJPY = (s: string) => s.toUpperCase().includes('JPY');
  const pipSize = (s: string) => (isJPY(s) ? 0.01 : 0.0001);
  const roundPrice = (v: number, s: string) => parseFloat(v.toFixed(isJPY(s) ? 3 : 5));
  const estimateATR = (s: string, price: number) => (isJPY(s) ? 0.15 : 0.0015);

  function getSelectedSymbol(): string {
    const sel = document.getElementById('sym') as HTMLSelectElement | null;
    return (sel?.value || 'EURUSD').toUpperCase();
  }
  function getMarketPrice(sym: string, side: 'buy' | 'sell'): number | null {
    const info = symbols.find((x) => (x.symbol || '').toUpperCase() === sym);
    if (!info) return null;
    return side === 'buy' ? Number(info.ask ?? info.bid ?? 0) : Number(info.bid ?? info.ask ?? 0);
  }

  function computeAutoLevels(side: 'buy' | 'sell') {
    const sym = getSelectedSymbol();
    const entry = getMarketPrice(sym, side);
    if (!entry || entry <= 0) return null;

    // clamp risk percent
    const rp = Math.min(Math.max(risk.defaultRiskPercent, 0.1), risk.maxRiskPercent);

    let slDist = 0;
    if (risk.sltpStrategy === 'PERCENT') {
      slDist = entry * (rp / 100);
    } else if (risk.sltpStrategy === 'PIPS') {
      const ps = pipSize(sym);
      const pips = Math.max(5, Math.round((entry * (rp / 100)) / ps));
      slDist = pips * ps;
    } else {
      // ATR-based (simple fallback estimate)
      const atr = estimateATR(sym, entry);
      slDist = atr; // 1x ATR
    }

    const tpDist = slDist * Math.max(0.5, Math.min(risk.rrTarget || 1.5, 5));

    const sl = side === 'buy' ? entry - slDist : entry + slDist;
    const tp = side === 'buy' ? entry + tpDist : entry - tpDist;

    const slR = roundPrice(sl, sym);
    const tpR = roundPrice(tp, sym);

    // basic sanity checks
    if (slR <= 0 || tpR <= 0 || Math.abs(tpR - slR) < pipSize(sym)) return null;

    return { sl: slR, tp: tpR };
  }

  function applyAutoLevels(side: 'buy' | 'sell') {
    if (userEditedLevels) return;
    const volEl = document.getElementById('volume') as HTMLInputElement | null;
    const vol = volEl?.value ? parseFloat(volEl.value) : 0;
    if (!vol || vol <= 0) return;
    const res = computeAutoLevels(side);
    if (!res) return;
    const slEl = document.getElementById('sl') as HTMLInputElement | null;
    const tpEl = document.getElementById('tp') as HTMLInputElement | null;
    if (slEl) slEl.value = String(res.sl);
    if (tpEl) tpEl.value = String(res.tp);
  }

  // Pending orders: compute auto SL/TP based on pending entry price
  function getPendingSide(): 'buy' | 'sell' {
    const typeEl = document.getElementById('pendingOrderType') as HTMLSelectElement | null;
    const v = (typeEl?.value || '').toLowerCase();
    return v.includes('buy') ? 'buy' : 'sell';
  }

  function computePendingAutoLevels(side: 'buy' | 'sell') {
    const sym = getSelectedSymbol();
    const priceEl = document.getElementById('pendingPrice') as HTMLInputElement | null;
    const entry = priceEl?.value ? parseFloat(priceEl.value) : NaN;
    if (!entry || Number.isNaN(entry) || entry <= 0) return null;

    // clamp risk percent
    const rp = Math.min(Math.max(risk.defaultRiskPercent, 0.1), risk.maxRiskPercent);

    let slDist = 0;
    if (risk.sltpStrategy === 'PERCENT') {
      slDist = entry * (rp / 100);
    } else if (risk.sltpStrategy === 'PIPS') {
      const ps = pipSize(sym);
      const pips = Math.max(5, Math.round((entry * (rp / 100)) / ps));
      slDist = pips * ps;
    } else {
      // ATR-based (simple fallback estimate)
      const ps = pipSize(sym);
      const estAtr = ps * 50; // ~50 pips baseline
      slDist = Math.max(estAtr * (rp / 1.0), ps * 10);
    }

    const tpDist = slDist * Math.max(0.5, Math.min(risk.rrTarget || 1.5, 5));

    const sl = side === 'buy' ? entry - slDist : entry + slDist;
    const tp = side === 'buy' ? entry + tpDist : entry - tpDist;

    const slR = roundPrice(sl, sym);
    const tpR = roundPrice(tp, sym);

    if (slR <= 0 || tpR <= 0 || Math.abs(tpR - slR) < pipSize(sym)) return null;

    return { sl: slR, tp: tpR };
  }

  function applyPendingAutoLevels(side: 'buy' | 'sell') {
    if (userEditedLevels) return;
    const volEl = document.getElementById('volume') as HTMLInputElement | null;
    const vol = volEl?.value ? parseFloat(volEl.value) : 0;
    if (!vol || vol <= 0) return;
    const res = computePendingAutoLevels(side);
    if (!res) return;
    const slEl = document.getElementById('sl') as HTMLInputElement | null;
    const tpEl = document.getElementById('tp') as HTMLInputElement | null;
    if (slEl) slEl.value = String(res.sl);
    if (tpEl) tpEl.value = String(res.tp);
  }


  // Wire auto-fill on volume/symbol change and when risk settings change
  useEffect(() => {
    const volEl = document.getElementById('volume') as HTMLInputElement | null;
    const symEl = document.getElementById('sym') as HTMLSelectElement | null;
    const slEl = document.getElementById('sl') as HTMLInputElement | null;
    const tpEl = document.getElementById('tp') as HTMLInputElement | null;

    const onUserEdit = () => setUserEditedLevels(true);
    slEl?.addEventListener('input', onUserEdit);
    tpEl?.addEventListener('input', onUserEdit);

    const onVolume = () => {
      setUserEditedLevels(false);
      // use last side hint for auto suggestion
      applyAutoLevels(lastSideRef.current);
    };
    const onSymbol = () => applyAutoLevels(lastSideRef.current);
    volEl?.addEventListener('input', onVolume);
    symEl?.addEventListener('change', onSymbol);

    const buyBtn = document.getElementById('buy-btn') as HTMLButtonElement | null;
    const sellBtn = document.getElementById('sell-btn') as HTMLButtonElement | null;
    const onBuySide = () => { lastSideRef.current = 'buy'; applyAutoLevels('buy'); };
    const onSellSide = () => { lastSideRef.current = 'sell'; applyAutoLevels('sell'); };
    buyBtn?.addEventListener('mouseenter', onBuySide);
    buyBtn?.addEventListener('focus', onBuySide);
    sellBtn?.addEventListener('mouseenter', onSellSide);
    sellBtn?.addEventListener('focus', onSellSide);



    // initial compute if volume already set
    onVolume();

    return () => {
      slEl?.removeEventListener('input', onUserEdit);
      tpEl?.removeEventListener('input', onUserEdit);
      volEl?.removeEventListener('input', onVolume);
      symEl?.removeEventListener('change', onSymbol);
      buyBtn?.removeEventListener('mouseenter', onBuySide);
      buyBtn?.removeEventListener('focus', onBuySide);
      sellBtn?.removeEventListener('mouseenter', onSellSide);
      sellBtn?.removeEventListener('focus', onSellSide);

    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [risk, symbols]);

  // Wire pending order auto-fill (price/type/volume/symbol/settings)
  useEffect(() => {
    const priceEl = document.getElementById('pendingPrice') as HTMLInputElement | null;
    const typeEl = document.getElementById('pendingOrderType') as HTMLSelectElement | null;
    const volEl = document.getElementById('volume') as HTMLInputElement | null;
    const symEl = document.getElementById('sym') as HTMLSelectElement | null;

    const onPending = () => {
      setUserEditedLevels(false);
      const side = getPendingSide();
      lastSideRef.current = side;
      applyPendingAutoLevels(side);
    };

    const onVol = () => { onPending(); };
    const onSym = () => { onPending(); };

    priceEl?.addEventListener('input', onPending);
    typeEl?.addEventListener('change', onPending);
    volEl?.addEventListener('input', onVol);
    symEl?.addEventListener('change', onSym);

    // initial compute when settings or inputs change
    onPending();

    return () => {
      priceEl?.removeEventListener('input', onPending);
      typeEl?.removeEventListener('change', onPending);
      volEl?.removeEventListener('input', onVol);
      symEl?.removeEventListener('change', onSym);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [risk, symbols]);



  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState('market');
  const [analysisTab, setAnalysisTab] = useState('chart');
  const [activityTab, setActivityTab] = useState('deals');
  const [connectionStatus, setConnectionStatus] = useState(true);
  const [analysisControlsExpanded, setAnalysisControlsExpanded] = useState(true);



  // --- Integration: API wiring and polling ---
  useEffect(() => {
    let cancelled = false;

    const DEFAULT_SYMBOLS = ['EURUSD','GBPUSD','USDJPY','XAUUSD'];
    const mergeWithDefaults = (rows: Symbol[]): Symbol[] => {
      const seen = new Set<string>();
      const out: Symbol[] = [];
      // add loaded rows first
      for (const r of rows || []) {
        const key = (r.symbol || '').toUpperCase();
        if (!key || seen.has(key)) continue;
        seen.add(key);
        out.push(r);
      }
      // ensure key defaults exist at least as placeholders
      for (const s of DEFAULT_SYMBOLS) {
        const key = s.toUpperCase();
        if (seen.has(key)) continue;
        seen.add(key);
        out.push({ symbol: s, bid: 0, ask: 0, spread: 0, change: 0, changePercent: 0 });
      }
      return out;
    };

    async function loadAllSymbols() {
      let result: Symbol[] = [];
      try {
        const live = await getSymbols(true);
        result = live || [];
      } catch {
        // ignore, try fallback
      }
      if (!result || result.length === 0) {
        try {
          const fallback = await getSymbols(false);
          result = fallback || [];
        } catch { /* ignore */ }
      }
      if (!cancelled) setSymbols(mergeWithDefaults(result));

      try {
        const prio = await getPrioritySymbols(5);
        if (!cancelled) setPrioritySymbols(prio);
      } catch { /* ignore */ }
    }

    loadAllSymbols();
    return () => { cancelled = true; };
  }, []);

  // Populate symbol selects when symbols change
  useEffect(() => {
    const symSelect = document.getElementById('sym') as HTMLSelectElement | null;
    if (symSelect && symbols?.length) {
      const current = symSelect.value;
      symSelect.innerHTML = '<option value="">Select Symbol...</option>' +
        symbols.map(s => `<option value="${s.symbol}">${s.symbol}</option>`).join('');
      if (current) symSelect.value = current;
    }
  }, [symbols]);

  // Account polling
  useEffect(() => {
    let alive = true;
    const refresh = async () => {
      try {
        const a = await getAccount();
        if (!alive) return;
        setAccount(a);
        setConnectionStatus(true);
      } catch {
        if (!alive) return;
        setConnectionStatus(false);
      }
    };
    refresh();
    const iv = setInterval(refresh, (window.CONFIG?.REFRESH_INTERVAL || 5000));
    return () => { alive = false; clearInterval(iv); };
  }, []);

  // Positions polling
  useEffect(() => {
    let alive = true;
    const refresh = async () => {
      try {
        const p = await getPositions();
        if (!alive) return;
        setPositions(p as Position[]);
      } catch {
        // ignore
      }
    };
    refresh();
    const iv = setInterval(refresh, (window.CONFIG?.REFRESH_INTERVAL || 5000));
    return () => { alive = false; clearInterval(iv); };
  }, []);

  async function handleSendOrder(side: 'buy' | 'sell') {
    const out = document.getElementById('order-output');
    function setOut(msg: string) { if (out) out.textContent = msg; }

    try {
      const symEl = document.getElementById('sym') as HTMLSelectElement | null;
      const volEl = document.getElementById('volume') as HTMLInputElement | null;
      const devEl = document.getElementById('deviation') as HTMLInputElement | null;
      const slEl = document.getElementById('sl') as HTMLInputElement | null;
      const tpEl = document.getElementById('tp') as HTMLInputElement | null;

      const canonical = symEl?.value || '';
      const volume = parseFloat(volEl?.value || '0');
      const deviation = parseInt(devEl?.value || '10', 10);
      const sl = slEl?.value ? parseFloat(slEl.value) : null;
      const tp = tpEl?.value ? parseFloat(tpEl.value) : null;

      if (!canonical) { setOut('Select a symbol'); return; }
      if (!volume || volume <= 0) { setOut('Enter a valid volume'); return; }

      setOut(`Sending ${side.toUpperCase()} order for ${volume} ${canonical}...`);
      const res = await postOrder({ canonical, side, volume, deviation, sl, tp, comment: 'Tradecraft Console' });
      if (res && (res.result_code || 0) >= 10000) {
        setOut(`Order OK. Ticket: ${res.order ?? ''} Code: ${res.result_code}`);
      } else {
        setOut(`Order failed: ${res?.error?.message || JSON.stringify(res)}`);
      }
      // refresh account & positions after order
      try { const a = await getAccount(); setAccount(a); } catch (_err) { /* no-op */ }
      try { const p = await getPositions(); setPositions(p as Position[]); } catch (_err) { /* no-op */ }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setOut(`Order error: ${msg}`);
    }
  }

  // Close position handlers
  const handleClosePositionClick = (position: Position) => {
    setPositionToClose(position);
    setCloseDialogOpen(true);
  };

  const handleClosePositionConfirm = async () => {
    if (!positionToClose || !positionToClose.ticket) return;

    setClosingPosition(true);
    try {
      const res = await closePosition(positionToClose.ticket);

      if (res && (res.result_code || 0) >= 10000) {
        toast({
          title: "Position Closed",
          description: `Successfully closed position #${positionToClose.ticket} for ${positionToClose.symbol}`,
          variant: "default",
        });

        // Refresh positions and account
        try {
          const p = await getPositions();
          setPositions(p as Position[]);
        } catch (_err) { /* no-op */ }

        try {
          const a = await getAccount();
          setAccount(a);
        } catch (_err) { /* no-op */ }
      } else {
        toast({
          title: "Close Failed",
          description: res?.error?.message || `Failed to close position #${positionToClose.ticket}`,
          variant: "destructive",
        });
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({
        title: "Error",
        description: `Failed to close position: ${msg}`,
        variant: "destructive",
      });
    } finally {
      setClosingPosition(false);
      setCloseDialogOpen(false);
      setPositionToClose(null);
    }
  };

  const [prioritySymbols, setPrioritySymbols] = useState<Symbol[]>([]);

  // Populate additional selects for history/activity when symbols change
  useEffect(() => {
    if (!symbols || symbols.length === 0) return; // keep initial defaults until symbols are loaded
    const fill = (id: string) => {
      const sel = document.getElementById(id) as HTMLSelectElement | null;
      if (!sel) return;
      const current = sel.value;
      sel.innerHTML = '<option value="">All Symbols</option>' +
        symbols.map(s => `<option value="${s.symbol}">${s.symbol}</option>`).join('');
      if (current) sel.value = current;
    };
    fill('histSymbol');
    fill('historySymbolFilter');
    fill('pendingSymbol');
    fill('pendingSymbolIntegrated');
  }, [symbols]);

  async function handleLoadHistorical() {
    const symEl = document.getElementById('histSymbol') as HTMLSelectElement | null;
    const tfEl = document.getElementById('histTimeframe') as HTMLSelectElement | null;
    const fromEl = document.getElementById('histDateFrom') as HTMLInputElement | null;
    const toEl = document.getElementById('histDateTo') as HTMLInputElement | null;
    const countEl = document.getElementById('histCount') as HTMLInputElement | null;
    const tbody = document.querySelector('#historical-bars-table tbody') as HTMLTableSectionElement | null;

    const symbol = (symEl?.value || '').toUpperCase();
    const timeframe = tfEl?.value || 'M1';
    const date_from = fromEl?.value || '';
    const date_to = toEl?.value || '';
    const count = countEl?.value ? parseInt(countEl.value, 10) : undefined;

    if (!symbol) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center text-text-muted py-4">Select a symbol</td></tr>';
      return;
    }
    try {
      let bars = await getHistoricalBars({ symbol, timeframe, date_from, date_to, count });
      if (!tbody) return;
      // Fallback: if no results and no explicit date range, retry with last 48 hours
      if ((!bars || bars.length === 0) && !date_from && !date_to) {
        const now = new Date();
        const from = new Date(now.getTime() - 48 * 60 * 60 * 1000);
        const df = from.toISOString();
        const dt = now.toISOString();
        bars = await getHistoricalBars({ symbol, timeframe, date_from: df, date_to: dt });
      }
      // Client-side synthetic fallback for offline/demo: generate minimal rows if still empty
      if (!bars || bars.length === 0) {
        const tfMin: Record<string, number> = { M1: 1, M5: 5, M15: 15, M30: 30, H1: 60, H4: 240, D1: 1440 };
        const n = Math.min(Math.max(count || 60, 20), 120);
        const step = (tfMin[timeframe] || 1) * 60 * 1000;
        const end = Date.now();
        let t = end - n * step;
        let base = isJPY(symbol) ? 150 : 1.1000;
        const ps = pipSize(symbol);
        const out: any[] = [];
        for (let i = 0; i < n; i++) {
          const drift = Math.sin(i / 7) * 3 * ps;
          const noise = ((i % 5) - 2) * ps * 0.5;
          const open = base;
          const close = base + drift + noise;
          const high = Math.max(open, close) + ps * 2;
          const low = Math.min(open, close) - ps * 2;
          out.push({ time: Math.floor(t / 1000), open, high, low, close, tick_volume: 100 + (i % 20) });
          base = close;
          t += step;
        }
        bars = out;
      }

      if (!bars || bars.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-text-muted py-4">No data</td></tr>';
      } else {
        type Bar = { time?: string | number; open?: number; high?: number; low?: number; close?: number; tick_volume?: number; volume?: number };
        tbody.innerHTML = (bars as Bar[]).map((b) => `
          <tr>
            <td>${b.time ?? ''}</td>
            <td class="text-right">${Number(b.open ?? 0).toFixed(5)}</td>
            <td class="text-right">${Number(b.high ?? 0).toFixed(5)}</td>
            <td class="text-right">${Number(b.low ?? 0).toFixed(5)}</td>
            <td class="text-right">${Number(b.close ?? 0).toFixed(5)}</td>
            <td class="text-right">${Number(b.tick_volume ?? b.volume ?? 0)}</td>
          </tr>
        `).join('');
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (tbody) tbody.innerHTML = `<tr><td colspan=6 class=\"text-center text-negative py-4\">Error: ${msg}</td></tr>`;
    }
  }

  async function handleCreatePending() {
    const outEl = (document.getElementById('order-output') as HTMLElement | null) || (document.getElementById('pending-order-output') as HTMLElement | null);
    const typeEl = document.getElementById('pendingOrderType') as HTMLSelectElement | null;
    const symEl = (document.getElementById('sym') as HTMLSelectElement | null) || (document.getElementById('pendingSymbol') as HTMLSelectElement | null);
    const priceEl = document.getElementById('pendingPrice') as HTMLInputElement | null;
    const volEl = (document.getElementById('volume') as HTMLInputElement | null) || (document.getElementById('pendingVolume') as HTMLInputElement | null);
    const slEl = (document.getElementById('sl') as HTMLInputElement | null) || (document.getElementById('pendingSL') as HTMLInputElement | null);
    const tpEl = (document.getElementById('tp') as HTMLInputElement | null) || (document.getElementById('pendingTP') as HTMLInputElement | null);

    const map: Record<string, string> = {
      'Buy Limit': 'buy_limit',
      'Sell Limit': 'sell_limit',
      'Buy Stop': 'buy_stop',
      'Sell Stop': 'sell_stop',
    };

    const orderType = typeEl?.value || '';
    const canonical = symEl?.value || '';
    const price = priceEl?.value ? Number(priceEl.value) : NaN;
    const volume = volEl?.value ? Number(volEl.value) : NaN;
    const sl = slEl?.value ? Number(slEl.value) : undefined;
    const tp = tpEl?.value ? Number(tpEl.value) : undefined;

    if (!canonical || !orderType || Number.isNaN(price) || Number.isNaN(volume)) {
      if (outEl) outEl.textContent = 'Please fill symbol, type, price, and volume.';
      return;
    }

    const payload = {
      canonical,
      order_type: map[orderType] || orderType.toLowerCase().replace(' ', '_'),
      price,
      volume,
      sl,
      tp,
      deviation: 10,
      comment: 'PENDING_FROM_UI',
      magic: 0,
    };

    try {
      const res = await createPendingOrder(payload);
      if (outEl) outEl.textContent = `Pending order created: ${JSON.stringify(res)}`;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      // One-shot adaptive retry: widen distance to satisfy broker stop-levels
      if (String(msg).includes('HTTP 409') && typeEl?.value) {
        const ot = typeEl.value as string;
        const fudge = 0.0010; // ~10 pips
        let adj = price;
        if (ot === 'Buy Limit' || ot === 'Sell Stop') adj = +(price - fudge).toFixed(5);
        if (ot === 'Sell Limit' || ot === 'Buy Stop') adj = +(price + fudge).toFixed(5);
        try {
          const retryRes = await createPendingOrder({ ...payload, price: adj });
          if (outEl) outEl.textContent = `Pending order created (retry @ ${adj}): ${JSON.stringify(retryRes)}`;
          return;
        } catch (e2) {
          const m2 = e2 instanceof Error ? e2.message : String(e2);
          if (outEl) outEl.textContent = `Failed to create pending order after retry: ${m2}`;
        }
      } else {
        if (outEl) outEl.textContent = `Failed to create pending order: ${msg}`;
      }
    }
  }



  // Activity: deals/orders + summary
  useEffect(() => {
    const fromEl = document.getElementById('historyDateFrom') as HTMLInputElement | null;
    const toEl = document.getElementById('historyDateTo') as HTMLInputElement | null;
    const symFilter = document.getElementById('historySymbolFilter') as HTMLSelectElement | null;

    let alive = true;
    const refresh = async () => {
      if (!alive) return;
      const opts = {
        date_from: fromEl?.value || '',
        date_to: toEl?.value || '',
        symbol: symFilter?.value || '',
      };
      if (activityTab === 'deals') {
        const table = document.querySelector('#deals-table tbody') as HTMLTableSectionElement | null;
        try {
          if (!opts.date_from || !opts.date_to) {
            if (table) table.innerHTML = '<tr><td colspan="6" class="text-center text-text-muted py-4">Set From/To dates to load deals</td></tr>';
            return;
          }
          const deals = await getDeals(opts);
          if (!table) return;
          if (!deals || deals.length === 0) {
            table.innerHTML = '<tr><td colspan="6" class="text-center text-text-muted py-4">No deals found</td></tr>';
          } else {
            let totalDeals = 0, totalProfit = 0, commission = 0;
            type Deal = { time?: string | number; symbol?: string; type?: string; volume?: number; price?: number; profit?: number; commission?: number };
            table.innerHTML = (deals as Deal[]).map((d) => {
              totalDeals += 1;
              totalProfit += Number(d.profit ?? 0);
              commission += Number(d.commission ?? 0);
              return `
                <tr>
                  <td>${d.time ?? ''}</td>
                  <td>${d.symbol ?? ''}</td>
                  <td>${d.type ?? ''}</td>
                  <td class="text-right">${Number(d.volume ?? 0).toFixed(2)}</td>
                  <td class="text-right">${Number(d.price ?? 0).toFixed(5)}</td>
                  <td class="text-right ${Number(d.profit ?? 0) >= 0 ? 'value-positive' : 'value-negative'}">${Number(d.profit ?? 0).toFixed(2)}</td>
                </tr>`;
            }).join('');
            const net = totalProfit - commission;
            const td = document.getElementById('total-deals');
            const tp = document.getElementById('total-profit');
            const tc = document.getElementById('total-commission');
            const np = document.getElementById('net-profit');
            if (td) td.textContent = String(totalDeals);
            if (tp) { tp.textContent = `$${totalProfit.toFixed(2)}`; tp.className = `text-lg font-mono tabular-nums ${net>=0?'value-positive':'value-negative'}`; }
            if (tc) tc.textContent = `$${commission.toFixed(2)}`;
            if (np) { np.textContent = `$${net.toFixed(2)}`; np.className = `text-lg font-mono tabular-nums ${net>=0?'value-positive':'value-negative'}`; }
          }
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : String(e);
          if (table) table.innerHTML = `<tr><td colspan=6 class="text-center text-negative py-4">Error: ${msg}</td></tr>`;
        }
      }
      if (activityTab === 'orders') {
        const table = document.querySelector('#orders-history-table tbody') as HTMLTableSectionElement | null;
        const pendTbody = document.getElementById('pending-orders-tbody') as HTMLTableSectionElement | null;
        try {
          // Pending orders list (independent of order history filters)
          try {
            const pend = await getPendingOrders();
            if (pendTbody) {
              if (!pend || pend.length === 0) {
                pendTbody.innerHTML = '<tr><td colSpan="5" class="text-center text-text-muted py-4">No pending orders</td></tr>';
              } else {
                type PendingOrd = { ticket?: number | string; order?: number | string; symbol?: string; type?: string; volume?: number; price?: number };
                pendTbody.innerHTML = (pend as PendingOrd[]).map((p) => `
                  <tr>
                    <td>${p.symbol ?? ''}</td>
                    <td>${p.type ?? ''}</td>
                    <td class="text-right">${Number(p.volume ?? 0).toFixed(2)}</td>
                    <td class="text-right">${Number((p as any).price_open ?? (p as any).price ?? (p as any).price_current ?? 0).toFixed(5)}</td>
                    <td>
                      <div class="flex gap-2">
                        <button type=button class="btn-secondary btn-xs modify-pending-btn" data-ticket="${p.ticket ?? p.order ?? ''}">Modify</button>
                        <button type=button class="btn-secondary btn-xs cancel-pending-btn" data-ticket="${p.ticket ?? p.order ?? ''}">Cancel</button>
                      </div>
                    </td>
                  </tr>`).join('');
                // wire cancel buttons
                pendTbody.querySelectorAll('.cancel-pending-btn')
                  .forEach((btn) => btn.addEventListener('click', async (ev) => {
                    const t = (ev.currentTarget as HTMLButtonElement).getAttribute('data-ticket');
                    if (!t) return;
                    try { await cancelPendingOrder(t); } catch {}
                    refresh();
                  }));
                // wire modify buttons
                pendTbody.querySelectorAll('.modify-pending-btn')
                  .forEach((btn) => btn.addEventListener('click', async (ev) => {
                    const t = (ev.currentTarget as HTMLButtonElement).getAttribute('data-ticket');
                    if (!t) return;
                    const priceEl = document.getElementById('pendingPrice') as HTMLInputElement | null;
                    const slEl = (document.getElementById('sl') as HTMLInputElement | null) || (document.getElementById('pendingSL') as HTMLInputElement | null);
                    const tpEl = (document.getElementById('tp') as HTMLInputElement | null) || (document.getElementById('pendingTP') as HTMLInputElement | null);
                    const payload: any = {};
                    const p = priceEl?.value ? parseFloat(priceEl.value) : NaN;
                    const slv = slEl?.value ? parseFloat(slEl.value) : NaN;
                    const tpv = tpEl?.value ? parseFloat(tpEl.value) : NaN;
                    if (!Number.isNaN(p)) payload.price = p;
                    if (!Number.isNaN(slv)) payload.sl = slv;
                    if (!Number.isNaN(tpv)) payload.tp = tpv;
                    try { await modifyPendingOrder(t, payload); } catch {}
                    refresh();
                  }));
              }
            }
          } catch (_err) { /* no-op */ }

          if (!opts.date_from || !opts.date_to) {
            if (table) table.innerHTML = '<tr><td colspan="6" class="text-center text-text-muted py-4">Set From/To dates to load order history</td></tr>';
            return;
          }
          const orders = await getOrdersHistory(opts);
          if (table) {
            if (!orders || orders.length === 0) {
              table.innerHTML = '<tr><td colspan="6" class="text-center text-text-muted py-4">No order history</td></tr>';
            } else {
              type OrderHist = { time?: string | number; symbol?: string; type?: string; volume?: number; price?: number; state?: string; status?: string };
              table.innerHTML = (orders as OrderHist[]).map((o) => `
                <tr>
                  <td>${o.time ?? ''}</td>
                  <td>${o.symbol ?? ''}</td>
                  <td>${o.type ?? ''}</td>
                  <td class="text-right">${Number(o.volume ?? 0).toFixed(2)}</td>
                  <td class="text-right">${Number((o as any).price_open ?? (o as any).price ?? (o as any).price_current ?? 0).toFixed(5)}</td>
                  <td>${o.state ?? o.status ?? ''}</td>
                </tr>`).join('');
            }
          }
          // Pending orders list
          try {
            const pend = await getPendingOrders();
            if (pendTbody) {
              if (!pend || pend.length === 0) {
                pendTbody.innerHTML = '<tr><td colSpan="5" class="text-center text-text-muted py-4">No pending orders</td></tr>';
              } else {
                type PendingOrd = { ticket?: number | string; order?: number | string; symbol?: string; type?: string; volume?: number; price?: number };
                pendTbody.innerHTML = (pend as PendingOrd[]).map((p) => `
                  <tr>
                    <td>${p.symbol ?? ''}</td>
                    <td>${p.type ?? ''}</td>
                    <td class="text-right">${Number(p.volume ?? 0).toFixed(2)}</td>
                    <td class="text-right">${Number((p as any).price_open ?? (p as any).price ?? (p as any).price_current ?? 0).toFixed(5)}</td>
                    <td>
                      <div class="flex gap-2">
                        <button type=button class="btn-secondary btn-xs modify-pending-btn" data-ticket="${p.ticket ?? p.order ?? ''}">Modify</button>
                        <button type=button class="btn-secondary btn-xs cancel-pending-btn" data-ticket="${p.ticket ?? p.order ?? ''}">Cancel</button>
                      </div>
                    </td>
                  </tr>`).join('');
                // wire cancel buttons
                pendTbody.querySelectorAll('.cancel-pending-btn')
                  .forEach((btn) => btn.addEventListener('click', async (ev) => {
                    const t = (ev.currentTarget as HTMLButtonElement).getAttribute('data-ticket');
                    if (!t) return;
                    try { await cancelPendingOrder(t); } catch {}
                    refresh();
                  }));
                // wire modify buttons
                pendTbody.querySelectorAll('.modify-pending-btn')
                  .forEach((btn) => btn.addEventListener('click', async (ev) => {
                    const t = (ev.currentTarget as HTMLButtonElement).getAttribute('data-ticket');
                    if (!t) return;
                    const priceEl = document.getElementById('pendingPrice') as HTMLInputElement | null;
                    const slEl = (document.getElementById('sl') as HTMLInputElement | null) || (document.getElementById('pendingSL') as HTMLInputElement | null);
                    const tpEl = (document.getElementById('tp') as HTMLInputElement | null) || (document.getElementById('pendingTP') as HTMLInputElement | null);
                    const payload: any = {};
                    const p = priceEl?.value ? parseFloat(priceEl.value) : NaN;
                    const slv = slEl?.value ? parseFloat(slEl.value) : NaN;
                    const tpv = tpEl?.value ? parseFloat(tpEl.value) : NaN;
                    if (!Number.isNaN(p)) payload.price = p;
                    if (!Number.isNaN(slv)) payload.sl = slv;
                    if (!Number.isNaN(tpv)) payload.tp = tpv;
                    try { await modifyPendingOrder(t, payload); } catch {}
                    refresh();
                  }));
              }
            }
          } catch (_err) { /* no-op */ }
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : String(e);
          if (table) table.innerHTML = `<tr><td colspan=6 class="text-center text-negative py-4">Error: ${msg}</td></tr>`;
        }
      }
    };

    // initial load when tab shown
    refresh();

    const onChange = () => refresh();
    fromEl?.addEventListener('change', onChange);
    toEl?.addEventListener('change', onChange);
    symFilter?.addEventListener('change', onChange);
    return () => {
      alive = false;
      fromEl?.removeEventListener('change', onChange);
      toEl?.removeEventListener('change', onChange);
      symFilter?.removeEventListener('change', onChange);
    };
  }, [activityTab]);

  // Connection status monitoring
  useEffect(() => {
    const checkConnection = () => {
      fetch(`${window.CONFIG?.API_BASE || 'http://127.0.0.1:5001'}/api/account`, {
        headers: window.getAuthHeaders?.() || {},
        signal: AbortSignal.timeout(window.CONFIG?.CONNECTION_TIMEOUT || 10000)
      })
        .then(() => setConnectionStatus(true))
        .catch(() => setConnectionStatus(false));
    };

    checkConnection();
    const interval = setInterval(checkConnection, window.CONFIG?.REFRESH_INTERVAL || 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const formatCurrency = (value: number, decimals = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <ErrorBoundary>
    <div className="min-h-screen bg-background text-text-primary">
      {/* Header */}
      <header className="h-header bg-panel border-b border-border flex items-center justify-between px-4 relative z-50">
        <div className="flex items-center gap-4">
          <button type="button"
            onClick={toggleSidebar}
            className="p-2 hover:bg-secondary rounded-md transition-colors"
            aria-label="Toggle sidebar"
          >
            <Menu className="w-4 h-4" />
          </button>
          <h1 className="text-lg font-semibold text-text-primary">Trade Agent MT5</h1>
        </div>

        {/* Account Info Header */}
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-1">
            <span className="text-text-secondary">Balance:</span>
            <span id="header-balance" className="font-mono tabular-nums font-medium">
              ${formatCurrency(account?.balance || 0)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-text-secondary">Equity:</span>
            <span id="header-equity" className="font-mono tabular-nums font-medium">
              ${formatCurrency(account?.equity || 0)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-text-secondary">Margin:</span>
            <span id="header-margin" className="font-mono tabular-nums font-medium">
              ${formatCurrency(account?.margin || 0)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-text-secondary">Free:</span>
            <span id="header-free-margin" className="font-mono tabular-nums font-medium">
              ${formatCurrency(account?.freeMargin || 0)}
            </span>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div
              id="connection-status"
              className={`w-2 h-2 rounded-full ${connectionStatus ? 'bg-status-online' : 'bg-status-offline'}`}
            />
            <span id="connection-text" className={connectionStatus ? 'status-online' : 'status-offline'}>
              {connectionStatus ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-3.5rem)]">
        {/* Sidebar */}
        <aside
          className={`bg-sidebar border-r border-sidebar-border transition-all duration-300 ${
            sidebarCollapsed ? 'w-sidebar-collapsed' : 'w-sidebar'
          } flex flex-col`}
        >
          {/* Navigation */}
          <nav className="p-3">
            <div className="space-y-1">
              <button type="button" className="w-full flex items-center gap-3 px-3 py-2 rounded-md bg-sidebar-item-active text-primary text-sm font-medium">
                <TrendingUp className="w-4 h-4" />
                {!sidebarCollapsed && 'Dashboard'}
              </button>
              <button id="nav-analysis" type="button" onClick={() => navigate('/analysis')} className="w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-sidebar-item-hover text-text-secondary text-sm">
                <BarChart3 className="w-4 h-4" />
                {!sidebarCollapsed && 'Analysis'}
              </button>
              <button id="nav-settings" type="button" onClick={() => navigate('/settings')} className="w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-sidebar-item-hover text-text-secondary text-sm">
                <Settings className="w-4 h-4" />
                {!sidebarCollapsed && 'Settings'}
              </button>
            </div>
          </nav>

          {/* AI Status Indicator */}
          {!sidebarCollapsed && <AIStatusIndicator />}

          {/* Priority Symbols */}
          {!sidebarCollapsed && (
            <div className="flex-1 p-3">
              <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-3">Priority Symbols</h3>
              <div id="priority-symbols-list" className="space-y-1">
                {prioritySymbols.slice(0, 8).map((symbol) => (
                  <div key={symbol.symbol} className="flex items-center justify-between p-2 rounded hover:bg-sidebar-item-hover text-xs">
                    <span className="font-medium">{symbol.symbol}</span>
                    <div className="text-right">
                      <div className="font-mono tabular-nums">{formatCurrency(symbol.bid, 5)}</div>
                      <div className={`font-mono tabular-nums ${Number(symbol.change ?? 0) >= 0 ? 'value-positive' : 'value-negative'}`}>
                        {formatPercent(symbol.changePercent ?? 0)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>


            </div>
          )}




          {/* Mini Market Watch for collapsed state */}
          {sidebarCollapsed && (
            <div id="sidebar-mini-watch-list" className="flex-1 p-2">
              <div className="space-y-2">
                {prioritySymbols.slice(0, 4).map((symbol) => (
                  <div key={symbol.symbol} className="text-center">
                    <div className="text-xs font-medium truncate">{symbol.symbol}</div>
                    <div className={`text-xs font-mono tabular-nums ${Number(symbol.change ?? 0) >= 0 ? 'value-positive' : 'value-negative'}`}>
                      {Number(symbol.change ?? 0) >= 0 ? '+' : ''}{Number(symbol.changePercent ?? 0).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Order Entry Section */}
          <div className="border-b border-border bg-panel">
            <div className="p-4">
              {/* Order Type Tabs */}
              <div className="flex gap-1 mb-4">
                <button type="button"
                  onClick={() => setActiveTab('market')}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    activeTab === 'market'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary-hover'
                  }`}
                >
                  Market Order
                </button>
                <button type="button"
                  onClick={() => setActiveTab('pending')}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    activeTab === 'pending'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary-hover'
                  }`}
                >
                  Pending Order
                </button>
              </div>

              {/* Order Entry Form */}
              <div className="grid grid-cols-12 gap-4 items-end">
                <div className="col-span-2">
                  <label htmlFor="sym" className="block text-xs font-medium text-text-secondary mb-1">Symbol</label>
                  <select id="sym" className="trading-input w-full">
                    <option>EURUSD</option>
                    <option>GBPUSD</option>
                    <option>USDJPY</option>
                    <option>AUDUSD</option>
                  </select>
                </div>

                <div className="col-span-1">
                  <label htmlFor="volume" className="block text-xs font-medium text-text-secondary mb-1">Volume (lots)</label>
                  <input
                    type="number"
                    id="volume"
                    className="trading-input w-full"
                    placeholder="0.01"
                    step="0.01"
                    min="0.01"
                  />
                </div>

                <div className="col-span-1">
                  <label htmlFor="deviation" className="block text-xs font-medium text-text-secondary mb-1">Deviation (pips)</label>
                  <input
                    type="number"
                    id="deviation"
                    className="trading-input w-full"
                    placeholder="10"
                    min="0"
                  />
                </div>

                <div className="col-span-1">
                  <label htmlFor="sl" className="block text-xs font-medium text-text-secondary mb-1">Stop Loss</label>
                  <input
                    type="number"
                    id="sl"
                    className="trading-input w-full"
                    placeholder="0.0000"
                    step="0.0001"
                  />
                </div>

                <div className="col-span-1">
                  <label htmlFor="tp" className="block text-xs font-medium text-text-secondary mb-1">Take Profit</label>
                  <input
                    type="number"
                    id="tp"
                    className="trading-input w-full"
                    placeholder="0.0000"
                    step="0.0001"
                  />
                </div>


                <div className="col-span-4">
                  <p className="text-xs text-text-muted">
                    Auto-fill uses your Risk strategy and R/R; values can be overridden. AI suggestions (placeholder) will appear here.
                  </p>
                </div>

                {activeTab === 'pending' && (
                  <>




                    <div className="col-span-2">

                      <label htmlFor="pendingOrderType" className="block text-xs font-medium text-text-secondary mb-1">Order Type</label>
                      <select id="pendingOrderType" className="trading-input w-full" aria-label="Pending order type" title="Pending order type">
                        <option>Buy Limit</option>
                        <option>Sell Limit</option>
                        <option>Buy Stop</option>
                        <option>Sell Stop</option>
                      </select>
                    </div>
                    <div className="col-span-2">
                      <label htmlFor="pendingPrice" className="block text-xs font-medium text-text-secondary mb-1">Price</label>
                      <input type="number" id="pendingPrice" className="trading-input w-full" step="0.0001" placeholder="0.0000" aria-label="Pending order price" title="Pending order price" />
                    </div>
                  </>
                )}

                {activeTab === 'market' ? (
                  <div className="col-span-3 flex gap-2">
                    <button id="buy-btn" type="button" onClick={() => handleSendOrder('buy')} className="btn-trading-success flex-1 flex items-center justify-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      BUY
                    </button>
                    <button id="sell-btn" type="button" onClick={() => handleSendOrder('sell')} className="btn-trading-danger flex-1 flex items-center justify-center gap-2">
                      <TrendingDown className="w-4 h-4" />
                      SELL
                    </button>
                  </div>
                ) : (
                  <div className="col-span-3">
                    <button id="place-pending-btn" type="button" onClick={handleCreatePending} className="btn-secondary w-full flex items-center justify-center gap-2">
                      <Clock className="w-4 h-4" /> Place Pending
                    </button>
                  </div>
                )}


                <div className="col-span-3">
                  <div id="order-output" className="text-xs text-text-secondary min-h-[20px]">
                    Ready to trade
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Market Analysis & Positions Layout */}
          <div className="flex-1 flex overflow-hidden">
            {/* Market Analysis - Center */}
            <div className="flex-1 flex flex-col border-r border-border">
              {/* Analysis Tabs */}
              <div className="border-b border-border bg-panel px-4 py-2">
                <div className="flex items-center justify-between">
                  <div className="flex gap-1">
                    <button type="button"
                      onClick={() => setAnalysisTab('chart')}
                      className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                        analysisTab === 'chart'
                          ? 'bg-primary text-primary-foreground'
                          : 'text-text-secondary hover:text-text-primary hover:bg-secondary'
                      }`}
                    >
                      Chart
                    </button>
                    <button type="button"
                      onClick={() => setAnalysisTab('bars')}
                      className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                        analysisTab === 'bars'
                          ? 'bg-primary text-primary-foreground'
                          : 'text-text-secondary hover:text-text-primary hover:bg-secondary'
                      }`}
                    >
                      Bars
                    </button>
                    <button type="button"
                      onClick={() => setAnalysisTab('ticks')}
                      className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                        analysisTab === 'ticks'
                          ? 'bg-primary text-primary-foreground'
                          : 'text-text-secondary hover:text-text-primary hover:bg-secondary'
                      }`}
                    >
                      Ticks
                    </button>
                    <button type="button"
                      onClick={() => setAnalysisTab('stats')}
                      className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                        analysisTab === 'stats'
                          ? 'bg-primary text-primary-foreground'
                          : 'text-text-secondary hover:text-text-primary hover:bg-secondary'
                      }`}
                    >
                      Stats
                    </button>
                  </div>


                  <button type="button"
                    onClick={() => setAnalysisControlsExpanded(!analysisControlsExpanded)}
                    className="p-1.5 hover:bg-secondary rounded transition-colors"
                    aria-label="Toggle analysis controls"
                  >
                    <Settings id="controls-toggle-icon" className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Analysis Controls Panel */}
              {analysisControlsExpanded && (
                <div id="analysis-controls-panel" className="border-b border-border bg-panel p-4">
                  <div className="grid grid-cols-6 gap-4 items-end">
                    <div>
                      <label htmlFor="histSymbol" className="block text-xs font-medium text-text-secondary mb-1">Symbol</label>
                      <select id="histSymbol" className="trading-input w-full">
                        <option>EURUSD</option>
                        <option>GBPUSD</option>
                        <option>USDJPY</option>
                      </select>
                    </div>
                    <div>
                      <label htmlFor="histTimeframe" className="block text-xs font-medium text-text-secondary mb-1">Timeframe</label>
                      <select id="histTimeframe" className="trading-input w-full">
                        <option>M1</option>
                        <option>M5</option>
                        <option>M15</option>
                        <option>H1</option>
                        <option>H4</option>
                        <option>D1</option>
                      </select>
                    </div>
                    <div>
                      <label htmlFor="histDateFrom" className="block text-xs font-medium text-text-secondary mb-1">From Date</label>
                      <input type="date" id="histDateFrom" className="trading-input w-full" />
                    </div>
                    <div>
                      <label htmlFor="histDateTo" className="block text-xs font-medium text-text-secondary mb-1">To Date</label>
                      <input type="date" id="histDateTo" className="trading-input w-full" />
                    </div>
                    <div>
                      <label htmlFor="histCount" className="block text-xs font-medium text-text-secondary mb-1">Count</label>
                      <input type="number" id="histCount" className="trading-input w-full" placeholder="100" />
                    </div>
                    <div>
                      <button type="button" onClick={handleLoadHistorical} className="btn-secondary w-full">Load Data</button>
                    </div>
                  </div>
                </div>
              )}



              {/* Analysis Content */}
              <div className="flex-1 p-4 overflow-auto">
                {analysisTab === 'chart' && (
                  <div className="h-full bg-card rounded-lg border border-border flex items-center justify-center">
                    <div className="text-center text-text-muted">
                      <LineChart className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Chart view will be rendered here</p>
                    </div>
                  </div>
                )}

                {analysisTab === 'bars' && (
                  <div className="h-full">
                    <div className="trading-panel h-full">
                      <div className="trading-header">
                        <h3 className="font-medium">Historical Bars</h3>
                      </div>
                      <div className="trading-content">
                        <div className="overflow-auto">
                          <table id="historical-bars-table" className="trading-table">
                            <thead>
                              <tr>
                                <th>Time</th>
                                <th>Open</th>
                                <th>High</th>
                                <th>Low</th>
                                <th>Close</th>
                                <th>Volume</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr>
                                <td colSpan={6} className="text-center text-text-muted py-8">
                                  No data available. Use controls above to load historical bars.
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {analysisTab === 'ticks' && (
                  <div className="h-full bg-card rounded-lg border border-border flex items-center justify-center">
                    <div className="text-center text-text-muted">
                      <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Tick data will be displayed here</p>
                    </div>
                  </div>
                )}

                {analysisTab === 'stats' && (
                  <div className="h-full bg-card rounded-lg border border-border flex items-center justify-center">
                    <div className="text-center text-text-muted">
                      <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>Statistics will be shown here</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Positions & Activity - Right Panel */}
            <div className="w-96 flex flex-col bg-panel">
              {/* Positions Section */}
              <div className="border-b border-border">
                <div className="px-4 py-3 border-b border-border">
                  <h3 className="font-medium text-text-primary">Open Positions</h3>
                </div>
                <div className="p-4 max-h-64 overflow-auto">
                  <table className="trading-table w-full text-xs">
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Type</th>
                        <th>Volume</th>
                        <th>P/L</th>
                        <th className="w-8"><span className="sr-only">Actions</span></th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="text-center text-text-muted py-4">
                            No open positions
                          </td>
                        </tr>
                      ) : (
                        positions.map((pos) => (
                          <tr key={pos.ticket || Math.random()}>
                            <td>{pos.symbol ?? ''}</td>
                            <td>{pos.type ?? ''}</td>
                            <td className="text-right">{Number(pos.volume || 0).toFixed(2)}</td>
                            <td className={`text-right ${Number(pos.profit || 0) >= 0 ? 'value-positive' : 'value-negative'}`}>
                              {Number(pos.profit || 0).toFixed(2)}
                            </td>
                            <td className="text-center">
                              <button
                                type="button"
                                onClick={() => handleClosePositionClick(pos)}
                                className="p-1 hover:bg-destructive/10 rounded transition-colors text-text-muted hover:text-destructive"
                                title="Close position"
                                aria-label={`Close position ${pos.ticket}`}
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Activity Section */}
              <div className="flex-1 flex flex-col">
                <div className="px-4 py-3 border-b border-border">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-text-primary">Activity</h3>
                    <div className="flex gap-1">
                      <button type="button"
                        onClick={() => setActivityTab('deals')}
                        className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                          activityTab === 'deals'
                            ? 'bg-primary text-primary-foreground'
                            : 'text-text-secondary hover:text-text-primary'
                        }`}
                      >
                        Deals
                      </button>
                      <button type="button"
                        onClick={() => setActivityTab('orders')}
                        className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                          activityTab === 'orders'
                            ? 'bg-primary text-primary-foreground'
                            : 'text-text-secondary hover:text-text-primary'
                        }`}
                      >
                        Orders
                      </button>
                      <button type="button"
                        onClick={() => setActivityTab('summary')}
                        className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                          activityTab === 'summary'
                            ? 'bg-primary text-primary-foreground'
                            : 'text-text-secondary hover:text-text-primary'
                        }`}
                      >
                        Summary
                      </button>
                    </div>
                  </div>
                </div>

                {/* Activity Filters */}
                <div className="px-4 py-2 border-b border-border bg-panel-alt">
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="date"
                      id="historyDateFrom"
                      className="trading-input text-xs"
                      placeholder="From"
                      aria-label="From date"
                      title="From date"
                    />
                    <input
                      type="date"
                      id="historyDateTo"
                      className="trading-input text-xs"
                      placeholder="To"
                      aria-label="To date"
                      title="To date"
                    />
                  </div>
                  <div className="mt-2">
                    <label htmlFor="historySymbolFilter" className="block text-xs font-medium text-text-secondary mb-1">Symbol filter</label>
                    <select id="historySymbolFilter" className="trading-input w-full text-xs" aria-label="Symbol filter" title="Symbol filter">
                      <option value="">All Symbols</option>
                      <option>EURUSD</option>
                      <option>GBPUSD</option>
                      <option>USDJPY</option>
                    </select>
                  </div>
                </div>

                {/* Activity Content */}
                <div className="flex-1 overflow-auto p-4">
                  {activityTab === 'deals' && (
                    <table id="deals-table" className="trading-table w-full text-xs">
                      <thead>
                        <tr>
                          <th>Time</th>
                          <th>Symbol</th>
                          <th>Type</th>
                          <th>Volume</th>
                          <th>Price</th>
                          <th>Profit</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td colSpan={6} className="text-center text-text-muted py-4">
                            No deals found
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  )}

                  {activityTab === 'orders' && (
                    <div>
                      <table id="orders-history-table" className="trading-table w-full text-xs">
                        <thead>
                          <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Type</th>
                            <th>Volume</th>
                            <th>Price</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td colSpan={6} className="text-center text-text-muted py-4">
                              No order history
                            </td>
                          </tr>
                        </tbody>
                      </table>

                      {/* Pending Orders Table */}
                      <div className="mt-4">
                        <h4 className="text-xs font-medium text-text-secondary mb-2">Pending Orders</h4>
                        <table className="trading-table w-full text-xs">
                          <thead>
                            <tr>
                              <th>Symbol</th>
                              <th>Type</th>
                              <th>Volume</th>
                              <th>Price</th>
                              <th>Action</th>
                            </tr>
                          </thead>
                          <tbody id="pending-orders-tbody">
                            <tr>
                              <td colSpan={5} className="text-center text-text-muted py-4">
                                No pending orders
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {activityTab === 'summary' && (
                    <div id="history-summary" className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div className="bg-card p-3 rounded border border-border">
                          <div className="text-text-secondary">Total Deals</div>
                          <div id="total-deals" className="text-lg font-mono tabular-nums">0</div>
                        </div>
                        <div className="bg-card p-3 rounded border border-border">
                          <div className="text-text-secondary">Total Profit</div>
                          <div id="total-profit" className="text-lg font-mono tabular-nums value-neutral">$0.00</div>
                        </div>
                        <div className="bg-card p-3 rounded border border-border">
                          <div className="text-text-secondary">Commission</div>
                          <div id="total-commission" className="text-lg font-mono tabular-nums">$0.00</div>
                        </div>
                        <div className="bg-card p-3 rounded border border-border">
                          <div className="text-text-secondary">Net Profit</div>
                          <div id="net-profit" className="text-lg font-mono tabular-nums value-neutral">$0.00</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Close Position Confirmation Dialog */}
      <AlertDialog open={closeDialogOpen} onOpenChange={setCloseDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Close Position</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to close position #{positionToClose?.ticket} for {positionToClose?.symbol}?
              {positionToClose?.profit !== undefined && (
                <div className="mt-2 text-sm">
                  <span className="font-medium">Current P/L: </span>
                  <span className={Number(positionToClose.profit) >= 0 ? 'text-green-500' : 'text-red-500'}>
                    ${Number(positionToClose.profit).toFixed(2)}
                  </span>
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={closingPosition}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleClosePositionConfirm}
              disabled={closingPosition}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {closingPosition ? 'Closing...' : 'Close Position'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

    </div>
    </ErrorBoundary>
  );
};

export default TradingDashboard;