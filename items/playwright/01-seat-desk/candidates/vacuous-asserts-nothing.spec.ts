// A candidate that clicks through the whole desk and checks nothing. It passes
// everywhere, and the cell that says so is vacuous rather than silent.
import { test } from '@playwright/test';

test('reserve a seat', async ({ page }) => {
  await page.goto('/');
  await page.fill('#name', 'Ada');
  await page.selectOption('#seat', 'A1');
  await page.click('#reserve');
});
