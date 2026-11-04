// A candidate that passes the real app and catches nothing. The gate has to
// reject it, and watching that happen is how we know the gate measures.
import { test, expect } from '@playwright/test';

test('the desk loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Dockside Seat Desk');
});
