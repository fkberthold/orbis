// A candidate that asserts nothing at all. It should land in the vacuous cell
// rather than the silent one, which is the whole reason two cells aren't
// enough.
import { test } from '@playwright/test';

test('the lookup answers', async ({ page }) => {
  await page.goto('/');
});
