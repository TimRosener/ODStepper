const { test, expect } = require('@playwright/test');

test.describe('Manual Interaction Test - Hot Bills Detail View', () => {
  test('should open app and interact with hot bills detail view', async ({ page }) => {
    console.log('🚀 Starting OLIS app interaction test...');
    
    // Step 1: Open the app
    console.log('📱 Opening OLIS application...');
    await page.goto('/');
    
    // Wait for the page to load
    await expect(page.locator('h1:has-text("Oregon Legislative Information System")')).toBeVisible();
    console.log('✅ App loaded successfully');
    
    // Step 2: Check connection status
    console.log('🔗 Checking connection status...');
    await expect(page.locator('#connection-status')).toBeVisible();
    await expect(page.locator('#session-selector')).toBeVisible();
    
    // Wait for sessions to load
    await page.waitForTimeout(2000);
    console.log('✅ Connection established');
    
    // Step 3: Select a session to load hot bills
    console.log('📋 Selecting legislative session (2025R1)...');
    await page.selectOption('#session-selector', '2025R1');
    
    // Wait for hot bills section to appear
    await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
    console.log('✅ Hot bills section loaded');
    
    // Step 4: Verify hot bills are present
    const hotBillButtons = page.locator('.hot-bill-button');
    const hotBillCount = await hotBillButtons.count();
    console.log(`📊 Found ${hotBillCount} hot bills`);
    
    expect(hotBillCount).toBeGreaterThan(0);
    
    // Step 5: Get the first hot bill and extract info
    const firstHotBill = hotBillButtons.first();
    await expect(firstHotBill).toBeVisible();
    
    // Extract bill information from the hot bill button
    const billId = await firstHotBill.locator('.bill-label').textContent();
    const billTitle = await firstHotBill.locator('.bill-title').textContent();
    const heatEmoji = await firstHotBill.locator('.heat-indicator').textContent();
    
    console.log(`🔥 First Hot Bill Details:`);
    console.log(`   Bill ID: ${billId}`);
    console.log(`   Title: ${billTitle}`);
    console.log(`   Heat Level: ${heatEmoji}`);
    
    // Step 6: Click the Details toggle button (it's separate from the hot-bill-button)
    console.log('👆 Clicking Details toggle button...');
    const firstHotBillContainer = page.locator('.hot-bill-container').first();
    const detailsButton = firstHotBillContainer.locator('.details-toggle');
    await expect(detailsButton).toBeVisible();
    await detailsButton.click();
    
    // Step 7: Wait for detail view to expand (target the first one specifically)
    console.log('📖 Waiting for detail view to expand...');
    const billDetails = page.locator('.bill-details').first();
    await expect(billDetails).toBeVisible({ timeout: 10000 });
    console.log('✅ Detail view expanded');
    
    // Step 8: Verify Top 5 sections are present
    console.log('🏙️ Checking Top 5 Cities/Locations section...');
    await expect(page.locator('h4:has-text("🏙️ Top 5 Cities/Locations")')).toBeVisible();
    
    console.log('🏛️ Checking Top 5 On Behalf Of section...');
    await expect(page.locator('h4:has-text("🏛️ Top 5 On Behalf Of")')).toBeVisible();
    
    // Step 9: Verify our changes - no "testimonies" word
    console.log('🔍 Verifying no "testimonies" word appears...');
    const detailsContent = await billDetails.textContent();
    expect(detailsContent).not.toContain('testimonies');
    console.log('✅ Confirmed: "testimonies" word removed successfully');
    
    // Step 10: Count items in Top 5 lists
    const cityItems = await page.locator('.top-submitters-list li').count();
    const behalfItems = await page.locator('.top-behalf-of-list li').count();
    
    console.log(`📊 Top 5 Lists Verification:`);
    console.log(`   Cities/Locations: ${cityItems} items`);
    console.log(`   On Behalf Of: ${behalfItems} items`);
    
    expect(cityItems).toBeLessThanOrEqual(5);
    expect(behalfItems).toBeLessThanOrEqual(5);
    console.log('✅ Confirmed: Lists limited to 5 items each');
    
    // Step 11: Check position breakdown section
    console.log('📈 Checking position breakdown...');
    await expect(page.locator('.position-breakdown')).toBeVisible();
    
    // Verify position categories
    await expect(page.locator('text=In Favor')).toBeVisible();
    await expect(page.locator('text=Against')).toBeVisible();
    await expect(page.locator('text=Neutral')).toBeVisible();
    console.log('✅ Position breakdown sections verified');
    
    // Step 12: Extract some actual data to show
    console.log('📋 Extracting detail view data...');
    
    const topCities = await page.locator('.top-submitters-list li').allTextContents();
    const topBehalf = await page.locator('.top-behalf-of-list li').allTextContents();
    
    console.log('🏙️ Top Cities/Locations:');
    topCities.forEach((city, index) => {
      console.log(`   ${index + 1}. ${city.trim()}`);
    });
    
    console.log('🏛️ Top On Behalf Of:');
    topBehalf.forEach((behalf, index) => {
      console.log(`   ${index + 1}. ${behalf.trim()}`);
    });
    
    // Step 13: Take a screenshot for verification
    console.log('📸 Taking screenshot of detail view...');
    await page.screenshot({ 
      path: 'tests/screenshots/hot-bills-detail-view.png',
      fullPage: true 
    });
    console.log('✅ Screenshot saved to tests/screenshots/hot-bills-detail-view.png');
    
    // Step 14: Final success message
    console.log('🎉 Test completed successfully!');
    console.log('✅ All interactions with hot bills detail view verified');
  });
});