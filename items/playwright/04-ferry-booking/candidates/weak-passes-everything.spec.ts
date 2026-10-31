// A candidate that passes the real app and catches nothing. It only walks
// forward, and every break in this item lives in going Back or in skipping
// ahead, so the gate has to reject it.
import { test, expect } from '@playwright/test';

test('a booking gets a reference', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('radio', { name: '07:30 Harbor to Gull Isle' }).check();
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('textbox', { name: 'Lead passenger' }).fill('Ada');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('button', { name: 'Confirm' }).click();

  // A bare <p> with no role or name to reach it by.
  await expect(page.locator('#reference')).toContainText('FB-');
});
