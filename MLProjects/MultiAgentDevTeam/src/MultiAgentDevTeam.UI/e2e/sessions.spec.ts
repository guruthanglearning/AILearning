import { test, expect } from '@playwright/test'

test.describe('Sessions Page', () => {
  test('loads sessions page', async ({ page }) => {
    await page.goto('/')
    await page.getByText('Past Sessions').click()
    await expect(page.locator('h1')).toContainText('Past Sessions')
  })

  test('shows empty or table state', async ({ page }) => {
    await page.goto('/')
    await page.getByText('Past Sessions').click()
    const noSessions = page.getByTestId('no-sessions')
    const table = page.getByTestId('sessions-table')
    await expect(noSessions.or(table)).toBeVisible({ timeout: 10000 })
  })
})
