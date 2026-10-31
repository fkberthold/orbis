// A candidate that asserts nothing at all. It should land in the vacuous cell
// rather than the silent one, which is the whole reason two cells aren't
// enough. It even presses the button, so doing things isn't mistaken for
// checking them.
import { test } from '@playwright/test';

test('the desk answers', async ({ page }) => {
  await page.goto('/');
  await page.fill('#recipient', 'Ada Lovelace');
  await page.fill('#postcode', '02139');
  await page.fill('#weight', '2.5');
  await page.click('#print');
});
