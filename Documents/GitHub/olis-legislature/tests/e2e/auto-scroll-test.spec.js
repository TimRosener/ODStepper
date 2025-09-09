const { test, expect } = require('@playwright/test');

test('Auto-Scroll Test - Container Scrolls to Top on Details Open', async ({ page }) => {
  console.log('🚀 Testing auto-scroll behavior when opening details...');
  
  // Step 1: Setup
  await page.goto('/');
  await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
  await page.selectOption('#session-selector', '2025R1');
  await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
  console.log('✅ OLIS setup complete');
  
  // Step 2: Scroll down to simulate user having scrolled past hot bills
  console.log('📜 Scrolling down to simulate user position...');
  await page.evaluate(() => {
    window.scrollTo(0, 800); // Scroll down 800px
  });
  
  // Wait a moment for scroll to complete
  await page.waitForTimeout(500);
  
  // Verify we're scrolled down
  const initialScrollY = await page.evaluate(() => window.scrollY);
  expect(initialScrollY).toBeGreaterThan(500);
  console.log(`✅ Scrolled down to position: ${initialScrollY}px`);
  
  // Step 3: Click a hot bill details button
  console.log('👆 Clicking hot bill Details button (should auto-scroll)...');
  const firstContainer = page.locator('.hot-bill-container').first();
  const firstDetailsButton = firstContainer.locator('.details-toggle');
  
  await firstDetailsButton.click();
  
  // Step 4: Wait for auto-scroll to complete and verify position
  console.log('⏳ Waiting for auto-scroll to complete...');
  await page.waitForTimeout(2000); // Wait for smooth scroll animation
  
  // Check if the hot bill container is now near the top of the viewport
  const containerBox = await firstContainer.boundingBox();
  const viewportHeight = await page.viewportSize();
  
  // The container should be near the top of the viewport (allowing some margin for headers)
  expect(containerBox.y).toBeLessThan(200); // Should be within top 200px
  console.log(`✅ Container positioned at: ${containerBox.y}px from top`);
  
  // Step 5: Verify the details are visible and expanded
  await expect(firstContainer).toHaveClass(/expanded/);
  const detailsPanel = page.locator('.bill-details').first();
  await expect(detailsPanel).toBeVisible();
  console.log('✅ Details properly expanded and visible');
  
  // Step 6: Test with a different bill (if available) to ensure consistent behavior
  const containerCount = await page.locator('.hot-bill-container').count();
  if (containerCount > 1) {
    console.log('🔄 Testing auto-scroll with second bill...');
    
    // Scroll down again
    await page.evaluate(() => {
      window.scrollTo(0, 1000);
    });
    await page.waitForTimeout(500);
    
    // Click second bill
    const secondContainer = page.locator('.hot-bill-container').nth(1);
    const secondDetailsButton = secondContainer.locator('.details-toggle');
    await secondDetailsButton.click();
    
    // Wait for scroll and verify
    await page.waitForTimeout(2000);
    const secondContainerBox = await secondContainer.boundingBox();
    expect(secondContainerBox.y).toBeLessThan(200);
    console.log(`✅ Second container also positioned correctly: ${secondContainerBox.y}px from top`);
  }
  
  console.log('🎉 Auto-scroll functionality working perfectly!');
  console.log('📱 Users no longer need to manually scroll after opening details');
});