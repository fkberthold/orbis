// A candidate that can't be loaded, because what it imports doesn't exist. No
// test reaches a verdict, so every cell reads did-not-run.
import { test, expect } from '@playwright/test';
import { openDesk } from './helpers-that-do-not-exist';

test('reserve succeeds', async ({ page }) => {
  await openDesk(page);
  // The banner is a bare <p> with no role or name to reach it by.
  await expect(page.locator('#banner')).toHaveText('Reserved A1 for Ada.');
});
