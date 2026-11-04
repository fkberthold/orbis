import { test, expect, Page } from '@playwright/test';

async function openDesk(page: Page) {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Northgate Label Desk',
  );
}

async function fillLabel(
  page: Page,
  recipient: string,
  postcode: string,
  weight: string,
  service: string,
) {
  await page.getByLabel('Recipient', { exact: true }).fill(recipient);
  await page.getByLabel('Postcode', { exact: true }).fill(postcode);
  await page.getByLabel('Weight (kg)', { exact: true }).fill(weight);
  await page.getByLabel('Service', { exact: true }).selectOption(service);
}

async function printLabel(page: Page) {
  await page.getByRole('button', { name: 'Print label' }).click();
}

// The messages under each field are bare paragraphs with no role or name, so
// their ids are the only way to reach them.
function fieldError(page: Page, field: string) {
  return page.locator(`#${field}-error`);
}

async function waitForAnswer(page: Page) {
  // A refusal and a print both land after the check, so "nothing printed"
  // only means something once "Checking..." has come and gone.
  await expect(page.getByRole('status')).toHaveText('Checking...');
  await expect(page.getByRole('status')).toHaveText('');
}

test('valid label prints', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, 'Ada Lovelace', '02139', '2.5', 'Standard');
  await printLabel(page);
  await waitForAnswer(page);

  await expect(page.getByRole('listitem')).toHaveText([
    'Ada Lovelace, 02139, 2.5 kg, Standard',
  ]);
  await expect(page.getByLabel('Recipient', { exact: true })).toHaveValue('');
  await expect(page.getByLabel('Postcode', { exact: true })).toHaveValue('');
  await expect(page.getByLabel('Weight (kg)', { exact: true })).toHaveValue('');
});

test('bad fields are reported together', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, '   ', '021390', '0', 'Standard');
  await printLabel(page);
  await waitForAnswer(page);

  await expect(fieldError(page, 'recipient')).toHaveText('Enter a recipient.');
  await expect(fieldError(page, 'postcode')).toHaveText(
    'Postcode must be five digits.',
  );
  await expect(fieldError(page, 'weight')).toHaveText(
    'Weight must be over 0 and at most 30 kg.',
  );
  await expect(page.getByRole('listitem')).toHaveCount(0);
});

test('weight tops out at thirty', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, 'Ada Lovelace', '02139', '30', 'Standard');
  await printLabel(page);
  await waitForAnswer(page);
  await expect(page.getByRole('listitem')).toHaveCount(1);

  await fillLabel(page, 'Ada Lovelace', '02139', '30.5', 'Standard');
  await printLabel(page);
  await waitForAnswer(page);
  await expect(fieldError(page, 'weight')).toHaveText(
    'Weight must be over 0 and at most 30 kg.',
  );
  await expect(page.getByRole('listitem')).toHaveCount(1);
});

test('express takes five kg or less', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, 'Ada Lovelace', '02139', '5', 'Express');
  await printLabel(page);
  await waitForAnswer(page);
  await expect(page.getByRole('listitem')).toHaveCount(1);

  await fillLabel(page, 'Ada Lovelace', '02139', '5.5', 'Express');
  await printLabel(page);
  await waitForAnswer(page);
  await expect(fieldError(page, 'service')).toHaveText(
    'Express takes 5 kg or less.',
  );
  // The weight is fine on its own, so it's the service that gets the blame.
  await expect(fieldError(page, 'weight')).toHaveText('');
  await expect(page.getByRole('listitem')).toHaveCount(1);
});

test('fixing mistakes clears the messages', async ({ page }) => {
  await openDesk(page);
  await fillLabel(page, 'Ada Lovelace', '2139', '2.5', 'Standard');
  await printLabel(page);
  await waitForAnswer(page);
  await expect(fieldError(page, 'postcode')).toHaveText(
    'Postcode must be five digits.',
  );

  // A refused label keeps what was typed, so only the postcode is redone.
  await page.getByLabel('Postcode', { exact: true }).fill('02139');
  await printLabel(page);
  await waitForAnswer(page);

  await expect(page.getByRole('listitem')).toHaveCount(1);
  // No role or name here either, so the class is what finds all four.
  await expect(page.locator('.field-error')).toHaveText(['', '', '', '']);
});
