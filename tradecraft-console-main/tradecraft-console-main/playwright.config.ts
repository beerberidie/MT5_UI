import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 45 * 1000,
  expect: { timeout: 7000 },
  retries: 1,
  workers: 1,
  reporter: 'list',
  webServer: [
    {
      command: 'npx vite preview --port 3000 --strictPort',
      url: 'http://127.0.0.1:3000',
      reuseExistingServer: true,
      timeout: 60 * 1000,
    },
    {
      // Start FastAPI backend with uvicorn from repo root (Windows cmd)
      command: 'cmd /d /s /c "cd ..\\.. && .\\.venv311\\Scripts\\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 5001"',
      url: 'http://127.0.0.1:5001/api/health',
      reuseExistingServer: true,
      timeout: 60 * 1000,
    },
  ],
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1366, height: 900 },
    ignoreHTTPSErrors: true,
    extraHTTPHeaders: {
      'X-API-Key': process.env.AUGMENT_API_KEY || 'AC135782469AD',
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});

