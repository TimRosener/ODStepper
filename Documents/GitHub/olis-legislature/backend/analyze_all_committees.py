#!/usr/bin/env python3
"""
Analyze ALL committee information from OLIS bills - complete dataset
"""

import asyncio
from collections import Counter
import re
from olis_client import OLISClient

async def analyze_all_committees():
    """Analyze CurrentCommitteeCode and CurrentSubCommittee fields from ALL OLIS data"""
    try:
        client = OLISClient()
        
        print("🔍 Analyzing ALL committee codes from 2025 Regular Session...")
        measures = await client.get_all_measures("2025R1")  # Get ALL bills, not just 200
        
        if measures:
            committee_data = []
            committee_codes = []
            subcommittees = []
            unknown_codes = []
            
            for bill in measures:
                location = bill.get('CurrentLocation', '')
                committee_code = (bill.get('CurrentCommitteeCode', '') or '').strip()
                subcommittee = (bill.get('CurrentSubCommittee', '') or '').strip()
                
                # Only analyze bills that are actually in committees
                if 'committee' in location.lower():
                    bill_id = f"{bill.get('MeasurePrefix', '')}{bill.get('MeasureNumber', '')}"
                    committee_data.append({
                        'bill': bill_id,
                        'location': location,
                        'committee_code': committee_code,
                        'subcommittee': subcommittee
                    })
                    
                    if committee_code:
                        committee_codes.append(committee_code)
                        
                        # Check if this is a code we don't recognize
                        from committee_mapping import is_valid_committee_code
                        if not is_valid_committee_code(committee_code):
                            unknown_codes.append(committee_code)
                            
                    if subcommittee:
                        subcommittees.append(subcommittee)
            
            print(f"📊 Analyzed {len(measures)} total bills")
            print(f"📋 Found {len(committee_data)} bills currently in committees")
            
            # Count unique committee codes and subcommittees
            committee_code_counts = Counter(committee_codes)
            subcommittee_counts = Counter(subcommittees)
            unknown_code_counts = Counter(unknown_codes)
            
            print("\n" + "=" * 80)
            print("🏛️ COMPLETE COMMITTEE CODE ANALYSIS:")
            print("=" * 80)
            
            print(f"\n📊 ALL COMMITTEE CODES FOUND ({len(committee_code_counts)} unique codes):")
            for code, count in committee_code_counts.most_common():
                print(f"  • '{code}': {count} bills")
            
            if subcommittee_counts:
                print(f"\n📊 SUBCOMMITTEES FOUND ({len(subcommittee_counts)} unique subcommittees):")
                for subcom, count in subcommittee_counts.most_common():
                    print(f"  • '{subcom}': {count} bills")
            else:
                print("\n❌ No subcommittee data found in CurrentSubCommittee field")
            
            if unknown_code_counts:
                print(f"\n⚠️ UNMAPPED COMMITTEE CODES ({len(unknown_code_counts)} codes need mapping):")
                for code, count in unknown_code_counts.most_common():
                    print(f"  • '{code}': {count} bills - NEEDS MAPPING!")
                    
                print(f"\n📋 SAMPLE BILLS WITH UNMAPPED CODES:")
                unmapped_samples = [data for data in committee_data if data['committee_code'] in unknown_codes][:10]
                for data in unmapped_samples:
                    print(f"  • {data['bill']:6} | {data['location']:30} | {data['committee_code']}")
            else:
                print("\n✅ All committee codes are properly mapped!")
            
            # Show a broader sample of all committee data
            print(f"\n📋 COMMITTEE DATA SAMPLE (First 30 bills with committees):")
            print("Bill ID | Current Location                    | Committee Code | Subcommittee")
            print("-" * 90)
            for i, data in enumerate(committee_data[:30]):
                code = data['committee_code'] or 'None'
                subcom = data['subcommittee'] or 'None'
                location = data['location'][:30].ljust(30)
                print(f"{data['bill']:6} | {location} | {code:14} | {subcom}")
                
        else:
            print("❌ No bills found")
            
    except Exception as e:
        print(f"❌ Error analyzing committees: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_all_committees())