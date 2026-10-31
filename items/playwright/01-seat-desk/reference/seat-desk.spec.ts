import { test, expect, Page } from '@playwright/test';

async function openDesk(page: Page) {
  await page.goto('/');
  await expect(page.locator('#heading')).toHaveText('Dockside Seat Desk');
}

test('reserve succeeds', async ({ page }) => {
  await openDesk(page);
  await page.fill('#name', 'Ada');
  await page.selectOption('#seat', 'A1');
  await page.click('#reserve');

  await expect(page.locator('#banner')).toHaveText('Reserved A1 for Ada.');
  await expect(page.locator('li.reservation')).toHaveCount(1);
  // The spinner has to come back down once the desk answers.
  await expect(page.locator('#status')).toHaveText('');
  await expect(page.locator('#reserve')).toBeEnabled();
});

test('taken seat is rejected', async ({ page }) => {
  await openDesk(page);
  await page.fill('#name', 'Ada');
  await page.selectOption('#seat', 'A2');
  await page.click('#reserve');

  await expect(page.locator('#error')).toHaveText('Seat A2 is already taken.');
  await expect(page.locator('li.reservation')).toHaveCount(0);
});

test('reserved seat is refused next time', async ({ page }) => {
  await openDesk(page);
  await page.fill('#name', 'Ada');
  await page.selectOption('#seat', 'A1');
  await page.click('#reserve');
  await expect(page.locator('#banner')).toHaveText('Reserved A1 for Ada.');

  // A1 was free when the page loaded, so only the first reservation can be
  // what makes it taken.
  await page.fill('#name', 'Bo');
  await page.selectOption('#seat', 'A1');
  await page.click('#reserve');

  await expect(page.locator('#error')).toHaveText('Seat A1 is already taken.');
  await expect(page.locator('li.reservation')).toHaveCount(1);
});

test('double click reserves once', async ({ page }) => {
  await openDesk(page);
  await page.fill('#name', 'Ada');
  await page.selectOption('#seat', 'A1');

  // force, because the button is meant to be down for the second click.
  await page.dblclick('#reserve', { force: true });

  await expect(page.locator('li.reservation')).toHaveCount(1);
  await expect(page.locator('#error')).toHaveText('');
});
