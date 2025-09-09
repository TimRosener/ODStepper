#!/usr/bin/env python3
"""
Comprehensive search for sponsor/author data in OLIS API
"""

import asyncio
import json
from olis_client import OLISClient

async def find_sponsor_data():
    """Search for sponsor information across different OLIS endpoints"""
    try:
        client = OLISClient()
        
        print("🔍 COMPREHENSIVE SPONSOR DATA INVESTIGATION")
        print("=" * 80)
        
        # 1. Check if there are more fields in different bill types
        print("\n1️⃣ EXAMINING DIFFERENT BILL TYPES FOR SPONSOR FIELDS...")
        measures = await client.get_measures("2025R1", limit=20)
        
        # Look at different types of bills
        bill_types = {}
        for bill in measures:
            bill_type = bill.get('MeasurePrefix', 'Unknown')
            if bill_type not in bill_types:
                bill_types[bill_type] = bill
        
        print(f"Found {len(bill_types)} different bill types: {list(bill_types.keys())}")
        
        # Check each bill type for any sponsor-related fields
        all_unique_fields = set()
        for bill_type, bill in bill_types.items():
            print(f"\n📋 {bill_type} - Fields containing 'sponsor', 'author', 'chief', or 'prime':")
            sponsor_fields = []
            for field_name in bill.keys():
                all_unique_fields.add(field_name)
                if any(word in field_name.lower() for word in ['sponsor', 'author', 'chief', 'prime']):
                    value = bill.get(field_name)
                    sponsor_fields.append(f"  • {field_name}: {value}")
            
            if sponsor_fields:
                for field in sponsor_fields:
                    print(field)
            else:
                print("  ❌ No direct sponsor fields found")
        
        print(f"\n📊 TOTAL UNIQUE FIELDS ACROSS ALL BILL TYPES: {len(all_unique_fields)}")
        
        # 2. Let's try to discover other OLIS API endpoints that might have sponsor data
        print("\n2️⃣ TESTING FOR ADDITIONAL SPONSOR-RELATED ENDPOINTS...")
        
        # Try some common sponsor-related endpoints
        potential_endpoints = [
            "MeasureSponsors",
            "BillSponsors", 
            "MeasureAuthors",
            "BillAuthors",
            "PrimarySponsors",
            "CoSponsors",
            "ChiefSponsors"
        ]
        
        for endpoint in potential_endpoints:
            try:
                print(f"Testing endpoint: {endpoint}")
                # Try to get data from potential endpoint
                result = await client._make_request(endpoint, {"$top": 1})
                if result:
                    print(f"  ✅ {endpoint} exists! Sample data:")
                    if isinstance(result, dict) and "value" in result:
                        sample = result["value"][0] if result["value"] else "No data"
                    elif isinstance(result, list) and result:
                        sample = result[0]
                    else:
                        sample = result
                    print(f"     {json.dumps(sample, indent=6)}")
            except Exception as e:
                if "404" in str(e) or "Not Found" in str(e):
                    print(f"  ❌ {endpoint} does not exist")
                else:
                    print(f"  ⚠️ {endpoint} error: {e}")
        
        # 3. Check measure history for sponsor information
        print("\n3️⃣ CHECKING MEASURE HISTORY FOR SPONSOR DATA...")
        
        # Get history for a sample bill
        sample_bill = measures[0] if measures else None
        if sample_bill:
            prefix = sample_bill.get('MeasurePrefix')
            number = sample_bill.get('MeasureNumber')
            session = sample_bill.get('SessionKey')
            
            print(f"Getting history for {prefix}{number}...")
            
            try:
                history = await client.get_measure_history(session, prefix, number)
                
                if history:
                    print(f"Found {len(history)} history entries")
                    print("Sample history entry fields:")
                    first_entry = history[0]
                    for field_name, value in first_entry.items():
                        print(f"  • {field_name}: {value}")
                        
                    # Look for sponsor-related fields in history
                    sponsor_history_fields = []
                    for entry in history[:5]:  # Check first 5 entries
                        for field_name in entry.keys():
                            if any(word in field_name.lower() for word in ['sponsor', 'author', 'chief', 'prime']):
                                sponsor_history_fields.append(field_name)
                    
                    if sponsor_history_fields:
                        print(f"Sponsor-related fields in history: {set(sponsor_history_fields)}")
                    else:
                        print("No sponsor fields found in history entries")
                        
            except Exception as e:
                print(f"Error getting history: {e}")
        
        # 4. Try direct OLIS OData endpoint exploration
        print("\n4️⃣ EXPLORING OLIS ODATA METADATA...")
        
        try:
            # Try to get OData metadata
            metadata_result = await client._make_request("$metadata", {})
            print("✅ Metadata endpoint accessible")
            print(f"Metadata type: {type(metadata_result)}")
            if isinstance(metadata_result, str):
                # Look for sponsor-related entity sets in metadata
                if 'sponsor' in metadata_result.lower():
                    print("📍 Found 'sponsor' references in metadata!")
                    # Extract relevant lines
                    lines = metadata_result.split('\n')
                    sponsor_lines = [line.strip() for line in lines if 'sponsor' in line.lower()]
                    for line in sponsor_lines[:10]:  # Show first 10 matches
                        print(f"  {line}")
                else:
                    print("❌ No 'sponsor' references found in metadata")
                    
        except Exception as e:
            print(f"Could not access metadata: {e}")
        
        # 5. Check committees endpoint for sponsor info
        print("\n5️⃣ CHECKING COMMITTEES DATA FOR MEMBER/SPONSOR INFO...")
        
        try:
            committees = await client.get_committees("2025R1")
            if committees:
                print(f"Found {len(committees)} committees")
                sample_committee = committees[0]
                print("Sample committee fields:")
                for field_name, value in sample_committee.items():
                    print(f"  • {field_name}: {value}")
                    
        except Exception as e:
            print(f"Error getting committees: {e}")
            
        print("\n" + "=" * 80)
        print("🎯 SPONSOR DATA INVESTIGATION COMPLETE")
        
    except Exception as e:
        print(f"❌ Error in sponsor investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(find_sponsor_data())