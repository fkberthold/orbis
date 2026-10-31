import { test, expect, Page } from '@playwright/test';

async function openDesk(page: Page) {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Dockside Seat Desk');
}

// The banner is a bare <p> with no role or name to reach it by.
function banner(page: Page) {
  return page.locator('#banner');
}

test('reserve succeeds', async ({ page }) => {
  await openDesk(page);
  await page.getByLabel('Name').fill('Ada');
  await page.getByLabel('Seat').selectOption('A1');
  await page.getByRole('button', { name: 'Reserve' }).click();

  await expect(banner(page)).toHaveText('Reserved A1 for Ada.');
  await expect(page.getByRole('listitem')).toHaveCount(1);
  // The spinner has to come back down once the desk answers.
  await expect(page.getByRole('status')).toHaveText('');
  await expect(page.getByRole('button', { name: 'Reserve' })).toBeEnabled();
});

test('taken seat is rejected', async ({ page }) => {
  await openDesk(page);
  await page.getByLabel('Name').fill('Ada');
  await page.getByLabel('Seat').selectOption('A2');
  await page.getByRole('button', { name: 'Reserve' }).click();

  await expect(page.getByRole('alert')).toHaveText('Seat A2 is already taken.');
  await expect(page.getByRole('listitem')).toHaveCount(0);
});

test('reserved seat is refused next time', async ({ page }) => {
  await openDesk(page);
  await page.getByLabel('Name').fill('Ada');
  await page.getByLabel('Seat').selectOption('A1');
  await page.getByRole('button', { name: 'Reserve' }).click();
  await expect(banner(page)).toHaveText('Reserved A1 for Ada.');

  // A1 was free when the page loaded, so only the first reservation can be
  // what makes it taken.
  await page.getByLabel('Name').fill('Bo');
  await page.getByLabel('Seat').selectOption('A1');
  await page.getByRole('button', { name: 'Reserve' }).click();

  await expect(page.getByRole('alert')).toHaveText('Seat A1 is already taken.');
  await expect(page.getByRole('listitem')).toHaveCount(1);
});

test('double click reserves once', async ({ page }) => {
  await openDesk(page);
  await page.getByLabel('Name').fill('Ada');
  await page.getByLabel('Seat').selectOption('A1');

  // force, because the button is meant to be down for the second click.
  await page.getByRole('button', { name: 'Reserve' }).dblclick({ force: true });

  await expect(page.getByRole('listitem')).toHaveCount(1);
  await expect(page.getByRole('alert')).toHaveText('');
});
