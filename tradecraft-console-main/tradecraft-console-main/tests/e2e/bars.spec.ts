import { test, expect } from '@playwright/test';

test.describe('Historical Bars with fallback', () => {
  test('EURUSD H1 loads bars via count or 48h fallback', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Bars' }).click();

    // Select EURUSD & H1
    await page.locator('#histSymbol').selectOption({ label: 'EURUSD' });
    await page.locator('#histTimeframe').selectOption({ label: 'H1' });
    await page.locator('#histCount').fill('100');

    // Trigger load
    await page.getByRole('button', { name: 'Load Data' }).click();

    const table = page.locator('#historical-bars-table');
    await expect(table).toBeVisible();

    // Expect rows to appear (fallback will kick in if count returns 0)
    const rows = table.locator('tbody tr');
    await expect(rows.first()).toBeVisible({ timeout: 15000 });

    // Ensure not the placeholder row
    await expect(rows.first().locator('td')).toHaveCount(6);
  });
});

