const { test, expect } = require('@playwright/test');

test.describe('API Integration Tests', () => {
  test('should connect to OLIS API successfully', async ({ page }) => {
    await page.goto('/');
    
    // Intercept API calls to verify they're working
    const apiResponse = page.waitForResponse(response => 
      response.url().includes('/api/sessions') && response.status() === 200
    );
    
    await apiResponse;
    
    // Verify sessions are loaded in dropdown
    const optionCount = await page.locator('#session-selector option').count();
    expect(optionCount).toBeGreaterThanOrEqual(3);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('**/api/sessions**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    await page.goto('/');
    
    // Check that error is handled gracefully
    await expect(page.locator('#alert-container')).toBeVisible();
  });

  test('should load hot bills data from API', async ({ page }) => {
    await page.goto('/');
    
    // Select session and wait for hot bills API call
    const hotBillsResponse = page.waitForResponse(response => 
      response.url().includes('/hot-bills') && response.status() === 200
    );
    
    await page.selectOption('#session-selector', '2025R1');
    
    const response = await hotBillsResponse;
    const responseBody = await response.json();
    
    // Verify API returns expected structure
    expect(responseBody.success).toBe(true);
    expect(responseBody.data.hot_bills).toBeDefined();
    expect(Array.isArray(responseBody.data.hot_bills)).toBe(true);
    
    // Verify top submitters and behalf_of have max 5 items
    if (responseBody.data.hot_bills.length > 0) {
      const firstBill = responseBody.data.hot_bills[0];
      if (firstBill.top_submitters) {
        expect(firstBill.top_submitters.length).toBeLessThanOrEqual(5);
      }
      if (firstBill.top_behalf_of) {
        expect(firstBill.top_behalf_of.length).toBeLessThanOrEqual(5);
      }
    }
  });

  test('should handle session switching', async ({ page }) => {
    await page.goto('/');
    
    // Test switching between sessions
    await page.selectOption('#session-selector', '2025R1');
    await expect(page.locator('#session-name')).not.toContainText('Select a session', { timeout: 10000 });
    
    await page.selectOption('#session-selector', '2024R1');
    await expect(page.locator('#session-name')).not.toContainText('Loading statistics...', { timeout: 10000 });
    
    // Verify hot bills update for different sessions
    await expect(page.locator('#hot-bills-section')).toBeVisible();
  });
});