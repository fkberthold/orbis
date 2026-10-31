// The reference's first test with the awaits dropped from its assertions,
// which is the commonest slip in TypeScript Playwright. The test ends before
// the desk answers, and Playwright fails the assertions still pending, so this
// objects to the real desk and the gate rejects it on G1.
import { test, expect } from '@playwright/test';

test('reserve succeeds', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Name').fill('Ada');
  await page.getByLabel('Seat').selectOption('A1');
  await page.getByRole('button', { name: 'Reserve' }).click();

  // The banner is a bare <p> with no role or name to reach it by.
  expect(page.locator('#banner')).toHaveText('Reserved A1 for Ada.');
  expect(page.getByRole('listitem')).toHaveCount(1);
});
