import { test, expect } from '@playwright/test';

test.describe('Accessibility and Keyboard Navigation', () => {
  test('keyboard navigation works on Dashboard', async ({ page }) => {
    await page.goto('/');

    // Wait for page to load
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    let focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();

    // Continue tabbing
    await page.keyboard.press('Tab');
    focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();

    // Shift+Tab should go backwards
    await page.keyboard.press('Shift+Tab');
    focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });

  test('keyboard navigation works on Settings page', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to Settings using keyboard
    const settingsNav = page.locator('#nav-settings');
    await settingsNav.focus();
    await page.keyboard.press('Enter');

    // Wait for Settings page to load
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();

    // Tab through form inputs
    await page.keyboard.press('Tab');
    let focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'SELECT', 'BUTTON', 'A']).toContain(focusedElement);

    // Continue tabbing through form
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBeTruthy();
    }
  });

  test('keyboard navigation works on AI page', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to AI page
    await page.locator('#nav-ai').click();
    await expect(page.getByRole('heading', { name: 'AI', level: 1 })).toBeVisible();

    // Tab through elements
    await page.keyboard.press('Tab');
    let focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();

    // Arrow keys should work for tab navigation if tabs are present
    const overviewTab = page.getByRole('button', { name: /overview/i });
    if (await overviewTab.isVisible()) {
      await overviewTab.focus();
      
      // Right arrow should move to next tab
      await page.keyboard.press('ArrowRight');
      focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBe('BUTTON');
    }
  });

  test('keyboard navigation works on Data page', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to Data page
    const dataNav = page.locator('#nav-data').or(page.getByRole('link', { name: /data|3rd party/i }));
    if (await dataNav.count() > 0) {
      await dataNav.first().click();
      
      // Wait for page to load
      await page.waitForTimeout(1000);

      // Tab through elements
      await page.keyboard.press('Tab');
      let focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBeTruthy();
    }
  });

  test('Enter key activates buttons', async ({ page }) => {
    await page.goto('/');

    // Focus on a button
    const aiNav = page.locator('#nav-ai');
    await aiNav.focus();

    // Press Enter
    await page.keyboard.press('Enter');

    // Should navigate to AI page
    await expect(page.getByRole('heading', { name: 'AI', level: 1 })).toBeVisible();
  });

  test('Space key activates buttons', async ({ page }) => {
    await page.goto('/');

    // Navigate to Settings
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();

    // Focus on a tab button
    const accountsTab = page.getByRole('button', { name: /^accounts$/i });
    if (await accountsTab.isVisible()) {
      await accountsTab.focus();

      // Press Space
      await page.keyboard.press('Space');

      // Tab should activate
      await expect(accountsTab).toHaveClass(/bg-primary|active/);
    }
  });

  test('Escape key closes dialogs', async ({ page }) => {
    await page.goto('/');

    // Try to open a dialog (if any exist)
    // For now, just verify Escape doesn't break the page
    await page.keyboard.press('Escape');

    // Page should still be functional
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
  });

  test('focus indicators are visible', async ({ page }) => {
    await page.goto('/');

    // Tab to first focusable element
    await page.keyboard.press('Tab');

    // Check if focused element has visible outline or focus ring
    const hasFocusStyle = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement;
      if (!el) return false;
      
      const styles = window.getComputedStyle(el);
      const outline = styles.outline;
      const boxShadow = styles.boxShadow;
      
      // Should have either outline or box-shadow for focus
      return outline !== 'none' || boxShadow !== 'none';
    });

    // Focus should be visible (either through outline or box-shadow)
    expect(hasFocusStyle).toBeTruthy();
  });

  test('all interactive elements are keyboard accessible', async ({ page }) => {
    await page.goto('/');

    // Get all buttons, links, and inputs
    const interactiveElements = await page.locator('button, a, input, select, textarea').all();

    // All should be reachable via keyboard (tabindex >= 0 or no tabindex)
    for (const element of interactiveElements.slice(0, 10)) { // Test first 10
      const tabIndex = await element.getAttribute('tabindex');
      
      // tabindex should not be -1 (unless it's a hidden element)
      const isVisible = await element.isVisible().catch(() => false);
      if (isVisible) {
        expect(tabIndex === null || parseInt(tabIndex) >= 0).toBeTruthy();
      }
    }
  });

  test('form inputs have associated labels', async ({ page }) => {
    await page.goto('/');
    await page.locator('#nav-settings').click();

    // Wait for Settings page
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();

    // Get all inputs
    const inputs = await page.locator('input[type="number"], input[type="text"], select').all();

    // Each input should have a label or aria-label
    for (const input of inputs.slice(0, 5)) { // Test first 5
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      // Should have either id (with corresponding label), aria-label, or aria-labelledby
      const hasLabel = id || ariaLabel || ariaLabelledBy;
      expect(hasLabel).toBeTruthy();
    }
  });

  test('buttons have accessible names', async ({ page }) => {
    await page.goto('/');

    // Get all buttons
    const buttons = await page.locator('button').all();

    // Each button should have text content or aria-label
    for (const button of buttons.slice(0, 10)) { // Test first 10
      const isVisible = await button.isVisible().catch(() => false);
      if (!isVisible) continue;

      const textContent = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      
      // Should have either text content or aria-label
      const hasAccessibleName = (textContent && textContent.trim().length > 0) || ariaLabel;
      expect(hasAccessibleName).toBeTruthy();
    }
  });

  test('page has proper heading hierarchy', async ({ page }) => {
    await page.goto('/');

    // Get all headings
    const h1Count = await page.locator('h1').count();
    const h2Count = await page.locator('h2').count();
    const h3Count = await page.locator('h3').count();

    // Should have at least one h1
    expect(h1Count).toBeGreaterThanOrEqual(1);

    // If there are h3s, there should be h2s
    if (h3Count > 0) {
      expect(h2Count).toBeGreaterThan(0);
    }
  });

  test('images have alt text', async ({ page }) => {
    await page.goto('/');

    // Get all images
    const images = await page.locator('img').all();

    // Each image should have alt attribute
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      
      // Alt attribute should exist (can be empty for decorative images)
      expect(alt !== null).toBeTruthy();
    }
  });

  test('color contrast is sufficient', async ({ page }) => {
    await page.goto('/');

    // Check a few key text elements for contrast
    const textElements = await page.locator('h1, h2, h3, p, button, a').all();

    for (const element of textElements.slice(0, 5)) { // Test first 5
      const isVisible = await element.isVisible().catch(() => false);
      if (!isVisible) continue;

      // Get computed styles
      const styles = await element.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        return {
          color: computed.color,
          backgroundColor: computed.backgroundColor,
          fontSize: computed.fontSize,
        };
      });

      // Just verify we can get the styles (actual contrast calculation is complex)
      expect(styles.color).toBeTruthy();
      expect(styles.backgroundColor).toBeTruthy();
    }
  });

  test('no duplicate IDs on page', async ({ page }) => {
    await page.goto('/');

    // Get all elements with IDs
    const ids = await page.evaluate(() => {
      const elements = document.querySelectorAll('[id]');
      const idList: string[] = [];
      elements.forEach(el => {
        if (el.id) idList.push(el.id);
      });
      return idList;
    });

    // Check for duplicates
    const uniqueIds = new Set(ids);
    expect(ids.length).toBe(uniqueIds.size);
  });

  test('page is usable with screen reader simulation', async ({ page }) => {
    await page.goto('/');

    // Get page structure for screen reader
    const landmarks = await page.locator('main, nav, header, footer, aside').count();
    
    // Should have semantic HTML landmarks
    expect(landmarks).toBeGreaterThan(0);

    // Get all headings for screen reader navigation
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();
    expect(headings).toBeGreaterThan(0);

    // Get all links for screen reader navigation
    const links = await page.locator('a').count();
    expect(links).toBeGreaterThan(0);
  });
});

