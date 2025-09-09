const { test, expect } = require('@playwright/test');

test('Full-Width Container Test - Bill and Details Expand Together', async ({ page }) => {
  console.log('🚀 Testing full-width bill container expansion...');
  
  // Step 1: Open the OLIS app
  console.log('📱 Opening OLIS application...');
  await page.goto('/');
  
  await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
  console.log('✅ OLIS App loaded');
  
  // Step 2: Select session and wait for hot bills
  console.log('🔗 Selecting session and loading hot bills...');
  await expect(page.locator('#session-selector')).toBeVisible();
  await page.selectOption('#session-selector', '2025R1');
  
  await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
  console.log('✅ Hot bills section loaded');
  
  // Step 3: Verify initial grid layout
  const hotBillContainers = page.locator('.hot-bill-container');
  const containerCount = await hotBillContainers.count();
  console.log(`📊 Found ${containerCount} hot bill containers`);
  
  // Step 4: Click first bill details and verify full-width expansion
  console.log('👆 Clicking first bill Details button...');
  const firstContainer = hotBillContainers.first();
  const firstDetailsButton = firstContainer.locator('.details-toggle');
  
  await firstDetailsButton.click();
  await page.waitForTimeout(1000);
  
  // Verify container has expanded class
  await expect(firstContainer).toHaveClass(/expanded/);
  console.log('✅ First container has expanded class');
  
  // Verify the container takes full width
  const expandedContainer = await firstContainer.boundingBox();
  const pageWidth = await page.viewportSize();
  expect(expandedContainer.width).toBeGreaterThan(pageWidth.width * 0.9);
  console.log(`✅ Container full-width: ${expandedContainer.width}px (viewport: ${pageWidth.width}px)`);
  
  // Step 5: Verify bill button is also full width
  const billButton = firstContainer.locator('.hot-bill-button');
  const buttonBox = await billButton.boundingBox();
  expect(buttonBox.width).toBeGreaterThan(pageWidth.width * 0.8);
  console.log(`✅ Bill button full-width: ${buttonBox.width}px`);
  
  // Step 6: Test switching to second bill
  if (containerCount > 1) {
    console.log('🔄 Testing switch to second bill...');
    const secondContainer = hotBillContainers.nth(1);
    const secondDetailsButton = secondContainer.locator('.details-toggle');
    
    await secondDetailsButton.click();
    await page.waitForTimeout(1000);
    
    // Verify first container collapsed, second expanded
    await expect(firstContainer).not.toHaveClass(/expanded/);
    await expect(secondContainer).toHaveClass(/expanded/);
    console.log('✅ Successfully switched: first collapsed, second expanded');
  }
  
  // Step 7: Test closing detail
  console.log('🔄 Testing detail close...');
  const activeContainer = page.locator('.hot-bill-container.expanded');
  const activeDetailsButton = activeContainer.locator('.details-toggle');
  
  await activeDetailsButton.click();
  await page.waitForTimeout(1000);
  
  // Verify no containers are expanded
  const expandedCount = await page.locator('.hot-bill-container.expanded').count();
  expect(expandedCount).toBe(0);
  console.log('✅ All containers back to normal grid layout');
  
  console.log('🎉 Full-width container expansion working perfectly!');
});