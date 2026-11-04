// A candidate that passes the real app and catches nothing. It checks that five
// rows are there, which every broken copy also gets right. The gate has to
// reject it, and watching that happen is how we know the gate measures.
import { test, expect } from '@playwright/test';

test('the queue loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('listitem')).toHaveCount(5);
});
