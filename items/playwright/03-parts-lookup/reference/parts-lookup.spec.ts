import { test, expect, Page } from '@playwright/test';

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

async function openLookup(page: Page) {
  await page.goto('/');
  // Waiting for the box to come on is waiting for the catalog, so every test
  // after this sees the real parts.json and not an empty list.
  await expect(page.locator('#search')).toBeEnabled();
}

test('loading notice clears', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#status')).toHaveText('Loading parts...');
  await expect(page.locator('#search')).toBeDisabled();

  await expect(page.locator('#status')).toHaveText('');
  await expect(page.locator('#search')).toBeEnabled();
});

test('lists every part', async ({ page }) => {
  await openLookup(page);
  await expect(page.locator('li.part')).toHaveText(CATALOG);
});

test('search by name ignores case', async ({ page }) => {
  await openLookup(page);
  await page.fill('#search', 'BRAKE');
  await expect(page.locator('li.part')).toHaveText([
    'BRK-1042 Front brake pad set',
    'BRK-1077 Rear brake rotor',
  ]);
});

test('search by part number', async ({ page }) => {
  await openLookup(page);
  await page.fill('#search', 'FLT-20');
  await expect(page.locator('li.part')).toHaveText([
    'FLT-2010 Oil filter',
    'FLT-2033 Cabin air filter',
  ]);
});

test('search with no match', async ({ page }) => {
  await openLookup(page);
  await page.fill('#search', 'carburetor');
  await expect(page.locator('li.part')).toHaveCount(0);
  await expect(page.locator('#empty')).toHaveText('No parts match "carburetor".');
});

test('failed catalog is reported', async ({ page }) => {
  // The real file never fails, so the failure has to be made here. The body
  // is JSON on purpose, since a lot of servers send their errors that way. A
  // body that won't parse would let an app that never checks the status get
  // the right message by accident.
  await page.route('**/parts.json', route =>
    route.fulfill({ status: 500, json: { error: 'catalog offline' } }),
  );
  await page.goto('/');
  await expect(page.locator('#error')).toHaveText("Couldn't load the parts catalog.");
  await expect(page.locator('#status')).toHaveText('');
  await expect(page.locator('li.part')).toHaveCount(0);
});

test('empty catalog is reported', async ({ page }) => {
  await page.route('**/parts.json', route =>
    route.fulfill({ status: 200, json: [] }),
  );
  await page.goto('/');
  await expect(page.locator('#error')).toHaveText('The parts catalog is empty.');
  await expect(page.locator('#status')).toHaveText('');
  await expect(page.locator('li.part')).toHaveCount(0);
});
