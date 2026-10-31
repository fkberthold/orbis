// A candidate that passes the real app and catches nothing. The gate has to
// reject it, and watching that happen is how we know the gate measures.
//
// It checks the heading, which no break touches. A pass-or-fail grader would
// call this test correct.
import { test, expect } from '@playwright/test';

test('the lookup loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#heading')).toHaveText('Northgate Parts Lookup');
});
