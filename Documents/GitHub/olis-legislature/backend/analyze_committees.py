#!/usr/bin/env python3
"""
Analyze committee information from OLIS bills
"""

import asyncio
from collections import Counter
import re
from olis_client import OLISClient

async def analyze_committees():
    """Analyze committee names from bill CurrentLocation field"""
    try:
        client = OLISClient()
        
        print("🔍 Analyzing committee information from 2025 Regular Session...")
        measures = await client.get_measures("2025R1", limit=200)
        
        if measures:
            committee_bills = []
            all_locations = []
            
            for bill in measures:
                location = bill.get('CurrentLocation', '')
                all_locations.append(location)
                
                if 'committee' in location.lower():
                    committee_bills.append({
                        'bill': f"{bill.get('MeasurePrefix', '')}{bill.get('MeasureNumber', '')}",
                        'location': location
                    })
            
            print(f"📊 Analyzed {len(measures)} bills")
            print(f"📋 Found {len(committee_bills)} bills currently in committees")
            
            # Extract committee names
            committee_names = []
            for bill in committee_bills:
                location = bill['location']
                
                # Try to extract committee name patterns
                if 'in senate committee' in location.lower():
                    # Try to extract specific committee name after "Senate Committee on"
                    match = re.search(r'senate committee on (.+?)(?:$|,|\.)', location, re.IGNORECASE)
                    if match:
                        committee_names.append(f"Senate {match.group(1).title()}")
                    else:
                        committee_names.append("Senate Committee")
                        
                elif 'in house committee' in location.lower():
                    # Try to extract specific committee name after "House Committee on"
                    match = re.search(r'house committee on (.+?)(?:$|,|\.)', location, re.IGNORECASE)
                    if match:
                        committee_names.append(f"House {match.group(1).title()}")
                    else:
                        committee_names.append("House Committee")
                        
                elif 'joint committee' in location.lower():
                    match = re.search(r'joint committee on (.+?)(?:$|,|\.)', location, re.IGNORECASE)
                    if match:
                        committee_names.append(f"Joint {match.group(1).title()}")
                    else:
                        committee_names.append("Joint Committee")
            
            # Count committees
            committee_counts = Counter(committee_names)
            
            print("\n" + "=" * 80)
            print("📊 COMMITTEE ANALYSIS RESULTS:")
            print("=" * 80)
            
            print(f"\n🏛️ COMMITTEES WITH BILLS ({len(committee_counts)} committees):")
            for committee, count in committee_counts.most_common():
                print(f"  • {committee}: {count} bills")
            
            print(f"\n📋 SAMPLE COMMITTEE BILL LOCATIONS:")
            for bill in committee_bills[:10]:
                print(f"  • {bill['bill']}: {bill['location']}")
                
            print(f"\n📈 ALL CURRENT LOCATION PATTERNS (Top 10):")
            location_counts = Counter(all_locations)
            for location, count in location_counts.most_common(10):
                print(f"  {count:3d}: '{location}'")
                
        else:
            print("❌ No bills found")
            
    except Exception as e:
        print(f"❌ Error analyzing committees: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_committees())