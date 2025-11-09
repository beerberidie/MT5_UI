# E2E Testing Guide - MT5_UI Tradecraft Console

## Overview

This guide covers the end-to-end (E2E) testing infrastructure for the MT5_UI Tradecraft Console application using Playwright.

## Table of Contents

1. [Setup](#setup)
2. [Running Tests](#running-tests)
3. [Test Structure](#test-structure)
4. [Writing Tests](#writing-tests)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Setup

### Prerequisites

- Node.js 18+ installed
- Python 3.11 with `.venv311` virtual environment
- FastAPI backend configured
- Vite React frontend built

### Installation

Playwright is already installed as a dev dependency:

```bash
npm install
```

### Configuration

The Playwright configuration is in `playwright.config.ts`:

- **Test Directory**: `./tests/e2e`
- **Timeout**: 45 seconds per test
- **Retries**: 1 retry on failure
- **Workers**: 1 (sequential execution)
- **Auto-start servers**:
  - Vite preview server on port 3000
  - FastAPI backend on port 5001

---

## Running Tests

### Run All E2E Tests

```bash
npm run test:e2e
```

### Run Specific Test File

```bash
npm run test:e2e -- tests/e2e/smoke.spec.ts
```

### Run Tests in UI Mode (Interactive)

```bash
npm run test:e2e:ui
```

### Run Tests in Debug Mode

```bash
npm run test:e2e:debug
```

### Run Tests with Specific Reporter

```bash
npm run test:e2e -- --reporter=list
npm run test:e2e -- --reporter=html
```

---

## Test Structure

### Test Files

```
tests/e2e/
├── smoke.spec.ts              # Basic smoke tests
├── navigation.spec.ts         # Navigation and routing tests
├── settings.spec.ts           # Settings page persistence tests
├── ai.spec.ts                 # AI page functionality tests
├── accessibility.spec.ts      # Keyboard navigation and a11y tests
├── performance.spec.ts        # Performance and responsive layout tests
├── console-errors.spec.ts     # Console and network error detection
├── bars.spec.ts              # Historical bars functionality
├── market.spec.ts            # Market data tests
├── pending.spec.ts           # Pending orders tests
├── error-handling.spec.ts    # Error handling tests
└── helpers.ts                # Shared utilities and API helpers
```

### Test Categories

#### 1. **Smoke Tests** (`smoke.spec.ts`)
- Basic page load
- Core UI elements visible
- No console errors

#### 2. **Navigation Tests** (`navigation.spec.ts`)
- Tab switching
- Page routing
- UI state persistence

#### 3. **Settings Tests** (`settings.spec.ts`)
- Form input persistence
- Settings save/load
- LocalStorage integration

#### 4. **AI Tests** (`ai.spec.ts`)
- AI page load
- Tab navigation
- Symbol selection
- Responsive layout
- Performance

#### 5. **Accessibility Tests** (`accessibility.spec.ts`)
- Keyboard navigation
- Focus indicators
- ARIA labels
- Screen reader compatibility
- Semantic HTML

#### 6. **Performance Tests** (`performance.spec.ts`)
- Page load times
- Bundle sizes
- Network request performance
- Responsive layouts (mobile, tablet, desktop)
- No layout shifts

#### 7. **Console Error Tests** (`console-errors.spec.ts`)
- No console errors
- No network failures
- No unhandled promise rejections
- Proper API headers
- No CORS errors

---

## Writing Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    const button = page.getByRole('button', { name: /click me/i });

    // Act
    await button.click();

    // Assert
    await expect(page.getByText('Success')).toBeVisible();
  });
});
```

### Using Helpers

```typescript
import { api, getTick, getPositions } from './helpers';

test('should fetch market data', async ({ page }) => {
  const tick = await getTick('EURUSD');
  expect(tick.bid).toBeGreaterThan(0);
});
```

### Console Error Detection

```typescript
test('should not have console errors', async ({ page }) => {
  const errors: string[] = [];
  
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      // Ignore known benign errors
      if (text.includes('fonts.gstatic.com')) return;
      errors.push(text);
    }
  });

  await page.goto('/');
  
  expect(errors, `Console errors:\n${errors.join('\n')}`).toHaveLength(0);
});
```

### Network Error Detection

```typescript
test('should not have network errors', async ({ page }) => {
  const failedRequests: string[] = [];

  page.on('requestfailed', (request) => {
    const url = request.url();
    if (url.includes('fonts.gstatic.com')) return;
    failedRequests.push(`${request.method()} ${url}`);
  });

  await page.goto('/');
  await page.waitForLoadState('networkidle');

  expect(failedRequests).toHaveLength(0);
});
```

### Responsive Layout Testing

```typescript
test('should work on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('/');
  
  await expect(page.getByText('Trade Agent MT5')).toBeVisible();
  
  // Reset viewport
  await page.setViewportSize({ width: 1366, height: 900 });
});
```

---

## Best Practices

### 1. **Use Semantic Queries**

Prefer role-based queries over CSS selectors:

```typescript
// ✅ Good
await page.getByRole('button', { name: /submit/i });
await page.getByRole('heading', { name: /settings/i });

