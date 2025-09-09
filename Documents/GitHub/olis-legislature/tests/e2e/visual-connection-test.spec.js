const { test, expect } = require('@playwright/test');

test('Visual Connection Test - Enhanced UI Cohesion', async ({ page }) => {
  console.log('🚀 Testing enhanced visual connection between bill components...');
  
  // Step 1: Setup
  await page.goto('/');
  await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
  await page.selectOption('#session-selector', '2025R1');
  await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
  console.log('✅ OLIS setup complete');
  
  // Step 2: Click first bill details and verify visual enhancements
  console.log('👆 Clicking first bill Details toggle...');
  const firstContainer = page.locator('.hot-bill-container').first();
  const firstDetailsButton = firstContainer.locator('.details-toggle');
  const firstBillButton = firstContainer.locator('.hot-bill-button');
  
  await firstDetailsButton.click();
  await page.waitForTimeout(1000);
  
  // Step 3: Verify enhanced visual states
  console.log('🎨 Checking visual connection indicators...');
  
  // Container should be expanded with enhanced styling
  await expect(firstContainer).toHaveClass(/expanded/);
  console.log('✅ Container expanded with enhanced styling');
  
  // Toggle button should be active (primary color)
  await expect(firstDetailsButton).toHaveClass(/active/);
  console.log('✅ Details toggle button highlighted as active');
  
  // Bill button should be active
  await expect(firstBillButton).toHaveClass(/active/);
  console.log('✅ Bill button highlighted as active');
  
  // Details panel should be visible
  const detailsPanel = page.locator('.bill-details').first();
  await expect(detailsPanel).toBeVisible();
  console.log('✅ Details panel visible with connection styling');
  
  // Step 4: Test switching to verify proper state management
  const containerCount = await page.locator('.hot-bill-container').count();
  if (containerCount > 1) {
    console.log('🔄 Testing state switching...');
    const secondContainer = page.locator('.hot-bill-container').nth(1);
    const secondDetailsButton = secondContainer.locator('.details-toggle');
    
    await secondDetailsButton.click();
    await page.waitForTimeout(1000);
    
    // First components should no longer be active
    await expect(firstContainer).not.toHaveClass(/expanded/);
    await expect(firstDetailsButton).not.toHaveClass(/active/);
    await expect(firstBillButton).not.toHaveClass(/active/);
    console.log('✅ First bill components properly deactivated');
    
    // Second components should be active
    await expect(secondContainer).toHaveClass(/expanded/);
    await expect(secondDetailsButton).toHaveClass(/active/);
    console.log('✅ Second bill components properly activated');
  }
  
  // Step 5: Test closing detail
  console.log('🔄 Testing detail close...');
  const activeDetailsButton = page.locator('.details-toggle.active');
  await activeDetailsButton.click();
  await page.waitForTimeout(1000);
  
  // Verify all active states are removed
  const activeContainers = await page.locator('.hot-bill-container.expanded').count();
  const activeToggleButtons = await page.locator('.details-toggle.active').count();
  const activeBillButtons = await page.locator('.hot-bill-button.active').count();
  
  expect(activeContainers).toBe(0);
  expect(activeToggleButtons).toBe(0);
  expect(activeBillButtons).toBe(0);
  console.log('✅ All visual connection states properly reset');
  
  console.log('🎉 Enhanced visual connection working perfectly!');
  console.log('🎨 Users can now clearly see the cohesive relationship between bill, toggle, and details');
});