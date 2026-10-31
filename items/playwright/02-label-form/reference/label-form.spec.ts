import { test, expect, Page } from '@playwright/test';

async function openDesk(page: Page) {
  await page.goto('/');
  await expect(page.locator('#heading')).toHaveText('Northgate Label Desk');
}

async function fillLabel(
  page: Page,
  recipient: string,
  postcode: string,
  weight: string,
  service: string,
) {
  await page.fill('#recipient', recipient);
  await page.fill('#postcode', postcode);
  await page.fill('#weight', weight);
  await page.selectOption('#service', service);
}

async function waitForAnswer(page: Page) {
  // A refusal and a print both land after the check, so "nothing printed"
  // only means something once "Checking..." has come and gone.
  await expect(page.locator('#status')).toHaveText('Checking...');
  await expect(page.locator('#status')).toHaveText('');
}

test('valid label prints', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, 'Ada Lovelace', '02139', '2.5', 'Standard');
  await page.click('#print');
  await waitForAnswer(page);

  await expect(page.locator('li.label')).toHaveText([
    'Ada Lovelace, 02139, 2.5 kg, Standard',
  ]);
  await expect(page.locator('#recipient')).toHaveValue('');
  await expect(page.locator('#postcode')).toHaveValue('');
  await expect(page.locator('#weight')).toHaveValue('');
});

test('bad fields are reported together', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, '   ', '021390', '0', 'Standard');
  await page.click('#print');
  await waitForAnswer(page);

  await expect(page.locator('#recipient-error')).toHaveText('Enter a recipient.');
  await expect(page.locator('#postcode-error')).toHaveText(
    'Postcode must be five digits.',
  );
  await expect(page.locator('#weight-error')).toHaveText(
    'Weight must be over 0 and at most 30 kg.',
  );
  await expect(page.locator('li.label')).toHaveCount(0);
});

test('weight tops out at thirty', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, 'Ada Lovelace', '02139', '30', 'Standard');
  await page.click('#print');
  await waitForAnswer(page);
  await expect(page.locator('li.label')).toHaveCount(1);

  await fillLabel(page, 'Ada Lovelace', '02139', '30.5', 'Standard');
  await page.click('#print');
  await waitForAnswer(page);
  await expect(page.locator('#weight-error')).toHaveText(
    'Weight must be over 0 and at most 30 kg.',
  );
  await expect(page.locator('li.label')).toHaveCount(1);
});

test('express takes five kg or less', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, 'Ada Lovelace', '02139', '5', 'Express');
  await page.click('#print');
  await waitForAnswer(page);
  await expect(page.locator('li.label')).toHaveCount(1);

  await fillLabel(page, 'Ada Lovelace', '02139', '5.5', 'Express');
  await page.click('#print');
  await waitForAnswer(page);
  await expect(page.locator('#service-error')).toHaveText(
    'Express takes 5 kg or less.',
  );
  // The weight is fine on its own, so it's the service that gets the blame.
  await expect(page.locator('#weight-error')).toHaveText('');
  await expect(page.locator('li.label')).toHaveCount(1);
});

test('fixing mistakes clears the messages', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, 'Ada Lovelace', '2139', '2.5', 'Standard');
  await page.click('#print');
  await waitForAnswer(page);
  await expect(page.locator('#postcode-error')).toHaveText(
    'Postcode must be five digits.',
  );

  // A refused label keeps what was typed, so only the postcode is redone.
  await page.fill('#postcode', '02139');
  await page.click('#print');
  await waitForAnswer(page);

  await expect(page.locator('li.label')).toHaveCount(1);
  await expect(page.locator('.field-error')).toHaveText(['', '', '', '']);
});
