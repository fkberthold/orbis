// The config you use while writing tests. It reads the app's address from
// BASE_URL, so the same file works for every item:
//
//   BASE_URL=http://127.0.0.1:8766 npx playwright test mine/01-seat-desk.spec.ts --ui
//
// The step page shows the right address for each item. The gate doesn't use
// this file. It writes its own for every run.
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testIgnore: ['node_modules/**', 'runs/**'],
  use: {
    baseURL: process.env.BASE_URL,
    trace: 'retain-on-failure',
  },
});
