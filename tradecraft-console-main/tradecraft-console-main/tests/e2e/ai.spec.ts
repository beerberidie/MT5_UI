import { test, expect } from '@playwright/test';
import { api } from './helpers';

test.describe('AI Page E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to AI page
    await page.goto('/');
    await page.locator('#nav-ai').click();
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible({ timeout: 10000 });
  });

  test('loads AI page without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() !== 'error') return;
      const text = `[${msg.location().url}:${msg.location().lineNumber}] ${msg.text()}`;
      // Ignore known benign external font CORS noise
      if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
      errors.push(text);
    });

    // Reload to capture console errors
    await page.reload();
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible({ timeout: 10000 });

    // Verify no console errors
    expect(errors, errors.join('\n')).toHaveLength(0);
  });

  test('displays AI page content', async ({ page }) => {
    // Page should have loaded successfully
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible();

    // Should have tab navigation
    const overviewTab = page.getByRole('button', { name: /overview/i });
    await expect(overviewTab).toBeVisible({ timeout: 5000 });
  });

  test('tab navigation works correctly', async ({ page }) => {
    // Overview tab should be visible
    const overviewTab = page.getByRole('button', { name: /overview/i });
    await expect(overviewTab).toBeVisible({ timeout: 5000 });

    // Click Strategies tab
    const strategiesTab = page.getByRole('button', { name: /strategies/i });
    await strategiesTab.click();
    await page.waitForTimeout(500);

    // Click History tab
    const historyTab = page.getByRole('button', { name: /history/i });
    await historyTab.click();
    await page.waitForTimeout(500);

    // Go back to Overview
    await overviewTab.click();
    await page.waitForTimeout(500);

    // Page should still be functional
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible();
  });

  test('keyboard navigation works for tabs', async ({ page }) => {
    // Focus on first tab
    const overviewTab = page.getByRole('button', { name: /overview/i });
    await overviewTab.focus();

    // Press Tab key to move to next element
    await page.keyboard.press('Tab');

    // Verify focus moved (element should be focused)
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });

  test('symbol selector is present', async ({ page }) => {
    // Look for symbol selector
    const symbolSelect = page.locator('select').first();

    // Should have at least one select element
    const selectCount = await page.locator('select').count();
    expect(selectCount).toBeGreaterThan(0);
  });

  test('responsive layout on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Reload page
    await page.reload();
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible({ timeout: 10000 });

    // Verify page is still functional
    const overviewTab = page.getByRole('button', { name: /overview/i });
    await expect(overviewTab).toBeVisible({ timeout: 5000 });

    // Reset viewport
    await page.setViewportSize({ width: 1366, height: 900 });
  });

  test('responsive layout on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    // Reload page
    await page.reload();
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible({ timeout: 10000 });

    // Verify page is still functional
    const overviewTab = page.getByRole('button', { name: /overview/i });
    await expect(overviewTab).toBeVisible({ timeout: 5000 });

    // Reset viewport
    await page.setViewportSize({ width: 1366, height: 900 });
  });

  test('no network errors during page load', async ({ page }) => {
    const failedRequests: string[] = [];

    page.on('requestfailed', (request) => {
      const url = request.url();
      // Ignore known benign failures (fonts, external resources)
      if (url.includes('fonts.gstatic.com') || url.includes('fonts.googleapis.com')) return;
      failedRequests.push(`${request.method()} ${url} - ${request.failure()?.errorText}`);
    });

    // Reload page to capture network errors
    await page.reload();
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible({ timeout: 10000 });

    // Wait for all network requests to complete
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // Verify no failed requests
    expect(failedRequests, failedRequests.join('\n')).toHaveLength(0);
  });

  test('page load performance is acceptable', async ({ page }) => {
    // Measure page load time
    const startTime = Date.now();

    await page.goto('/');
    await page.locator('#nav-ai').click();
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible({ timeout: 10000 });

    const loadTime = Date.now() - startTime;

    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('AI page remains functional after interactions', async ({ page }) => {
    // Wait for initial load
    await page.waitForTimeout(1000);

    // Click through tabs
    const strategiesTab = page.getByRole('button', { name: /strategies/i });
    await strategiesTab.click();
    await page.waitForTimeout(500);

    const historyTab = page.getByRole('button', { name: /history/i });
    await historyTab.click();
    await page.waitForTimeout(500);

    // Verify page didn't crash
    await expect(page.getByRole('heading', { name: /AI Trading/i })).toBeVisible();
  });

  test('page has interactive buttons', async ({ page }) => {
    // Should have multiple buttons on the page
    const buttonCount = await page.locator('button').count();
    expect(buttonCount).toBeGreaterThan(3);
  });
});

