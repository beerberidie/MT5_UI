import { test, expect } from '@playwright/test';

// Network failure and invalid input handling

test.describe('Error handling', () => {
  test('network failure on bars shows error then recovers', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Bars' }).click();

    await page.locator('#histSymbol').selectOption({ label: 'EURUSD' });
    await page.locator('#histTimeframe').selectOption({ label: 'H1' });
    await page.locator('#histCount').fill('50');

    // Fail first call
    await page.route('**/api/history/bars**', route => route.abort());
    await page.getByRole('button', { name: 'Load Data' }).click();
    const table = page.locator('#historical-bars-table');
    await expect(table.locator('tbody td')).toContainText(/Error:/, { timeout: 10000 });

    // Unroute and try again
    await page.unroute('**/api/history/bars**');
    await page.getByRole('button', { name: 'Load Data' }).click();
    const rows = table.locator('tbody tr');
    await expect(rows.first()).toBeVisible();
  });

  test('invalid pending inputs prompt validation message', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Pending Order' }).click();

    // Ensure volume and price empty
    await page.locator('#volume').fill('');
    await page.locator('#pendingPrice').fill('');

    await page.locator('#place-pending-btn').click();

    const out = page.locator('#order-output, #pending-order-output');
    await expect(out).toContainText(/Please fill symbol, type, price, and volume\./);
  });
});

