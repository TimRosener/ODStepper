#!/usr/bin/env python3
"""
Analyze specific committee codes and subcommittee information from OLIS bills
"""

import asyncio
from collections import Counter
import re
from olis_client import OLISClient

async def analyze_committee_codes():
    """Analyze CurrentCommitteeCode and CurrentSubCommittee fields from OLIS data"""
    try:
        client = OLISClient()
        
        print("🔍 Analyzing committee codes from 2025 Regular Session...")
        measures = await client.get_measures("2025R1", limit=200)
        
        if measures:
            committee_data = []
            committee_codes = []
            subcommittees = []
            
            for bill in measures:
                location = bill.get('CurrentLocation', '')
                committee_code = bill.get('CurrentCommitteeCode', '')
                subcommittee = bill.get('CurrentSubCommittee', '')
                
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
                    if subcommittee:
                        subcommittees.append(subcommittee)
            
            print(f"📊 Analyzed {len(measures)} total bills")
            print(f"📋 Found {len(committee_data)} bills currently in committees")
            
            # Count unique committee codes and subcommittees
            committee_code_counts = Counter(committee_codes)
            subcommittee_counts = Counter(subcommittees)
            
            print("\n" + "=" * 80)
            print("🏛️ COMMITTEE CODE ANALYSIS:")
            print("=" * 80)
            
            if committee_code_counts:
                print(f"\n📊 COMMITTEE CODES FOUND ({len(committee_code_counts)} unique codes):")
                for code, count in committee_code_counts.most_common():
                    print(f"  • '{code}': {count} bills")
            else:
                print("\n❌ No committee codes found in CurrentCommitteeCode field")
            
            if subcommittee_counts:
                print(f"\n📊 SUBCOMMITTEES FOUND ({len(subcommittee_counts)} unique subcommittees):")
                for subcom, count in subcommittee_counts.most_common():
                    print(f"  • '{subcom}': {count} bills")
            else:
                print("\n❌ No subcommittee data found in CurrentSubCommittee field")
            
            print(f"\n📋 DETAILED COMMITTEE DATA SAMPLE (First 20 bills):")
            print("Bill ID | Current Location | Committee Code | Subcommittee")
            print("-" * 80)
            for i, data in enumerate(committee_data[:20]):
                code = data['committee_code'] or 'None'
                subcom = data['subcommittee'] or 'None'
                print(f"{data['bill']:6} | {data['location']:20} | {code:14} | {subcom}")
            
            # Check if there are any other fields that might contain committee info
            print(f"\n🔍 CHECKING OTHER POTENTIAL COMMITTEE FIELDS:")
            sample_bill = measures[0] if measures else {}
            committee_related_fields = []
            
            for field_name in sample_bill.keys():
                if 'committee' in field_name.lower() or 'comm' in field_name.lower():
                    committee_related_fields.append(field_name)
            
            if committee_related_fields:
                print("Found potential committee-related fields:")
                for field in committee_related_fields:
                    sample_values = []
                    for bill in measures[:10]:  # Check first 10 bills
                        value = bill.get(field, '')
                        if value and value not in sample_values:
                            sample_values.append(str(value)[:50])  # Limit length
                    print(f"  • {field}: {sample_values[:3]}")  # Show first 3 unique values
            else:
                print("No additional committee-related fields found")
                
        else:
            print("❌ No bills found")
            
    except Exception as e:
        print(f"❌ Error analyzing committee codes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_committee_codes())