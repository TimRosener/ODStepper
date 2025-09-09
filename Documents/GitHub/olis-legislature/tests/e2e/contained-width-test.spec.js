const { test, expect } = require('@playwright/test');

test('Contained Width Test - Expansion within Main Content Area', async ({ page }) => {
  console.log('🚀 Testing contained width expansion within main content...');
  
  // Step 1: Open the OLIS app
  await page.goto('/');
  await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
  console.log('✅ OLIS App loaded');
  
  // Step 2: Select session and wait for hot bills
  await expect(page.locator('#session-selector')).toBeVisible();
  await page.selectOption('#session-selector', '2025R1');
  await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
  console.log('✅ Hot bills section loaded');
  
  // Step 3: Get main content area dimensions for comparison
  const mainContent = page.locator('.main-content');
  const mainContentBox = await mainContent.boundingBox();
  console.log(`📏 Main content area width: ${mainContentBox.width}px`);
  
  // Step 4: Click first bill details and verify contained expansion
  console.log('👆 Clicking first bill Details button...');
  const firstContainer = page.locator('.hot-bill-container').first();
  const firstDetailsButton = firstContainer.locator('.details-toggle');
  
  await firstDetailsButton.click();
  await page.waitForTimeout(1000);
  
  // Step 5: Verify container expansion is contained within main content
  const expandedContainer = await firstContainer.boundingBox();
  console.log(`📏 Expanded container width: ${expandedContainer.width}px`);
  
  // The container should be close to main content width but not exceed it significantly
  expect(expandedContainer.width).toBeLessThanOrEqual(mainContentBox.width + 20); // Allow 20px tolerance
  expect(expandedContainer.width).toBeGreaterThan(mainContentBox.width * 0.9); // At least 90% of main content
  console.log('✅ Container properly contained within main content area');
  
  // Step 6: Verify bill button width
  const billButton = firstContainer.locator('.hot-bill-button');
  const buttonBox = await billButton.boundingBox();
  console.log(`📏 Bill button width: ${buttonBox.width}px`);
  
  // Button should also be contained properly
  expect(buttonBox.width).toBeLessThanOrEqual(mainContentBox.width);
  expect(buttonBox.width).toBeGreaterThan(mainContentBox.width * 0.85);
  console.log('✅ Bill button properly sized within container');
  
  // Step 7: Verify details panel width
  const detailsPanel = page.locator('.bill-details').first();
  const detailsBox = await detailsPanel.boundingBox();
  console.log(`📏 Details panel width: ${detailsBox.width}px`);
  
  // Details should match container width
  expect(detailsBox.width).toBeLessThanOrEqual(expandedContainer.width + 10);
  expect(detailsBox.width).toBeGreaterThan(expandedContainer.width * 0.9);
  console.log('✅ Details panel properly sized within container');
  
  console.log('🎉 Contained width expansion working perfectly!');
});