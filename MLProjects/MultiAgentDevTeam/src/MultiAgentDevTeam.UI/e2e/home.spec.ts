import { test, expect } from '@playwright/test'

test.describe('Home Page', () => {
  test('has title', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/MultiAgent/)
  })

  test('shows requirement textarea', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByTestId('requirement-input')).toBeVisible()
  })

  test('shows submit button', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByTestId('submit-btn')).toBeVisible()
  })

  test('shows validation error on empty submit', async ({ page }) => {
    await page.goto('/')
    await page.getByTestId('pipeline-form').evaluate(f => (f as HTMLFormElement).dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
    await expect(page.getByTestId('validation-error')).toBeVisible()
    await expect(page.getByTestId('validation-error')).toContainText('Requirement is required')
  })

  test('shows validation error for short requirement', async ({ page }) => {
    await page.goto('/')
    await page.getByTestId('requirement-input').fill('short')
    await page.getByTestId('pipeline-form').evaluate(f => (f as HTMLFormElement).dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
    await expect(page.getByTestId('validation-error')).toContainText('at least 10 characters')
  })

  test('navigates to sessions page', async ({ page }) => {
    await page.goto('/')
    await page.getByText('Past Sessions').click()
    await expect(page.getByTestId('no-sessions').or(page.getByTestId('sessions-table'))).toBeVisible({ timeout: 10000 })
  })
})
