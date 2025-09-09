const { test, expect } = require('@playwright/test');

test('Scroll Demo - Auto-scroll on Details Open', async ({ page }) => {
  console.log('🚀 Demonstrating auto-scroll behavior...');
  
  // Step 1: Setup
  await page.goto('/');
  await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
  await page.selectOption('#session-selector', '2025R1');
  await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
  console.log('✅ OLIS setup complete');
  
  // Step 2: Scroll down as much as the page allows
  console.log('📜 Scrolling down to bottom of page...');
  await page.evaluate(() => {
    window.scrollTo(0, document.body.scrollHeight);
  });
  
  await page.waitForTimeout(1000);
  const initialScrollY = await page.evaluate(() => window.scrollY);
  console.log(`📍 Scrolled to position: ${initialScrollY}px`);
  
  // Step 3: Click first hot bill details button
  console.log('👆 Clicking first hot bill Details button...');
  const firstContainer = page.locator('.hot-bill-container').first();
  const firstDetailsButton = firstContainer.locator('.details-toggle');
  
  await firstDetailsButton.click();
  console.log('⏳ Auto-scroll should now bring the container to the top...');
  
  // Wait for scroll animation
  await page.waitForTimeout(2000);
  
  // Step 4: Verify the container is now near the top
  const containerBox = await firstContainer.boundingBox();
  console.log(`📍 Container now at: ${containerBox.y}px from top of viewport`);
  
  // The container should be visible and near the top
  expect(containerBox.y).toBeGreaterThanOrEqual(0);
  expect(containerBox.y).toBeLessThan(300); // Within top 300px is reasonable
  
  console.log('✅ Auto-scroll working - container is now at the top!');
  
  // Step 5: Verify details are expanded
  await expect(firstContainer).toHaveClass(/expanded/);
  const detailsPanel = page.locator('.bill-details').first();
  await expect(detailsPanel).toBeVisible();
  console.log('✅ Details properly expanded and visible');
  
  console.log('🎉 Auto-scroll demonstration complete!');
  console.log('💡 Users will now see the full expanded bill without needing to scroll');
});