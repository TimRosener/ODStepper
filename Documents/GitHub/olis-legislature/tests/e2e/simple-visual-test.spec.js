const { test, expect } = require('@playwright/test');

test('Simple Visual Test - Should open browser visibly', async ({ page }) => {
  console.log('🚀 Starting VISUAL test...');
  
  // Open a simple page
  console.log('📱 Opening Google...');
  await page.goto('https://www.google.com');
  
  // Wait 3 seconds so you can see the browser
  console.log('⏱️ Waiting 3 seconds - YOU SHOULD SEE A BROWSER WINDOW NOW');
  await page.waitForTimeout(3000);
  
  // Check for Google search box
  await expect(page.locator('input[name="q"]')).toBeVisible();
  console.log('✅ Google loaded successfully - browser should be visible');
  
  // Wait another 2 seconds
  await page.waitForTimeout(2000);
  
  console.log('🎉 Visual test complete!');
});