// ❌ Avoid
await page.locator('.submit-button');
await page.locator('#heading-1');
```

### 2. **Add Timeouts for Async Operations**

```typescript
// ✅ Good
await expect(element).toBeVisible({ timeout: 10000 });
await page.waitForLoadState('networkidle', { timeout: 15000 });

// ❌ Avoid (uses default timeout which may be too short)
await expect(element).toBeVisible();
```

### 3. **Ignore Known Benign Errors**

```typescript
// Ignore external font CORS errors
if (text.includes('fonts.gstatic.com') || text.includes('CORS policy')) return;
```

### 4. **Use Descriptive Test Names**

```typescript
// ✅ Good
test('loads AI page without console errors', async ({ page }) => {});

// ❌ Avoid
test('test 1', async ({ page }) => {});
```

### 5. **Clean Up After Tests**

```typescript
test.afterEach(async ({ page }) => {
  // Reset viewport
  await page.setViewportSize({ width: 1366, height: 900 });
});
```

### 6. **Use Regex for Flexible Matching**

```typescript
// ✅ Good - case insensitive, flexible
await page.getByRole('heading', { name: /AI Trading/i });

// ❌ Avoid - exact match, brittle
await page.getByRole('heading', { name: 'AI Trading' });
```

### 7. **Wait for Network Idle**

```typescript
await page.goto('/');
await page.waitForLoadState('networkidle');
```

---

## Troubleshooting

### Tests Timing Out

**Problem**: Tests fail with timeout errors.

**Solutions**:
1. Increase timeout in test:
   ```typescript
   test('slow test', async ({ page }) => {
     test.setTimeout(60000); // 60 seconds
   });
   ```

2. Check if servers are running:
   ```bash
   # Vite preview should be on port 3000
   # FastAPI should be on port 5001
   ```

3. Add explicit waits:
   ```typescript
   await page.waitForLoadState('networkidle', { timeout: 15000 });
   ```

### Console Errors Not Captured

**Problem**: Console errors are not being detected.

**Solution**: Ensure listener is set up before navigation:
```typescript
const errors: string[] = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') errors.push(msg.text());
});
await page.goto('/'); // Navigate AFTER setting up listener
```

### Element Not Found

**Problem**: `locator.click: Target closed` or element not found.

**Solutions**:
1. Wait for element to be visible:
   ```typescript
   await expect(element).toBeVisible({ timeout: 10000 });
   await element.click();
   ```

2. Use more flexible selectors:
   ```typescript
   // Instead of exact text
   page.getByText('Submit')
   
   // Use regex
   page.getByText(/submit/i)
   ```

### Network Requests Failing

**Problem**: API requests return 401 or 403.

**Solution**: Check API key in `playwright.config.ts`:
```typescript
extraHTTPHeaders: {
  'X-API-Key': process.env.AUGMENT_API_KEY || 'AC135782469AD',
}
```

### Servers Not Starting

**Problem**: Playwright can't start Vite or FastAPI servers.

**Solutions**:
1. Build the frontend first:
   ```bash
   npm run build
   ```

2. Check Python virtual environment:
   ```bash
   .\.venv311\Scripts\python.exe -m uvicorn backend.app:app --version
   ```

3. Check port availability:
   ```bash
   netstat -ano | findstr :3000
   netstat -ano | findstr :5001
   ```

---

## Coverage Goals

### Current Coverage

- ✅ Smoke tests
- ✅ Navigation tests
- ✅ Settings persistence
- ✅ AI page functionality
- ✅ Keyboard accessibility
- ✅ Responsive layouts
- ✅ Console error detection
- ✅ Network error detection
- ✅ Performance metrics

### Future Coverage

- [ ] Trade execution workflows
- [ ] Real-time data updates
- [ ] WebSocket connections
- [ ] Multi-account switching
- [ ] Advanced AI features
- [ ] Visual regression testing

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          npm install
          pip install -r requirements.txt
      
      - name: Build frontend
        run: npm run build
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

---

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Testing Library Best Practices](https://testing-library.com/docs/queries/about)
- [Web Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

**Last Updated**: 2025-10-10
**Version**: 1.0.0

