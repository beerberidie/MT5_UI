import { test, expect } from '@playwright/test';

test.describe('UI Navigation and Core Controls', () => {
  test('tabs and controls are interactive', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('Analysis')).toBeVisible();
    await expect(page.getByText('Settings')).toBeVisible();
    await expect(page.getByRole('button', { name: 'AI' })).toBeVisible();

    // AI should navigate to dedicated page
    await page.locator('#nav-ai').click();
    await expect(page.getByRole('heading', { name: 'AI', level: 1 })).toBeVisible();

    // Go back to root
    await page.goto('/');

    // Trading tab defaults
    await expect(page.locator('#sym')).toBeVisible();
    await expect(page.locator('#volume')).toBeVisible();

    // Switch order entry tabs
    await page.getByRole('button', { name: 'Pending Order' }).click();
    await expect(page.locator('#pendingOrderType')).toBeVisible();
    await page.getByRole('button', { name: 'Market Order' }).click();
    await expect(page.locator('#buy-btn')).toBeVisible();
    await expect(page.locator('#sell-btn')).toBeVisible();

    // Analysis panel -> switch to Bars tab
    await page.getByRole('button', { name: 'Bars' }).click();
    await expect(page.locator('#histSymbol')).toBeVisible();
    await expect(page.locator('#histTimeframe')).toBeVisible();
    await expect(page.locator('#historical-bars-table')).toBeVisible();

    // Activity panel -> switch to Orders view
    await page.getByRole('button', { name: 'Orders' }).click();
    await expect(page.locator('#orders-history-table')).toBeVisible();
    await expect(page.locator('#pending-orders-tbody')).toBeVisible();
  });
});

