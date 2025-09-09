#!/usr/bin/env python3
"""
Examine a bill that's currently in committee to see all populated fields
"""

import asyncio
import json
from olis_client import OLISClient

async def examine_committee_bill():
    """Find and examine a bill that's currently in committee"""
    try:
        client = OLISClient()
        
        print("🔍 Looking for bills currently in committees...")
        measures = await client.get_measures("2025R1", limit=50)  # Get more bills to find one in committee
        
        committee_bill = None
        for bill in measures:
            if 'committee' in bill.get('CurrentLocation', '').lower():
                committee_bill = bill
                break
        
        if committee_bill:
            print(f"\n📊 COMMITTEE BILL EXAMPLE:")
            print(f"Bill: {committee_bill.get('MeasurePrefix', '')}{committee_bill.get('MeasureNumber', '')}")
            print(f"Location: {committee_bill.get('CurrentLocation', '')}")
            print(f"Committee Code: {committee_bill.get('CurrentCommitteeCode', '')}")
            print("=" * 80)
            
            print("\n🔍 ALL FIELDS WITH VALUES:")
            for field, value in sorted(committee_bill.items()):
                if value is not None and value != '':
                    if isinstance(value, str) and len(value) > 100:
                        display_value = f'"{value[:100]}..."'
                    elif isinstance(value, str):
                        display_value = f'"{value}"'
                    else:
                        display_value = str(value)
                    print(f"  • {field:25} = {display_value}")
            
            print("\n📋 COMPLETE BILL JSON:")
            print(json.dumps(committee_bill, indent=2, ensure_ascii=False))
            
        else:
            print("❌ No bills in committee found in sample")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(examine_committee_bill())