const { test, expect } = require('@playwright/test');

test('Visual Demo - Hot Bills UI Enhancement', async ({ page }) => {
  console.log('🚀 Starting VISUAL DEMO of Hot Bills UI enhancements...');
  
  // Step 1: Open the OLIS app
  console.log('📱 Opening OLIS application at http://localhost:8001...');
  await page.goto('/');
  
  // Wait longer to see the page load
  await page.waitForTimeout(2000);
  
  // Wait for the page to load
  await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
  console.log('✅ OLIS App loaded - you should see the main page');
  
  // Step 2: Select session
  console.log('🔗 Selecting 2025R1 session...');
  await expect(page.locator('#session-selector')).toBeVisible();
  await page.selectOption('#session-selector', '2025R1');
  
  // Wait to see session loading
  await page.waitForTimeout(3000);
  console.log('⏳ Waiting for hot bills to load...');
  
  // Wait for hot bills section
  await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
  console.log('✅ Hot bills section loaded - you should see hot bill buttons');
  
  // Step 3: Click first bill details
  console.log('👆 Clicking first hot bill Details button...');
  const firstDetailsButton = page.locator('.details-toggle').first();
  await firstDetailsButton.click();
  
  // Wait to see the detail view expand
  await page.waitForTimeout(2000);
  console.log('📖 First detail view should be expanded and FULL WIDTH');
  
  // Step 4: Click second bill details (should close first)
  console.log('🔄 Clicking second hot bill Details button...');
  const secondDetailsButton = page.locator('.details-toggle').nth(1);
  await secondDetailsButton.click();
  
  // Wait to see the switch
  await page.waitForTimeout(2000);
  console.log('✅ Second detail opened, first should be closed');
  
  // Step 5: Click same button to close
  console.log('🔄 Clicking same button to close detail...');
  await secondDetailsButton.click();
  
  // Wait to see it close
  await page.waitForTimeout(2000);
  console.log('✅ Detail closed, active highlight removed');
  
  console.log('🎉 Visual demo complete! You should have seen all UI enhancements working.');
});