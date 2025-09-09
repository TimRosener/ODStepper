#!/usr/bin/env python3
"""
Simple test script to check if the OLIS client works without full dependencies
"""

import asyncio
import json
from olis_client import OLISClient

async def test_olis_client():
    """Test the OLIS client functionality"""
    try:
        print("🔧 Testing OLIS Client...")
        client = OLISClient()
        
        print("📡 Fetching sessions from OLIS...")
        sessions = await client.get_sessions()
        
        print(f"✅ Found {len(sessions)} sessions")
        if sessions:
            # Show first session
            print(f"📋 First session: {sessions[0]['SessionName']} ({sessions[0]['SessionKey']})")
            
            # Test getting stats for first session
            session_key = sessions[0]['SessionKey']
            print(f"📊 Testing session stats for: {session_key}")
            measures = await client.get_measures(session_key, limit=10)
            print(f"✅ Found {len(measures)} measures (limited to 10 for test)")
            
            if measures:
                print(f"📄 First measure: {measures[0].get('MeasurePrefix', '')}{measures[0].get('MeasureNumber', '')} - {measures[0].get('CatchLine', 'No description')[:100]}...")
        
        print("🎉 OLIS client test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ OLIS client test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_olis_client())
    exit(0 if success else 1)