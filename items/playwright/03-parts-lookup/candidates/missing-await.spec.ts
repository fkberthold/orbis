// The reference's "lists every part" test with the awaits dropped from its
// assertions, which is the commonest slip in TypeScript Playwright. The test
// ends before the catalog arrives, and Playwright fails the assertions still
// pending, so this objects to the real lookup and the gate rejects it.
import { test, expect } from '@playwright/test';

const CATALOG = [
  'BRK-1042 Front brake pad set',
  'BRK-1077 Rear brake rotor',
  'FLT-2010 Oil filter',
  'FLT-2033 Cabin air filter',
  'BLT-3105 Serpentine belt',
  'SPK-4001 Spark plug, iridium',
  'WPR-5020 Wiper blade, 22 inch',
  'BAT-6100 Battery, group 35',
];

test('lists every part', async ({ page }) => {
  await page.goto('/');
  expect(page.getByRole('searchbox', { name: 'Search' })).toBeEnabled();
  expect(page.getByRole('listitem')).toHaveText(CATALOG);
});
