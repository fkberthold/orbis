// A candidate that can't be loaded, because what it imports doesn't exist. It
// exists so the did-not-run cell is driven by something, rather than being a
// name in a table nobody has reached.
import { test, expect } from '@playwright/test';
import { openDesk } from './helpers-that-do-not-exist';

test('the desk loads', async ({ page }) => {
  await openDesk(page);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Northgate Label Desk');
});
