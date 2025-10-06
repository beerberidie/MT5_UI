export const API_BASE = process.env.API_BASE || 'http://127.0.0.1:5001';
export const API_KEY = process.env.AUGMENT_API_KEY || 'AC135782469AD';

export async function api(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers || {});
  headers.set('X-API-Key', API_KEY);
  if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const doFetch = async () => fetch(`${API_BASE}${path}`, { ...init, headers });
  let res = await doFetch();
  let retries = 5;
  let delay = 500;
  while ((res.status === 429 || res.status === 503) && retries-- > 0) {
    const ra = parseInt(res.headers.get('retry-after') || '0', 10);
    const waitMs = ra > 0 ? ra * 1000 : delay;
    await new Promise(r => setTimeout(r, waitMs));
    delay = Math.min(delay * 2, 4000);
    res = await doFetch();
  }
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  const text = await res.text();
  try { return JSON.parse(text); } catch { return text; }
}

export async function getTick(symbol: string): Promise<{ bid?: number; ask?: number; last?: number }> {
  return api(`/api/symbols/${encodeURIComponent(symbol)}/tick`);
}

export async function getPositions(): Promise<any[]> {
  return api('/api/positions');
}

export async function closePosition(ticket: number | string) {
  return api(`/api/positions/${ticket}/close`, { method: 'POST', body: JSON.stringify({}) });
}

export async function getPending(): Promise<any[]> {
  return api('/api/orders');
}

export async function cancelPending(ticket: number | string) {
  try {
    return await api(`/api/orders/${ticket}`, { method: 'DELETE', body: JSON.stringify({}) });
  } catch (e) {
    // swallow for idempotency in tests
    return null;
  }
}

export function sleep(ms: number) { return new Promise(res => setTimeout(res, ms)); }

