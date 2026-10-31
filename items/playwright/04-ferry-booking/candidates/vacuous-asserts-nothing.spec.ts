// A candidate that asserts nothing at all. It walks the whole booking, so it
// looks busy, and it should still land in the vacuous cell rather than the
// silent one.
import { test } from '@playwright/test';

test('the booking goes through', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('07:30 Harbor to Gull Isle').check();
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByLabel('Lead passenger').fill('Ada');
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('button', { name: 'Confirm' }).click();
});
