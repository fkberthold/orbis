// The reference's first test with the awaits dropped from its assertions,
// which is the commonest slip in TypeScript Playwright. The test ends before
// the desk answers, and Playwright fails the assertions still pending, so this
// objects to the real desk and the gate rejects it on G1.
import { test, expect } from '@playwright/test';

test('valid label prints', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Recipient', { exact: true }).fill('Ada Lovelace');
  await page.getByLabel('Postcode', { exact: true }).fill('02139');
  await page.getByLabel('Weight (kg)', { exact: true }).fill('2.5');
  await page.getByLabel('Service', { exact: true }).selectOption('Standard');
  await page.getByRole('button', { name: 'Print label' }).click();

  expect(page.getByRole('listitem')).toHaveText([
    'Ada Lovelace, 02139, 2.5 kg, Standard',
  ]);
  expect(page.getByLabel('Recipient', { exact: true })).toHaveValue('');
  expect(page.getByLabel('Postcode', { exact: true })).toHaveValue('');
  expect(page.getByLabel('Weight (kg)', { exact: true })).toHaveValue('');
});
