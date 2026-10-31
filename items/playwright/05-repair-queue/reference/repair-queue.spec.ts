import { test, expect, Page } from '@playwright/test';

async function openQueue(page: Page) {
  await page.goto('/');
  await expect(page.locator('#heading')).toHaveText('Spoke and Chain Repair Queue');
}

function job(page: Page, ticket: string) {
  // Three rows say "Brake pads", so the ticket is what picks one out.
  return page.locator('li.job').filter({ hasText: ticket });
}

function tickets(page: Page) {
  return page.locator('li.job .ticket');
}

test('queue starts in priority order', async ({ page }) => {
  await openQueue(page);
  await expect(tickets(page)).toHaveText(['#102', '#101', '#104', '#105', '#103']);
});

test('raising priority resorts', async ({ page }) => {
  await openQueue(page);
  await job(page, '#105').getByLabel('Priority').selectOption('High');

  // #105 joins #102 at High and stays behind it, because #102 is older.
  await expect(tickets(page)).toHaveText(['#102', '#105', '#101', '#104', '#103']);
});

test('finish removes only that job', async ({ page }) => {
  await openQueue(page);
  let message = '';
  page.once('dialog', async (dialog) => {
    message = dialog.message();
    await dialog.accept();
  });
  await job(page, '#103').getByRole('button', { name: 'Finish' }).click();

  await expect(job(page, '#103')).toHaveCount(0);
  await expect(page.locator('li.job')).toHaveCount(4);
  await expect(page.locator('#done li')).toHaveText(['#103 Brake pads (Chen)']);
  expect(message).toBe('Finish #103 Brake pads for Chen?');
});

test('cancel keeps the job', async ({ page }) => {
  await openQueue(page);
  let message = '';
  page.once('dialog', async (dialog) => {
    message = dialog.message();
    await dialog.dismiss();
  });
  await job(page, '#101').getByRole('button', { name: 'Finish' }).click();

  await expect(page.locator('li.job')).toHaveCount(5);
  await expect(job(page, '#101')).toHaveCount(1);
  await expect(page.locator('#done li')).toHaveCount(0);
  expect(message).toBe('Finish #101 Brake pads for Ruiz?');
});
