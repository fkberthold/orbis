// The reference's first test with the awaits dropped from its assertions,
// which is the commonest slip in TypeScript Playwright. The test ends before
// the desk answers, and Playwright fails the assertions still pending, so this
// objects to the real desk and the gate rejects it on G1.
import { test, expect } from '@playwright/test';

test('valid label prints', async ({ page }) => {
  await page.goto('/');
  await page.fill('#recipient', 'Ada Lovelace');
  await page.fill('#postcode', '02139');
  await page.fill('#weight', '2.5');
  await page.selectOption('#service', 'Standard');
  await page.click('#print');

  expect(page.locator('li.label')).toHaveText([
    'Ada Lovelace, 02139, 2.5 kg, Standard',
  ]);
  expect(page.locator('#recipient')).toHaveValue('');
  expect(page.locator('#postcode')).toHaveValue('');
  expect(page.locator('#weight')).toHaveValue('');
});
