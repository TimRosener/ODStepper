const { test, expect } = require('@playwright/test');

test.describe('Hot Bills UI Enhancement Test', () => {
  test('should display full-width details, highlight active bill, and allow only one detail open', async ({ page }) => {
    console.log('🚀 Testing Hot Bills UI enhancements...');
    
    // Step 1: Open the app
    console.log('📱 Opening OLIS application...');
    await page.goto('/');
    
    // Wait for the page to load
    await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
    console.log('✅ App loaded successfully');
    
    // Step 2: Check connection and select session
    console.log('🔗 Checking connection and selecting session...');
    await expect(page.locator('#connection-status')).toBeVisible();
    await expect(page.locator('#session-selector')).toBeVisible();
    
    // Wait for sessions to load
    await page.waitForTimeout(2000);
    await page.selectOption('#session-selector', '2025R1');
    
    // Wait for hot bills section to appear
    await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
    console.log('✅ Hot bills section loaded');
    
    // Step 3: Verify we have hot bills
    const hotBillButtons = page.locator('.hot-bill-button');
    const hotBillCount = await hotBillButtons.count();
    console.log(`📊 Found ${hotBillCount} hot bills`);
    expect(hotBillCount).toBeGreaterThan(0);
    
    // Step 4: Test clicking first bill details toggle
    console.log('👆 Testing first bill detail toggle...');
    const firstBillContainer = page.locator('.hot-bill-container').first();
    const firstDetailsButton = firstBillContainer.locator('.details-toggle');
    const firstHotBillButton = firstBillContainer.locator('.hot-bill-button');
    
    await expect(firstDetailsButton).toBeVisible();
    await firstDetailsButton.click();
    
    // Step 5: Verify first detail view opens and bill gets highlighted
    console.log('📖 Verifying first detail view opens...');
    const firstBillDetails = page.locator('.bill-details').first();
    await expect(firstBillDetails).toBeVisible({ timeout: 10000 });
    
    // Check if the bill button has active class
    await expect(firstHotBillButton).toHaveClass(/active/);
    console.log('✅ First bill highlighted with active state');
    
    // Step 6: Verify full-width detail view
    console.log('📏 Checking if detail view uses full width...');
    const detailsWidth = await firstBillDetails.boundingBox();
    const pageWidth = await page.viewportSize();
    
    // The detail should be significantly wider than a contained element
    // (allowing some margin for scrollbars, etc.)
    expect(detailsWidth.width).toBeGreaterThan(pageWidth.width * 0.8);
    console.log(`✅ Detail view width: ${detailsWidth.width}px (viewport: ${pageWidth.width}px)`);
    
    // Step 7: Test that only one detail can be open at a time
    if (hotBillCount > 1) {
      console.log('🔄 Testing single detail view constraint...');
      const secondBillContainer = page.locator('.hot-bill-container').nth(1);
      const secondDetailsButton = secondBillContainer.locator('.details-toggle');
      const secondHotBillButton = secondBillContainer.locator('.hot-bill-button');
      
      await secondDetailsButton.click();
      
      // Wait a moment for the transition
      await page.waitForTimeout(500);
      
      // Verify first detail is now hidden and first bill is no longer active
      await expect(firstBillDetails).not.toBeVisible();
      await expect(firstHotBillButton).not.toHaveClass(/active/);
      console.log('✅ First detail closed when second opened');
      
      // Verify second detail is visible and second bill is active
      const secondBillDetails = page.locator('.bill-details').nth(1);
      await expect(secondBillDetails).toBeVisible();
      await expect(secondHotBillButton).toHaveClass(/active/);
      console.log('✅ Second bill highlighted and detail opened');
      
      // Step 8: Test closing the detail by clicking toggle again
      console.log('🔄 Testing detail close functionality...');
      await secondDetailsButton.click();
      
      await page.waitForTimeout(500);
      await expect(secondBillDetails).not.toBeVisible();
      await expect(secondHotBillButton).not.toHaveClass(/active/);
      console.log('✅ Detail closed and active state removed');
    }
    
    // Step 9: Take a screenshot for verification
    console.log('📸 Taking screenshot...');
    await page.screenshot({ 
      path: 'tests/screenshots/hot-bills-ui-enhancement.png',
      fullPage: true 
    });
    
    console.log('🎉 All UI enhancements working correctly!');
  });
});