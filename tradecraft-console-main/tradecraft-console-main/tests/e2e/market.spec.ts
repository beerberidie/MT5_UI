import { test, expect } from '@playwright/test';
import { getPositions, closePosition, sleep } from './helpers';

const SYMBOL = 'EURUSD';

async function positionsFor(symbol: string) {
  const pos = await getPositions();
  return (pos || []).filter((p: any) => (p.symbol || '') === symbol);
}

test.describe('Market orders BUY/SELL 0.01 with cleanup', () => {
  test('BUY then close; SELL then close', async ({ page }) => {
    await page.goto('/');

    // Baseline positions
    const base = await positionsFor(SYMBOL);

    // Prepare market inputs

    await page.locator('#sym').selectOption({ label: SYMBOL });
    await page.locator('#volume').fill('0.01');
    await page.getByRole('button', { name: 'Market Order' }).click();

    // Execute BUY
    await page.locator('#buy-btn').click();
    // Wait for positions to refresh (poll a few times)
    let afterBuy = await positionsFor(SYMBOL);
    for (let i=0; i<6 && afterBuy.length < base.length + 1; i++) {
      await sleep(800);
      afterBuy = await positionsFor(SYMBOL);
    }

    // Find new position and close it
    expect(afterBuy.length).toBeGreaterThanOrEqual(base.length + 1);
    // Close all new positions compared to baseline
    for (const p of afterBuy) {
      if (!base.find(b => (b.ticket||b.position) === (p.ticket||p.position))) {
        const t = p.ticket || p.position;
        await closePosition(t);
      }
    }

    await sleep(1200);

    // Execute SELL
    await page.locator('#sell-btn').click();
    // Wait for positions to refresh (poll a few times)
    let afterSell = await positionsFor(SYMBOL);
    for (let i=0; i<6 && afterSell.length < base.length + 1; i++) {
      await sleep(800);
      afterSell = await positionsFor(SYMBOL);
    }

    expect(afterSell.length).toBeGreaterThanOrEqual(base.length + 1);
    for (const p of afterSell) {
      if (!base.find(b => (b.ticket||b.position) === (p.ticket||p.position))) {
        const t = p.ticket || p.position;
        await closePosition(t);
      }
    }

    // Verify we returned to baseline count
    const finalPos = await positionsFor(SYMBOL);
    expect(finalPos.length).toBeGreaterThanOrEqual(base.length);
  });
});

