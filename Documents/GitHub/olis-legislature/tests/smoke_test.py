#!/usr/bin/env python3
"""
Quick smoke test script for OLIS critical features

This is the automated version of the smoke test checklist from CRITICAL_FEATURES.md.
Run this before and after making changes to verify critical functionality.
"""

import asyncio
import httpx
import sys
from datetime import datetime


async def run_smoke_tests():
    """Run the quick smoke test checklist"""
    
    print("🔍 OLIS Critical Features Smoke Test")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    base_url = "http://localhost:8001"
    timeout = 10.0
    
    # Test results
    tests = []
    
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
            
            # Test 1: Check if server is running
            print("1️⃣  Testing server health...")
            try:
                response = await client.get("/health")
                if response.status_code == 200 and response.json().get("status") == "healthy":
                    tests.append(("✅", "Server health check"))
                    print("   ✅ Server is running")
                else:
                    tests.append(("❌", f"Server health check (status: {response.status_code})"))
                    print("   ❌ Server health check failed")
            except Exception as e:
                tests.append(("❌", f"Server health check (error: {str(e)})"))
                print("   ❌ Server is not running or not responding")
            
            # Test 2: Check sessions load
            print("\n2️⃣  Testing sessions API...")
            try:
                response = await client.get("/api/sessions")
                if response.status_code == 200:
                    sessions = response.json()
                    if sessions and len(sessions) > 0:
                        tests.append(("✅", f"Sessions API ({len(sessions)} sessions found)"))
                        print(f"   ✅ Found {len(sessions)} legislative sessions")
                    else:
                        tests.append(("⚠️", "Sessions API (no sessions found)"))
                        print("   ⚠️  Sessions API works but no sessions found")
                else:
                    tests.append(("❌", f"Sessions API (status: {response.status_code})"))
                    print("   ❌ Sessions API failed")
            except Exception as e:
                tests.append(("❌", f"Sessions API (error: {str(e)})"))
                print("   ❌ Sessions API error")
            
            # Test 3: Check hot bills with position data
            print("\n3️⃣  Testing hot bills with position breakdowns...")
            try:
                response = await client.get("/api/sessions/2025R1/hot-bills?limit=2")
                if response.status_code == 200:
                    data = response.json()
                    hot_bills = data.get("hot_bills", [])
                    
                    if hot_bills:
                        # Check if position breakdown exists and has data
                        first_bill = hot_bills[0]
                        position_breakdown = first_bill.get("position_breakdown", {})
                        
                        if position_breakdown:
                            # Check if we have proper position mapping (not all unknown)
                            total_known = (position_breakdown.get("in_favor", 0) + 
                                         position_breakdown.get("against", 0) + 
                                         position_breakdown.get("neutral", 0))
                            total_unknown = position_breakdown.get("unknown", 0)
                            
                            if total_known > 0:
                                tests.append(("✅", f"Hot bills position data (detected {total_known} known positions)"))
                                print(f"   ✅ Position mapping working: {total_known} known, {total_unknown} unknown positions")
                            else:
                                tests.append(("⚠️", "Hot bills position data (all positions unknown)"))
                                print("   ⚠️  Hot bills API works but all positions are unknown")
                        else:
                            tests.append(("❌", "Hot bills position data (no position breakdown)"))
                            print("   ❌ Hot bills missing position breakdown")
                    else:
                        tests.append(("⚠️", "Hot bills API (no hot bills found)"))
                        print("   ⚠️  Hot bills API works but no bills found")
                else:
                    tests.append(("❌", f"Hot bills API (status: {response.status_code})"))
                    print("   ❌ Hot bills API failed")
            except Exception as e:
                tests.append(("❌", f"Hot bills API (error: {str(e)})"))
                print("   ❌ Hot bills API error")
            
            # Test 4: Check detailed health API
            print("\n4️⃣  Testing detailed health API...")
            try:
                response = await client.get("/api/health/detailed")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and "data" in data:
                        health_data = data["data"]
                        if "status" in health_data and "uptime_seconds" in health_data:
                            tests.append(("✅", "Detailed health API"))
                            print("   ✅ Detailed health API working")
                        else:
                            tests.append(("❌", "Detailed health API (missing required fields)"))
                            print("   ❌ Detailed health API missing required fields")
                    else:
                        tests.append(("❌", "Detailed health API (invalid response format)"))
                        print("   ❌ Detailed health API invalid response format")
                else:
                    tests.append(("❌", f"Detailed health API (status: {response.status_code})"))
                    print("   ❌ Detailed health API failed")
            except Exception as e:
                tests.append(("❌", f"Detailed health API (error: {str(e)})"))
                print("   ❌ Detailed health API error")
        
        # Test 5: UI Page Tests (basic connectivity)
        print("\n5️⃣  Testing UI pages...")
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout, follow_redirects=True) as client:
            
            # Test main dashboard
            try:
                response = await client.get("/")
                if response.status_code == 200:
                    content = response.text
                    if "OLIS" in content and "[App Name]" not in content:
                        tests.append(("✅", "Main dashboard loads"))
                        print("   ✅ Main dashboard loads with OLIS content")
                    else:
                        tests.append(("⚠️", "Main dashboard (contains template content)"))
                        print("   ⚠️  Main dashboard loads but may contain template content")
                else:
                    tests.append(("❌", f"Main dashboard (status: {response.status_code})"))
                    print("   ❌ Main dashboard failed to load")
            except Exception as e:
                tests.append(("❌", f"Main dashboard (error: {str(e)})"))
                print("   ❌ Main dashboard error")
            
            # Test system health page
            try:
                response = await client.get("/system-health")
                if response.status_code == 200:
                    content = response.text
                    if "/api/health/detailed" in content and "[App Name]" not in content:
                        tests.append(("✅", "System health page"))
                        print("   ✅ System health page loads with real API connection")
                    else:
                        tests.append(("⚠️", "System health page (may show template content)"))
                        print("   ⚠️  System health page loads but may show template content")
                else:
                    tests.append(("❌", f"System health page (status: {response.status_code})"))
                    print("   ❌ System health page failed to load")
            except Exception as e:
                tests.append(("❌", f"System health page (error: {str(e)})"))
                print("   ❌ System health page error")
            
            # Test design library page
            try:
                response = await client.get("/examples")
                if response.status_code == 200:
                    content = response.text
                    if "OLIS" in content and "[App Name]" not in content:
                        tests.append(("✅", "Design library page"))
                        print("   ✅ Design library page loads with OLIS content")
                    else:
                        tests.append(("⚠️", "Design library page (may show template content)"))
                        print("   ⚠️  Design library page loads but may show template content")
                else:
                    tests.append(("❌", f"Design library page (status: {response.status_code})"))
                    print("   ❌ Design library page failed to load")
            except Exception as e:
                tests.append(("❌", f"Design library page (error: {str(e)})"))
                print("   ❌ Design library page error")
    
    except Exception as e:
        print(f"\n❌ Critical error during smoke test: {str(e)}")
        tests.append(("❌", f"Critical error: {str(e)}"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SMOKE TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for status, _ in tests if status == "✅")
    warnings = sum(1 for status, _ in tests if status == "⚠️")
    failed = sum(1 for status, _ in tests if status == "❌")
    
    print(f"✅ Passed: {passed}")
    print(f"⚠️  Warnings: {warnings}")  
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {len(tests)}")
    
    if failed > 0:
        print("\n❌ CRITICAL ISSUES DETECTED:")
        for status, test_name in tests:
            if status == "❌":
                print(f"   • {test_name}")
        print("\n🔧 ACTION REQUIRED: Review failed tests before proceeding with changes")
        return False
    elif warnings > 0:
        print("\n⚠️  WARNINGS DETECTED:")
        for status, test_name in tests:
            if status == "⚠️":
                print(f"   • {test_name}")
        print("\n🔍 REVIEW RECOMMENDED: Check warnings but safe to proceed")
        return True
    else:
        print("\n✅ ALL TESTS PASSED - System ready for changes")
        return True


if __name__ == "__main__":
    try:
        result = asyncio.run(run_smoke_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Smoke test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Smoke test failed with error: {str(e)}")
        sys.exit(1)