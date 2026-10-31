import { test, expect, Page } from '@playwright/test';

async function openQueue(page: Page) {
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'Spoke and Chain Repair Queue' }),
  ).toBeVisible();
}

// Both lists are plain list items with no name of their own. A job waiting in
// the queue is the one with a Finish button, and a done job hasn't got one.
function queueRows(page: Page) {
  return page
    .getByRole('listitem')
    .filter({ has: page.getByRole('button', { name: 'Finish' }) });
}

function doneRows(page: Page) {
  return page
    .getByRole('listitem')
    .filter({ hasNot: page.getByRole('button', { name: 'Finish' }) });
}

function job(page: Page, ticket: string) {
  // Three rows say "Brake pads", so the ticket is what picks one out.
  return queueRows(page).filter({ hasText: ticket });
}

function tickets(page: Page) {
  // The ticket is a bare span with no role, so its text is what reaches it.
  return queueRows(page).getByText(/^#\d+$/);
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
  await expect(queueRows(page)).toHaveCount(4);
  await expect(doneRows(page)).toHaveText(['#103 Brake pads (Chen)']);
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

  await expect(queueRows(page)).toHaveCount(5);
  await expect(job(page, '#101')).toHaveCount(1);
  await expect(doneRows(page)).toHaveCount(0);
  expect(message).toBe('Finish #101 Brake pads for Ruiz?');
});
