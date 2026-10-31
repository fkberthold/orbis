// The reference's first test with the awaits dropped from its assertions,
// which is the commonest slip in TypeScript Playwright. Here it doesn't object
// to the real booking, and it still catches the break in Back keeping the
// passengers. The gate rejects it on G2, because it stays silent against the
// other three breaks. That's the same reason any one-test candidate fails, so
// the missing awaits aren't what this item's gate catches.
import { test, expect, Page } from '@playwright/test';

function stepTitle(page: Page) {
  return page.getByRole('heading', { level: 2 });
}

test('back keeps entries', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('radio', { name: '07:30 Harbor to Gull Isle' }).check();
  await page.getByRole('button', { name: 'Next' }).click();
  await page.getByRole('textbox', { name: 'Lead passenger' }).fill('Ada');
  await page.getByRole('combobox', { name: 'Passengers', exact: true }).selectOption('2');
  await page.getByRole('button', { name: 'Next' }).click();

  await page.goBack();
  expect(stepTitle(page)).toHaveText('2. Passengers');
  expect(page.getByRole('textbox', { name: 'Lead passenger' })).toHaveValue('Ada');
  expect(page.getByRole('combobox', { name: 'Passengers', exact: true })).toHaveValue('2');

  await page.goBack();
  expect(stepTitle(page)).toHaveText('1. Pick a crossing');
  expect(page.getByRole('radio', { name: '07:30 Harbor to Gull Isle' })).toBeChecked();
});
