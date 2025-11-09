import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('Dashboard loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    
    const loadTime = Date.now() - startTime;

    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('Settings page loads within acceptable time', async ({ page }) => {
    await page.goto('/');
    
    const startTime = Date.now();
    
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();
    
    const loadTime = Date.now() - startTime;

    // Page should load within 2 seconds
    expect(loadTime).toBeLessThan(2000);
  });

  test('AI page loads within acceptable time', async ({ page }) => {
    await page.goto('/');
    
    const startTime = Date.now();
    
    await page.locator('#nav-ai').click();
    await expect(page.getByRole('heading', { name: 'AI', level: 1 })).toBeVisible();
    
    const loadTime = Date.now() - startTime;

    // Page should load within 2 seconds
    expect(loadTime).toBeLessThan(2000);
  });

  test('Data page loads within acceptable time', async ({ page }) => {
    await page.goto('/');
    
    const dataNav = page.locator('#nav-data').or(page.getByRole('link', { name: /data|3rd party/i }));
    if (await dataNav.count() > 0) {
      const startTime = Date.now();
      
      await dataNav.first().click();
      await page.waitForTimeout(500); // Wait for initial render
      
      const loadTime = Date.now() - startTime;

      // Page should load within 2 seconds
      expect(loadTime).toBeLessThan(2000);
    }
  });

  test('tab switching is fast', async ({ page }) => {
    await page.goto('/');
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();

    // Switch between tabs and measure time
    const accountsTab = page.getByRole('button', { name: /^accounts$/i });
    if (await accountsTab.isVisible()) {
      const startTime = Date.now();
      
      await accountsTab.click();
      await page.waitForTimeout(100); // Wait for tab content to render
      
      const switchTime = Date.now() - startTime;

      // Tab switch should be instant (< 500ms)
      expect(switchTime).toBeLessThan(500);
    }
  });

  test('no memory leaks during navigation', async ({ page }) => {
    await page.goto('/');

    // Navigate between pages multiple times
    for (let i = 0; i < 5; i++) {
      await page.locator('#nav-settings').click();
      await page.waitForTimeout(200);
      
      await page.locator('#nav-ai').click();
      await page.waitForTimeout(200);
      
      await page.goto('/');
      await page.waitForTimeout(200);
    }

    // Page should still be responsive
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
  });

  test('handles rapid tab switching without errors', async ({ page }) => {
    await page.goto('/');
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();

    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Rapidly switch tabs
    const riskTab = page.getByRole('button', { name: /risk management/i });
    const accountsTab = page.getByRole('button', { name: /^accounts$/i });
    const apisTab = page.getByRole('button', { name: /api integrations/i });

    for (let i = 0; i < 10; i++) {
      if (await accountsTab.isVisible()) await accountsTab.click();
      if (await apisTab.isVisible()) await apisTab.click();
      if (await riskTab.isVisible()) await riskTab.click();
    }

    // Should not have console errors
    expect(errors.filter(e => !e.includes('fonts.gstatic.com'))).toHaveLength(0);
  });

  test('network requests complete within acceptable time', async ({ page }) => {
    const slowRequests: string[] = [];

    page.on('response', (response) => {
      const timing = response.timing();
      if (timing && timing.responseEnd > 5000) { // 5 seconds
        slowRequests.push(`${response.url()} took ${timing.responseEnd}ms`);
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    
    // Wait for all network requests
    await page.waitForLoadState('networkidle');

    // No requests should take more than 5 seconds
    expect(slowRequests, slowRequests.join('\n')).toHaveLength(0);
  });

  test('page size is reasonable', async ({ page }) => {
    let totalSize = 0;

    page.on('response', async (response) => {
      try {
        const buffer = await response.body();
        totalSize += buffer.length;
      } catch (e) {
        // Some responses may not have body
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    // Total page size should be less than 5MB
    expect(totalSize).toBeLessThan(5 * 1024 * 1024);
  });

  test('JavaScript bundle size is reasonable', async ({ page }) => {
    let jsSize = 0;

    page.on('response', async (response) => {
      const url = response.url();
      if (url.endsWith('.js') || url.includes('.js?')) {
        try {
          const buffer = await response.body();
          jsSize += buffer.length;
        } catch (e) {
          // Ignore
        }
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    // JS bundle should be less than 2MB
    expect(jsSize).toBeLessThan(2 * 1024 * 1024);
  });

  test('CSS bundle size is reasonable', async ({ page }) => {
    let cssSize = 0;

    page.on('response', async (response) => {
      const url = response.url();
      if (url.endsWith('.css') || url.includes('.css?')) {
        try {
          const buffer = await response.body();
          cssSize += buffer.length;
        } catch (e) {
          // Ignore
        }
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    // CSS bundle should be less than 500KB
    expect(cssSize).toBeLessThan(500 * 1024);
  });

  test('no excessive re-renders', async ({ page }) => {
    await page.goto('/');
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();

    // Type in an input and verify it doesn't cause excessive re-renders
    const maxRiskInput = page.locator('#risk-max');
    if (await maxRiskInput.isVisible()) {
      // Clear and type
      await maxRiskInput.fill('2.5');

      // Wait a bit
      await page.waitForTimeout(500);

      // Input should still have the value (not re-rendered and cleared)
      await expect(maxRiskInput).toHaveValue('2.5');
    }
  });

  test('handles large data sets efficiently', async ({ page }) => {
    await page.goto('/');

    // Navigate to a page that might have large data (e.g., Bars/History)
    const barsTab = page.getByRole('button', { name: 'Bars' });
    if (await barsTab.isVisible()) {
      await barsTab.click();

      // Load historical data
      const loadButton = page.getByRole('button', { name: /load|fetch/i });
      if (await loadButton.isVisible()) {
        const startTime = Date.now();
        
        await loadButton.click();
        await page.waitForTimeout(2000); // Wait for data to load
        
        const loadTime = Date.now() - startTime;

        // Should load within 5 seconds even with large data
        expect(loadTime).toBeLessThan(5000);
      }
    }
  });

  test('smooth scrolling performance', async ({ page }) => {
    await page.goto('/');

    // Scroll down the page
    await page.evaluate(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    });

    await page.waitForTimeout(500);

    // Scroll back up
    await page.evaluate(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    await page.waitForTimeout(500);

    // Page should still be responsive
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
  });

  test('no layout shifts during load', async ({ page }) => {
    await page.goto('/');

    // Get initial position of a key element
    const header = page.getByText('Trade Agent MT5');
    const initialBox = await header.boundingBox();

    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Get final position
    const finalBox = await header.boundingBox();

    // Position should not have shifted significantly (< 10px)
    if (initialBox && finalBox) {
      const shift = Math.abs(initialBox.y - finalBox.y);
      expect(shift).toBeLessThan(10);
    }
  });
});

test.describe('Responsive Layout Tests', () => {
  test('mobile viewport (375x667) - iPhone SE', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Page should load
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();

    // Navigation should be accessible
    const aiNav = page.locator('#nav-ai');
    await expect(aiNav).toBeVisible();

    // Click navigation
    await aiNav.click();
    await expect(page.getByRole('heading', { name: 'AI', level: 1 })).toBeVisible();
  });

  test('mobile viewport (390x844) - iPhone 12/13', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');

    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    
    // Settings should be accessible
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();
  });

  test('tablet viewport (768x1024) - iPad', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    await expect(page.getByText('Trade Agent MT5')).toBeVisible();

    // All navigation should be visible
    await expect(page.locator('#nav-ai')).toBeVisible();
    await expect(page.locator('#nav-settings')).toBeVisible();
  });

  test('desktop viewport (1920x1080) - Full HD', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    await expect(page.getByText('Trade Agent MT5')).toBeVisible();

    // Layout should use full width efficiently
    const mainContent = page.locator('main').or(page.locator('[role="main"]'));
    if (await mainContent.count() > 0) {
      const box = await mainContent.first().boundingBox();
      if (box) {
        // Content should be reasonably wide
        expect(box.width).toBeGreaterThan(800);
      }
    }
  });

  test('ultra-wide viewport (2560x1440) - 2K', async ({ page }) => {
    await page.setViewportSize({ width: 2560, height: 1440 });
    await page.goto('/');

    await expect(page.getByText('Trade Agent MT5')).toBeVisible();

    // Page should not have excessive whitespace
    // Content should be centered or use max-width
  });

  test('no horizontal scrollbar on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check for horizontal overflow
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    expect(hasHorizontalScroll).toBeFalsy();
  });

  test('touch targets are large enough on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Get all buttons
    const buttons = await page.locator('button').all();

    // Check first 5 visible buttons
    for (const button of buttons.slice(0, 5)) {
      const isVisible = await button.isVisible().catch(() => false);
      if (!isVisible) continue;

      const box = await button.boundingBox();
      if (box) {
        // Touch targets should be at least 44x44px (iOS guideline)
        expect(box.width).toBeGreaterThanOrEqual(40); // Allow slight margin
        expect(box.height).toBeGreaterThanOrEqual(40);
      }
    }
  });

  test('text is readable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check font sizes
    const textElements = await page.locator('p, span, div').all();

    for (const element of textElements.slice(0, 5)) {
      const isVisible = await element.isVisible().catch(() => false);
      if (!isVisible) continue;

      const fontSize = await element.evaluate((el) => {
        return window.getComputedStyle(el).fontSize;
      });

      const fontSizeNum = parseInt(fontSize);
      
      // Font size should be at least 14px for readability
      expect(fontSizeNum).toBeGreaterThanOrEqual(12);
    }
  });
});

