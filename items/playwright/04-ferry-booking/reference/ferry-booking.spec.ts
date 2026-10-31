import { test, expect, Page } from '@playwright/test';

function stepTitle(page: Page) {
  return page.locator('#step-title');
}

async function pickCrossing(page: Page, label: string) {
  await page.getByLabel(label).check();
  await page.getByRole('button', { name: 'Next' }).click();
  await expect(stepTitle(page)).toHaveText('2. Passengers');
}

async function enterPassengers(page: Page, lead: string, count: string) {
  await page.getByLabel('Lead passenger').fill(lead);
  await page.getByLabel('Passengers', { exact: true }).selectOption(count);
  await page.getByRole('button', { name: 'Next' }).click();
  await expect(stepTitle(page)).toHaveText('3. Review and confirm');
}

test('back keeps entries', async ({ page }) => {
  await page.goto('/');
  await pickCrossing(page, '07:30 Harbor to Gull Isle');
  await enterPassengers(page, 'Ada', '2');

  await page.goBack();
  await expect(stepTitle(page)).toHaveText('2. Passengers');
  await expect(page.getByLabel('Lead passenger')).toHaveValue('Ada');
  await expect(page.getByLabel('Passengers', { exact: true })).toHaveValue('2');

  await page.goBack();
  await expect(stepTitle(page)).toHaveText('1. Pick a crossing');
  await expect(page.getByLabel('07:30 Harbor to Gull Isle')).toBeChecked();
});

test('review shows changes', async ({ page }) => {
  await page.goto('/');
  await pickCrossing(page, '07:30 Harbor to Gull Isle');
  await enterPassengers(page, 'Ada', '2');
  await expect(page.locator('#review-fare')).toHaveText('$24');

  await page.goBack();
  await page.goBack();
  await expect(stepTitle(page)).toHaveText('1. Pick a crossing');
  await pickCrossing(page, '18:45 Harbor to Gull Isle');
  // Filled in again rather than trusted, so this test stays about the review
  // and doesn't also lean on Back keeping the fields.
  await enterPassengers(page, 'Grace', '3');

  await expect(page.locator('#review-crossing')).toHaveText('18:45 Harbor to Gull Isle');
  await expect(page.locator('#review-lead')).toHaveText('Grace');
  await expect(page.locator('#review-count')).toHaveText('3');
  await expect(page.locator('#review-fare')).toHaveText('$54');
});

test('confirm twice books once', async ({ page }) => {
  await page.goto('/');
  await pickCrossing(page, '12:15 Harbor to Gull Isle');
  await enterPassengers(page, 'Ada', '1');
  await page.getByRole('button', { name: 'Confirm' }).click();

  const reference = page.locator('#reference');
  await expect(reference).toHaveText(/Booking FB-\d+/);
  const first = await reference.innerText();

  await page.goBack();
  await expect(stepTitle(page)).toHaveText('3. Review and confirm');
  await page.getByRole('button', { name: 'Confirm' }).click();

  await expect(reference).toHaveText(first);
  await expect(page.locator('li.booking')).toHaveCount(1);
});

test('deep link starts over', async ({ page }) => {
  for (const address of ['/#/review', '/#/passengers']) {
    await page.goto(address);
    // The address first, because the second goto only changes the hash and
    // the crossing step is still on screen from the first one.
    await expect(page).toHaveURL(/#\/crossing$/);
    await expect(stepTitle(page)).toHaveText('1. Pick a crossing');
  }
});
