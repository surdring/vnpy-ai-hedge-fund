import { test, expect } from '@playwright/test';

test.describe('Frontend Smoke Tests', () => {
  test('homepage loads', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await expect(page).toHaveTitle(/AI Hedge Fund/);
  });

  test('workflow editor renders', async ({ page }) => {
    await page.goto('http://localhost:5173');
    // Check that React Flow canvas is present
    const canvas = page.locator('.react-flow');
    await expect(canvas).toBeVisible({ timeout: 10000 });
  });

  test('navigation works', async ({ page }) => {
    await page.goto('http://localhost:5173');
    // Check sidebar navigation exists
    const sidebar = page.locator('[data-sidebar]');
    await expect(sidebar).toBeVisible({ timeout: 10000 });
  });
});