const { test, expect } = require('@playwright/test');

test.describe('Navigation and Core Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the main dashboard', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/OLIS/);
    
    // Check main elements are visible
    await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
    await expect(page.locator('#session-selector')).toBeVisible();
    await expect(page.locator('#connection-status')).toBeVisible();
  });

  test('should navigate through sidebar menu', async ({ page }) => {
    // Test Session Overview
    await page.click('a[href="/"]');
    await expect(page.locator('#main-dashboard')).toBeVisible();
    
    // Test System Health
    await page.click('a[href="/system-health"]');
    await expect(page.url()).toContain('/system-health');
    
    // Test Design Library
    await page.click('a[href="/examples"]');
    await expect(page.url()).toContain('/examples');
    
    // Test Admin Panel
    await page.click('a[href="/admin"]');
    await expect(page.url()).toContain('/admin');
  });

  test('should show session information when selected', async ({ page }) => {
    // Select a session
    await page.selectOption('#session-selector', '2025R1');
    
    // Wait for session data to load
    await expect(page.locator('#session-name')).not.toHaveText('Select a session to view bill categories');
    await expect(page.locator('#total-bills-count')).not.toHaveText('-');
    
    // Check that hot bills section appears
    await expect(page.locator('#hot-bills-section')).toBeVisible();
  });

  test('should display connection status', async ({ page }) => {
    // Wait for connection status to be established
    await expect(page.locator('#connection-status')).toBeVisible();
    
    // Should eventually show connected status (not pending)
    await expect(page.locator('#connection-text')).not.toHaveText('Connecting to OLIS...', { timeout: 10000 });
  });

  test('should be responsive on mobile', async ({ page, isMobile }) => {
    if (isMobile) {
      // Test that sidebar is hidden on mobile initially
      await expect(page.locator('.sidebar')).toHaveCSS('transform', 'matrix(1, 0, 0, 1, -280, 0)');
      
      // Test main content is visible
      await expect(page.locator('.main-content')).toBeVisible();
    }
  });
});