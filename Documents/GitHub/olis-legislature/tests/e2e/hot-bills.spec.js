const { test, expect } = require('@playwright/test');

test.describe('Hot Bills Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the app to load
    await expect(page.locator('#session-selector')).toBeVisible();
  });

  test('should display Top 5 lists without testimonies word', async ({ page }) => {
    // Select a session
    await page.selectOption('#session-selector', '2025R1');
    
    // Wait for hot bills to load
    await expect(page.locator('#hot-bills-section')).toBeVisible();
    
    // Click on the first hot bill details button
    const firstHotBill = page.locator('.hot-bill-button').first();
    await expect(firstHotBill).toBeVisible();
    
    const detailsButton = firstHotBill.locator('button:has-text("Details")');
    await detailsButton.click();
    
    // Wait for details to expand
    await expect(page.locator('.bill-details')).toBeVisible();
    
    // Verify Top 5 headers are present
    await expect(page.locator('h4:has-text("🏙️ Top 5 Cities/Locations")')).toBeVisible();
    await expect(page.locator('h4:has-text("🏛️ Top 5 On Behalf Of")')).toBeVisible();
    
    // Verify no "testimonies" word appears in the lists
    const detailsContent = await page.locator('.bill-details').textContent();
    expect(detailsContent).not.toContain('testimonies');
    
    // Verify we have exactly 5 or fewer items in each list
    const cityItems = await page.locator('.top-submitters-list li').count();
    const behalfItems = await page.locator('.top-behalf-of-list li').count();
    
    expect(cityItems).toBeLessThanOrEqual(5);
    expect(behalfItems).toBeLessThanOrEqual(5);
    
    // Verify format: should show numbers without "testimonies" word
    const firstCityItem = await page.locator('.top-submitters-list li').first().textContent();
    expect(firstCityItem).toMatch(/.*\(\d+\)$/); // Should end with (number)
    expect(firstCityItem).not.toContain('testimonies');
  });

  test('should load hot bills for different sessions', async ({ page }) => {
    // Test 2025R1
    await page.selectOption('#session-selector', '2025R1');
    await expect(page.locator('#hot-bills-section')).toBeVisible();
    let billCount = await page.locator('.hot-bill-button').count();
    expect(billCount).toBeGreaterThan(0);
    
    // Test 2024R1
    await page.selectOption('#session-selector', '2024R1');
    await expect(page.locator('#hot-bills-section')).toBeVisible();
    billCount = await page.locator('.hot-bill-button').count();
    expect(billCount).toBeGreaterThan(0);
  });

  test('should display position breakdowns correctly', async ({ page }) => {
    await page.selectOption('#session-selector', '2025R1');
    await expect(page.locator('#hot-bills-section')).toBeVisible();
    
    const firstHotBill = page.locator('.hot-bill-button').first();
    const detailsButton = firstHotBill.locator('button:has-text("Details")');
    await detailsButton.click();
    
    // Check for position breakdown section
    await expect(page.locator('.position-breakdown')).toBeVisible();
    
    // Verify position categories are present
    await expect(page.locator(':text("In Favor")')).toBeVisible();
    await expect(page.locator(':text("Against")')).toBeVisible();
    await expect(page.locator(':text("Neutral")')).toBeVisible();
  });
});