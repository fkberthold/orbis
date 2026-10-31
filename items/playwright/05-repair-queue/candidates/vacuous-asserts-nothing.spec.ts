// A candidate that asserts nothing at all. It clicks Finish and walks away,
// which is how a real vacuous test looks. It should land in the vacuous cell
// rather than the silent one, which is the whole reason two cells aren't
// enough.
import { test } from '@playwright/test';

test('finish a job', async ({ page }) => {
  await page.goto('/');
  await page
    .locator('li.job')
    .filter({ hasText: '#103' })
    .getByRole('button', { name: 'Finish' })
    .click();
});
