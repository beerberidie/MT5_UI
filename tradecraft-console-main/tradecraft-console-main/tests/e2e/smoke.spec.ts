import { test, expect } from '@playwright/test';

test.describe('Tradecraft UI smoke', () => {
  test('loads without console errors and shows core controls', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() !== 'error') return;
      const text = `[${msg.location().url}:${msg.location().lineNumber}] ${msg.text()}`;
      // Ignore known benign external font CORS noise in CI
      if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
      errors.push(text);
    });

    await page.goto('/');

    // Header and key sections render
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Open Positions' })).toBeVisible();
    await expect(page.getByText('Activity')).toBeVisible();

    // Symbol select exists with some options
    const sym = page.locator('#sym');
    await expect(sym).toBeVisible();
    const optCount = await sym.locator('option').count();
    expect(optCount).toBeGreaterThan(0);

    // Basic trade buttons present (non-destructive: we do not click them here)
    await expect(page.getByRole('button', { name: 'BUY' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'SELL' })).toBeVisible();

    // Switch to Analysis -> Bars and ensure the historical table placeholder exists
    await page.getByRole('button', { name: 'Bars' }).click();
    const barsTable = page.locator('#historical-bars-table');
    await expect(barsTable).toBeVisible();

    // Ensure no console errors captured during basic navigation
    expect(errors, errors.join('\n')).toHaveLength(0);
  });
});

