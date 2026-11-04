// The reference's finish test with the awaits dropped from its web-first
// assertions, which is the commonest slip in TypeScript Playwright. The queue
// answers at once, so the pending assertions still settle and still count. It
// passes the real queue and catches the four copies that break Finish. It's
// rejected on G2, because it's silent against the copies that break sorting
// and cancel, and that's down to it being one test, not to the missing awaits.
import { test, expect } from '@playwright/test';

test('finish removes only that job', async ({ page }) => {
  await page.goto('/');
  let message = '';
  page.once('dialog', async (dialog) => {
    message = dialog.message();
    await dialog.accept();
  });
  await page
    .getByRole('listitem')
    .filter({ hasText: '#103' })
    .getByRole('button', { name: 'Finish' })
    .click();

  const finish = page.getByRole('button', { name: 'Finish' });
  const queueRows = page.getByRole('listitem').filter({ has: finish });
  const doneRows = page.getByRole('listitem').filter({ hasNot: finish });

  expect(queueRows.filter({ hasText: '#103' })).toHaveCount(0);
  expect(queueRows).toHaveCount(4);
  expect(doneRows).toHaveText(['#103 Brake pads (Chen)']);
  expect(message).toBe('Finish #103 Brake pads for Chen?');
});
