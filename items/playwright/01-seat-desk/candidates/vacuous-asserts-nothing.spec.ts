// A candidate that clicks through the whole desk and checks nothing. It passes
// everywhere, and the cell that says so is vacuous rather than silent.
import { test } from '@playwright/test';

test('reserve a seat', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Name').fill('Ada');
  await page.getByLabel('Seat').selectOption('A1');
  await page.getByRole('button', { name: 'Reserve' }).click();
});
