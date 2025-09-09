#!/usr/bin/env python3
"""
Find the actual testimony positions (for/against/neutral) in OLIS
"""

import asyncio
import json
from olis_client import OLISClient

async def find_testimony_positions():
    """Find where testimony positions are stored"""
    try:
        client = OLISClient()
        
        print("🔍 INVESTIGATING TESTIMONY POSITION DATA")
        print("=" * 80)
        
        # 1. Look for a positions lookup table
        print("\n1️⃣ TESTING FOR TESTIMONY POSITION LOOKUP ENDPOINTS...")
        
        potential_position_endpoints = [
            "TestimonyPositions",
            "PositionOnMeasure", 
            "MeasurePositions",
            "CommitteeTestimonyPositions",
            "PublicTestimonyPositions"
        ]
        
        for endpoint in potential_position_endpoints:
            try:
                result = await client._make_request(endpoint, {"$top": 5})
                if result:
                    print(f"✅ {endpoint} exists!")
                    if isinstance(result, dict) and "value" in result:
                        sample = result["value"]
                    elif isinstance(result, list):
                        sample = result
                    else:
                        sample = [result]
                    
                    if sample:
                        print(f"Sample data from {endpoint}:")
                        first_record = sample[0] if isinstance(sample, list) else sample
                        for field, value in first_record.items():
                            print(f"  • {field}: {value}")
                        print()
            except Exception as e:
                if "404" in str(e):
                    print(f"❌ {endpoint} does not exist")
                else:
                    print(f"⚠️ {endpoint} error: {e}")
        
        # 2. Check if PositionOnMeasureId links to another table
        print("\n2️⃣ INVESTIGATING PositionOnMeasureId FIELD...")
        
        # Get some testimony with PositionOnMeasureId values
        testimony = await client._make_request("CommitteePublicTestimonies", {
            "$filter": "SessionKey eq '2025R1'",
            "$top": 10
        })
        
        if testimony:
            if isinstance(testimony, dict) and "value" in testimony:
                records = testimony["value"]
            else:
                records = testimony if isinstance(testimony, list) else [testimony]
            
            position_ids = []
            for record in records:
                pos_id = record.get('PositionOnMeasureId')
                if pos_id:
                    position_ids.append(pos_id)
            
            print(f"Found PositionOnMeasureId values: {position_ids[:10]}")
            
            # Try to use these IDs to look up positions
            if position_ids:
                pos_id = position_ids[0]
                
                # Try different ways to look up position
                lookup_attempts = [
                    f"PositionOnMeasures({pos_id})",
                    f"TestimonyPositions({pos_id})",
                    f"MeasurePositions({pos_id})"
                ]
                
                for lookup in lookup_attempts:
                    try:
                        position_data = await client._make_request(lookup, {})
                        if position_data:
                            print(f"✅ Found position data via {lookup}:")
                            print(f"  {json.dumps(position_data, indent=2)}")
                            break
                    except Exception as e:
                        print(f"❌ {lookup} failed: {e}")
        
        # 3. Check if there are other testimony-related endpoints
        print("\n3️⃣ EXPLORING ALL TESTIMONY-RELATED ENDPOINTS...")
        
        other_endpoints = [
            "PositionOnMeasures",
            "CommitteeTestimonies", 
            "PublicTestimonies",
            "TestimonyTypes",
            "TestimonyStatuses"
        ]
        
        for endpoint in other_endpoints:
            try:
                result = await client._make_request(endpoint, {
                    "$top": 3,
                    "$filter": "SessionKey eq '2025R1'" if 'SessionKey' in str(result) else None
                })
                if result:
                    print(f"✅ {endpoint} found!")
                    if isinstance(result, dict) and "value" in result:
                        sample = result["value"]
                    else:
                        sample = result if isinstance(result, list) else [result]
                    
                    if sample:
                        first = sample[0] if isinstance(sample, list) else sample
                        print(f"  Sample fields: {list(first.keys())}")
                        
                        # Look for position-related fields
                        position_fields = [k for k in first.keys() if 'position' in k.lower() or 'stance' in k.lower() or 'support' in k.lower()]
                        if position_fields:
                            print(f"  Position fields found: {position_fields}")
                            for field in position_fields:
                                print(f"    {field}: {first[field]}")
                    print()
                        
            except Exception as e:
                if "404" not in str(e):
                    print(f"⚠️ {endpoint}: {e}")
        
        # 4. Try direct position lookup with known IDs
        print("\n4️⃣ DIRECT POSITION LOOKUP ATTEMPTS...")
        
        if position_ids:
            # Try the most likely endpoint
            try:
                positions_result = await client._make_request("PositionOnMeasures", {
                    "$filter": f"Id eq {position_ids[0]}"
                })
                if positions_result:
                    print("✅ Found PositionOnMeasures data!")
                    print(json.dumps(positions_result, indent=2))
            except Exception as e:
                print(f"❌ PositionOnMeasures lookup failed: {e}")
        
        print("\n" + "=" * 80)
        print("🎯 TESTIMONY POSITION INVESTIGATION COMPLETE")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(find_testimony_positions())