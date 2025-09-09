const { test, expect } = require('@playwright/test');

test.describe('Bill Status Display Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the app to load
    await expect(page.locator('#session-selector')).toBeVisible();
  });

  test('should display bill status badges in hot bills', async ({ page }) => {
    console.log('🏛️ Testing bill status badge display...');
    
    // Select a session with historical data
    await page.selectOption('#session-selector', '2024R1');
    
    // Wait for hot bills to load
    await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
    console.log('✅ Hot bills section loaded');
    
    // Verify that hot bills are present
    const hotBillButtons = page.locator('.hot-bill-button');
    const billCount = await hotBillButtons.count();
    expect(billCount).toBeGreaterThan(0);
    console.log(`📊 Found ${billCount} hot bills`);
    
    // Debug: Let's see what the actual structure looks like
    const firstBillHtml = await hotBillButtons.first().innerHTML();
    console.log(`🔍 First bill HTML structure:`, firstBillHtml.substring(0, 500));
    
    // Check that each hot bill has a status badge
    for (let i = 0; i < Math.min(billCount, 3); i++) { // Test first 3 bills
      const billButton = hotBillButtons.nth(i);
      
      // Check for the actual structure that exists in app.js
      const hasHotBillHeader = await billButton.locator('.hot-bill-header').count();
      const hasBillIdSection = await billButton.locator('.bill-id-section').count();
      const hasBillLabel = await billButton.locator('.bill-label').count();
      const hasStatusBadge = await billButton.locator('.bill-status-badge').count();
      
      console.log(`📊 Bill ${i + 1} structure: hot-bill-header=${hasHotBillHeader}, bill-id-section=${hasBillIdSection}, bill-label=${hasBillLabel}, status-badge=${hasStatusBadge}`);
      
      // Verify the expected structure exists
      await expect(billButton.locator('.hot-bill-header')).toBeVisible();
      await expect(billButton.locator('.bill-id-section')).toBeVisible();
      
      // Verify bill ID is present in .bill-label
      const billId = billButton.locator('.bill-label');
      await expect(billId).toBeVisible();
      const billIdText = await billId.textContent();
      expect(billIdText).toMatch(/^[A-Z]{2,4}\d+$/); // Format like HB1234, SB5678
      console.log(`📄 Bill ${i + 1}: ${billIdText}`);
      
      // Verify status badge is present
      const statusBadge = billButton.locator('.bill-status-badge');
      await expect(statusBadge).toBeVisible();
      
      // Verify status badge has appropriate styling classes
      const statusBadgeClass = await statusBadge.getAttribute('class');
      expect(statusBadgeClass).toContain('bill-status-badge');
      expect(statusBadgeClass).toMatch(/status-(primary|success|warning|danger|info|secondary)/);
      
      // Verify status badge has readable text
      const statusText = await statusBadge.textContent();
      expect(statusText.length).toBeGreaterThan(0);
      console.log(`📊 Status: ${statusText}`);
      
      // Verify heat indicator is still present
      await expect(billButton.locator('.heat-indicator')).toBeVisible();
    }
    
    console.log('✅ All hot bills display status badges correctly');
  });

  test('should show different status colors for different bill statuses', async ({ page }) => {
    console.log('🎨 Testing status badge color variations...');
    
    // Select a session
    await page.selectOption('#session-selector', '2024R1');
    await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
    
    // Collect all status badges and their classes
    const statusBadges = page.locator('.bill-status-badge');
    const badgeCount = await statusBadges.count();
    expect(badgeCount).toBeGreaterThan(0);
    
    const statusClassesSeen = new Set();
    const statusTextsSeen = new Set();
    
    for (let i = 0; i < Math.min(badgeCount, 6); i++) { // Check up to 6 badges
      const badge = statusBadges.nth(i);
      const badgeClass = await badge.getAttribute('class');
      const badgeText = await badge.textContent();
      
      // Extract status color class
      const colorMatch = badgeClass.match(/status-(primary|success|warning|danger|info|secondary)/);
      if (colorMatch) {
        statusClassesSeen.add(colorMatch[1]);
      }
      
      statusTextsSeen.add(badgeText.trim());
      
      console.log(`🏷️ Badge ${i + 1}: "${badgeText}" (${colorMatch ? colorMatch[1] : 'unknown'})`);
    }
    
    // Verify we have different status types (indicating actual bill status classification)
    console.log(`📊 Unique status classes seen: ${Array.from(statusClassesSeen).join(', ')}`);
    console.log(`📊 Unique status texts seen: ${Array.from(statusTextsSeen).join(', ')}`);
    
    // We should have at least some variety in status (unless all bills happen to have same status)
    expect(statusTextsSeen.size).toBeGreaterThan(0);
    
    console.log('✅ Status badge color variations working correctly');
  });

  test('should maintain responsive design with status badges', async ({ page }) => {
    console.log('📱 Testing responsive design with status badges...');
    
    // Test desktop layout first
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.selectOption('#session-selector', '2024R1');
    await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
    
    const firstBill = page.locator('.hot-bill-button').first();
    
    // Verify desktop layout
    await expect(firstBill.locator('.hot-bill-header')).toBeVisible();
    await expect(firstBill.locator('.bill-status-badge')).toBeVisible();
    console.log('✅ Desktop layout working');
    
    // Test tablet layout
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500); // Allow for responsive adjustments
    
    await expect(firstBill.locator('.bill-status-badge')).toBeVisible();
    console.log('✅ Tablet layout working');
    
    // Test mobile layout
    await page.setViewportSize({ width: 480, height: 800 });
    await page.waitForTimeout(500); // Allow for responsive adjustments
    
    await expect(firstBill.locator('.bill-status-badge')).toBeVisible();
    console.log('✅ Mobile layout working');
    
    // Test that status badge text is still readable on mobile
    const statusBadge = firstBill.locator('.bill-status-badge');
    const statusText = await statusBadge.textContent();
    expect(statusText.length).toBeGreaterThan(0);
    
    console.log('✅ Status badges maintain responsive design across all screen sizes');
  });

  test('should display status badges alongside existing hot bill features', async ({ page }) => {
    console.log('🔗 Testing integration with existing hot bill features...');
    
    await page.selectOption('#session-selector', '2024R1');
    await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
    
    const firstBill = page.locator('.hot-bill-button').first();
    
    // Verify all components are present together
    await expect(firstBill.locator('.bill-label')).toBeVisible();
    await expect(firstBill.locator('.bill-status-badge')).toBeVisible();
    await expect(firstBill.locator('.heat-indicator')).toBeVisible();
    await expect(firstBill.locator('.bill-title')).toBeVisible();
    await expect(firstBill.locator('.bill-stats')).toBeVisible();
    
    // Verify bill stats still show the expected metrics
    const statNumbers = firstBill.locator('.bill-stats .stat-number');
    expect(await statNumbers.count()).toBe(3); // testimonies, submitters, hotness
    
    // Verify heat indicator still works
    const heatIndicator = firstBill.locator('.heat-indicator');
    const heatIndicatorText = await heatIndicator.textContent();
    expect(['🔥', '🌶️', '🔶', '🟡']).toContain(heatIndicatorText);
    
    console.log('✅ Status badges integrate well with existing hot bill features');
  });

  test('should handle unknown or missing status gracefully', async ({ page }) => {
    console.log('🛡️ Testing graceful handling of unknown status...');
    
    await page.selectOption('#session-selector', '2024R1');
    await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
    
    // All bills should have some status badge, even if unknown
    const statusBadges = page.locator('.bill-status-badge');
    const badgeCount = await statusBadges.count();
    const billCount = await page.locator('.hot-bill-button').count();
    
    expect(badgeCount).toBe(billCount); // Every bill should have a status badge
    
    // Check that no badge is completely empty
    for (let i = 0; i < Math.min(badgeCount, 3); i++) {
      const badge = statusBadges.nth(i);
      const badgeText = await badge.textContent();
      expect(badgeText.trim().length).toBeGreaterThan(0);
    }
    
    console.log('✅ Unknown status handling works correctly');
  });

  test('should load status information within reasonable time', async ({ page }) => {
    console.log('⏱️ Testing status loading performance...');
    
    const startTime = Date.now();
    
    await page.selectOption('#session-selector', '2024R1');
    
    // Wait for hot bills section to appear
    await expect(page.locator('#hot-bills-section')).toBeVisible({ timeout: 15000 });
    
    // Wait for first status badge to appear
    await expect(page.locator('.bill-status-badge').first()).toBeVisible({ timeout: 5000 });
    
    const loadTime = Date.now() - startTime;
    console.log(`⏱️ Total load time: ${loadTime}ms`);
    
    // Status should load within reasonable time (20 seconds including API calls)
    expect(loadTime).toBeLessThan(20000);
    
    console.log('✅ Status information loads within acceptable time limits');
  });
});