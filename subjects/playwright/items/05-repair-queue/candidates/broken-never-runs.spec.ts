// A candidate that can't be loaded, because what it imports doesn't exist. It
// exists so the did-not-run cell is driven by something, rather than being a
// name in a table nobody has reached.
import { test } from '@playwright/test';
import { openQueue } from './helpers-that-do-not-exist';

test('the queue loads', async ({ page }) => {
  await openQueue(page);
});
