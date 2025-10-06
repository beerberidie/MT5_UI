import { test, expect } from '@playwright/test';

// Basic persistence test for Settings (Risk Management)
test.describe('Settings: Risk Management persistence', () => {
  test('save and reload persists risk settings', async ({ page }) => {
    // Load SPA root and navigate via UI to ensure client routing works under static server
    await page.goto('/');
    const navSettings = page.locator('#nav-settings');
    await navSettings.click();

    // Inputs
    const maxRisk = page.locator('#risk-max');
    const defRisk = page.locator('#risk-default');
    const rr = page.locator('#risk-rr');
    const strategy = page.locator('#risk-strategy');

    // Set values
    await maxRisk.fill('2');
    await defRisk.fill('1.2');
    await rr.fill('2');
    await strategy.selectOption('ATR');

    // Save
    await page.click('#settings-save');
    await expect(page.getByText('Saved')).toBeVisible();

    // Reload via SPA navigation
    await page.goto('/');
    await navSettings.click();

    await expect(maxRisk).toHaveValue('2');
    await expect(defRisk).toHaveValue('1.2');
    await expect(rr).toHaveValue('2');
    await expect(strategy).toHaveValue('ATR');
  });
});

