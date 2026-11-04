// A candidate that passes the real app and catches nothing. The gate has to
// reject it, and watching that happen is how we know the gate measures.
//
// This one is the timing trap the task warns about. It checks that nothing was
// printed right after the click, before the desk has answered, so it passes
// against a desk that goes on to print a refused label.
import { test, expect } from '@playwright/test';

test('a blank label prints nothing', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Print label' }).click();
  await expect(page.getByRole('listitem')).toHaveCount(0);
});
