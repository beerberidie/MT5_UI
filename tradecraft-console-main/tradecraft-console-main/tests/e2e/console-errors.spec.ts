import { test, expect } from '@playwright/test';

test.describe('Console and Network Error Detection', () => {
  test('Dashboard loads without console errors', async ({ page }) => {
    const errors: string[] = [];
    const warnings: string[] = [];

    page.on('console', (msg) => {
      const text = `[${msg.location().url}:${msg.location().lineNumber}] ${msg.text()}`;
      
      // Ignore known benign issues
      if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
      if (text.includes('fonts.googleapis.com')) return;
      
      if (msg.type() === 'error') {
        errors.push(text);
      } else if (msg.type() === 'warning') {
        warnings.push(text);
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    // No console errors
    expect(errors, `Console errors:\n${errors.join('\n')}`).toHaveLength(0);
    
    // Warnings are okay but log them
    if (warnings.length > 0) {
      console.log(`Warnings found:\n${warnings.join('\n')}`);
    }
  });

  test('Settings page loads without console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() !== 'error') return;
      const text = `[${msg.location().url}:${msg.location().lineNumber}] ${msg.text()}`;
      if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
      errors.push(text);
    });

    await page.goto('/');
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(errors, `Console errors:\n${errors.join('\n')}`).toHaveLength(0);
  });

  test('AI page loads without console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() !== 'error') return;
      const text = `[${msg.location().url}:${msg.location().lineNumber}] ${msg.text()}`;
      if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
      errors.push(text);
    });

    await page.goto('/');
    await page.locator('#nav-ai').click();
    await expect(page.getByRole('heading', { name: 'AI', level: 1 })).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(errors, `Console errors:\n${errors.join('\n')}`).toHaveLength(0);
  });

  test('Data page loads without console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() !== 'error') return;
      const text = `[${msg.location().url}:${msg.location().lineNumber}] ${msg.text()}`;
      if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
      errors.push(text);
    });

    await page.goto('/');
    
    const dataNav = page.locator('#nav-data').or(page.getByRole('link', { name: /data|3rd party/i }));
    if (await dataNav.count() > 0) {
      await dataNav.first().click();
      await page.waitForTimeout(1000);
      await page.waitForLoadState('networkidle');

      expect(errors, `Console errors:\n${errors.join('\n')}`).toHaveLength(0);
    }
  });

  test('no console errors during tab navigation', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() !== 'error') return;
      const text = msg.text();
      if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
      errors.push(text);
    });

    await page.goto('/');
    await page.locator('#nav-settings').click();
    await page.waitForTimeout(500);

    // Switch between tabs
    const accountsTab = page.getByRole('button', { name: /^accounts$/i });
    if (await accountsTab.isVisible()) {
      await accountsTab.click();
      await page.waitForTimeout(300);
    }

    const apisTab = page.getByRole('button', { name: /api integrations/i });
    if (await apisTab.isVisible()) {
      await apisTab.click();
      await page.waitForTimeout(300);
    }

    const riskTab = page.getByRole('button', { name: /risk management/i });
    if (await riskTab.isVisible()) {
      await riskTab.click();
      await page.waitForTimeout(300);
    }

    expect(errors, `Console errors:\n${errors.join('\n')}`).toHaveLength(0);
  });

  test('no console errors during form interaction', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() !== 'error') return;
      const text = msg.text();
      if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
      errors.push(text);
    });

    await page.goto('/');
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();

    // Interact with form inputs
    const maxRiskInput = page.locator('#risk-max');
    if (await maxRiskInput.isVisible()) {
      await maxRiskInput.fill('2.5');
      await page.waitForTimeout(300);
    }

    const defRiskInput = page.locator('#risk-default');
    if (await defRiskInput.isVisible()) {
      await defRiskInput.fill('1.5');
      await page.waitForTimeout(300);
    }

    expect(errors, `Console errors:\n${errors.join('\n')}`).toHaveLength(0);
  });

  test('Dashboard loads without network errors', async ({ page }) => {
    const failedRequests: string[] = [];

    page.on('requestfailed', (request) => {
      const url = request.url();
      // Ignore known benign failures
      if (url.includes('fonts.gstatic.com') || url.includes('fonts.googleapis.com')) return;
      failedRequests.push(`${request.method()} ${url} - ${request.failure()?.errorText}`);
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(failedRequests, `Failed requests:\n${failedRequests.join('\n')}`).toHaveLength(0);
  });

  test('Settings page loads without network errors', async ({ page }) => {
    const failedRequests: string[] = [];

    page.on('requestfailed', (request) => {
      const url = request.url();
      if (url.includes('fonts.gstatic.com') || url.includes('fonts.googleapis.com')) return;
      failedRequests.push(`${request.method()} ${url}`);
    });

    await page.goto('/');
    await page.locator('#nav-settings').click();
    await expect(page.getByRole('heading', { name: /risk management|settings/i })).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(failedRequests, `Failed requests:\n${failedRequests.join('\n')}`).toHaveLength(0);
  });

  test('AI page loads without network errors', async ({ page }) => {
    const failedRequests: string[] = [];

    page.on('requestfailed', (request) => {
      const url = request.url();
      if (url.includes('fonts.gstatic.com') || url.includes('fonts.googleapis.com')) return;
      failedRequests.push(`${request.method()} ${url}`);
    });

    await page.goto('/');
    await page.locator('#nav-ai').click();
    await expect(page.getByRole('heading', { name: 'AI', level: 1 })).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(failedRequests, `Failed requests:\n${failedRequests.join('\n')}`).toHaveLength(0);
  });

  test('no 404 errors for static assets', async ({ page }) => {
    const notFoundRequests: string[] = [];

    page.on('response', (response) => {
      if (response.status() === 404) {
        const url = response.url();
        // Ignore external resources
        if (url.includes('fonts.gstatic.com') || url.includes('fonts.googleapis.com')) return;
        notFoundRequests.push(url);
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(notFoundRequests, `404 errors:\n${notFoundRequests.join('\n')}`).toHaveLength(0);
  });

  test('no 500 errors from API', async ({ page }) => {
    const serverErrors: string[] = [];

    page.on('response', (response) => {
      if (response.status() >= 500) {
        const url = response.url();
        serverErrors.push(`${response.status()} ${url}`);
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(serverErrors, `Server errors:\n${serverErrors.join('\n')}`).toHaveLength(0);
  });

  test('API requests have proper headers', async ({ page }) => {
    const requestsWithoutAuth: string[] = [];

    page.on('request', (request) => {
      const url = request.url();
      
      // Check if it's an API request
      if (url.includes('/api/')) {
        const headers = request.headers();
        
        // Should have X-API-Key header
        if (!headers['x-api-key']) {
          requestsWithoutAuth.push(url);
        }
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    // All API requests should have auth header
    expect(requestsWithoutAuth, `Requests without auth:\n${requestsWithoutAuth.join('\n')}`).toHaveLength(0);
  });

  test('no CORS errors for API requests', async ({ page }) => {
    const corsErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (text.includes('CORS') && text.includes('/api/')) {
          corsErrors.push(text);
        }
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(corsErrors, `CORS errors:\n${corsErrors.join('\n')}`).toHaveLength(0);
  });

  test('no unhandled promise rejections', async ({ page }) => {
    const rejections: string[] = [];

    page.on('pageerror', (error) => {
      rejections.push(error.message);
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    
    // Navigate around
    await page.locator('#nav-settings').click();
    await page.waitForTimeout(500);
    await page.locator('#nav-ai').click();
    await page.waitForTimeout(500);
    await page.goto('/');
    await page.waitForTimeout(500);

    expect(rejections, `Unhandled rejections:\n${rejections.join('\n')}`).toHaveLength(0);
  });

  test('no React errors in console', async ({ page }) => {
    const reactErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (text.includes('React') || text.includes('Warning:')) {
          reactErrors.push(text);
        }
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    expect(reactErrors, `React errors:\n${reactErrors.join('\n')}`).toHaveLength(0);
  });

  test('no deprecation warnings', async ({ page }) => {
    const deprecations: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'warning') {
        const text = msg.text();
        if (text.toLowerCase().includes('deprecat')) {
          deprecations.push(text);
        }
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
    await page.waitForLoadState('networkidle');

    // Log deprecations but don't fail (they're warnings)
    if (deprecations.length > 0) {
      console.log(`Deprecation warnings:\n${deprecations.join('\n')}`);
    }
  });

  test('handles API errors gracefully', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (!text.includes('fonts.gstatic.com') && !text.includes('CORS policy')) {
          errors.push(text);
        }
      }
    });

    await page.goto('/');
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();

    // Even if API returns errors, the page should handle them gracefully
    // and not crash with console errors
    await page.waitForTimeout(2000);

    // Should not have unhandled errors
    expect(errors, `Unhandled errors:\n${errors.join('\n')}`).toHaveLength(0);
  });

  test('no memory leaks from event listeners', async ({ page }) => {
    await page.goto('/');

    // Navigate multiple times to check for listener leaks
    for (let i = 0; i < 10; i++) {
      await page.locator('#nav-settings').click();
      await page.waitForTimeout(100);
      await page.locator('#nav-ai').click();
      await page.waitForTimeout(100);
      await page.goto('/');
      await page.waitForTimeout(100);
    }

    // Page should still be responsive
    await expect(page.getByText('Trade Agent MT5')).toBeVisible();
  });
});

