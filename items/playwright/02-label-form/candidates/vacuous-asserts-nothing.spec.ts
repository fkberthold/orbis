// A candidate that asserts nothing at all. It should land in the vacuous cell
// rather than the silent one, which is the whole reason two cells aren't
// enough. It even presses the button, so doing things isn't mistaken for
// checking them.
import { test } from '@playwright/test';

test('the desk answers', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Recipient', { exact: true }).fill('Ada Lovelace');
  await page.getByLabel('Postcode', { exact: true }).fill('02139');
  await page.getByLabel('Weight (kg)', { exact: true }).fill('2.5');
  await page.getByRole('button', { name: 'Print label' }).click();
});
