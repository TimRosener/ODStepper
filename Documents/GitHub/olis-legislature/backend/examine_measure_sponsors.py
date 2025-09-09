#!/usr/bin/env python3
"""
Examine the MeasureSponsors endpoint in detail
"""

import asyncio
import json
from olis_client import OLISClient

async def examine_measure_sponsors():
    """Examine the MeasureSponsors endpoint structure and data"""
    try:
        client = OLISClient()
        
        print("🔍 DETAILED EXAMINATION OF MEASURE SPONSORS ENDPOINT")
        print("=" * 80)
        
        # Get sponsor data for 2025R1 session
        print("\n1️⃣ GETTING SPONSOR DATA FOR 2025R1 SESSION...")
        
        sponsors_2025 = await client._make_request("MeasureSponsors", {
            "$filter": "SessionKey eq '2025R1'",
            "$top": 10,
            "$orderby": "MeasureNumber"
        })
        
        if sponsors_2025:
            if isinstance(sponsors_2025, dict) and "value" in sponsors_2025:
                sponsor_records = sponsors_2025["value"]
            elif isinstance(sponsors_2025, list):
                sponsor_records = sponsors_2025
            else:
                sponsor_records = [sponsors_2025]
                
            print(f"Found {len(sponsor_records)} sponsor records in 2025R1")
            
            if sponsor_records:
                print("\n📊 SPONSOR RECORD STRUCTURE:")
                first_record = sponsor_records[0]
                for field, value in first_record.items():
                    print(f"  • {field:20} = {value}")
                
                print(f"\n📋 SAMPLE SPONSOR RECORDS:")
                for i, record in enumerate(sponsor_records[:5]):
                    bill_id = f"{record.get('MeasurePrefix', '')}{record.get('MeasureNumber', '')}"
                    sponsor_type = record.get('SponsorType', '')
                    legislator = record.get('LegislatoreCode', '')  # Note: typo in field name
                    level = record.get('SponsorLevel', '')
                    print(f"  {i+1}. {bill_id:8} | {level:10} | {sponsor_type:10} | {legislator}")
                
                # Analyze sponsor types and levels
                print(f"\n🔍 SPONSOR DATA ANALYSIS:")
                
                sponsor_types = {}
                sponsor_levels = {}
                for record in sponsor_records:
                    s_type = record.get('SponsorType', 'Unknown')
                    s_level = record.get('SponsorLevel', 'Unknown')
                    sponsor_types[s_type] = sponsor_types.get(s_type, 0) + 1
                    sponsor_levels[s_level] = sponsor_levels.get(s_level, 0) + 1
                
                print(f"Sponsor Types: {dict(sponsor_types)}")
                print(f"Sponsor Levels: {dict(sponsor_levels)}")
                
        else:
            print("❌ No sponsor data found for 2025R1")
        
        # 2. Try to get sponsor data for a specific bill we know exists
        print("\n2️⃣ GETTING SPONSORS FOR A SPECIFIC BILL...")
        
        # First get a bill from 2025R1
        measures = await client.get_measures("2025R1", limit=10)
        if measures:
            sample_bill = measures[0]
            prefix = sample_bill.get('MeasurePrefix')
            number = sample_bill.get('MeasureNumber')
            
            print(f"Looking for sponsors of {prefix}{number}...")
            
            bill_sponsors = await client._make_request("MeasureSponsors", {
                "$filter": f"SessionKey eq '2025R1' and MeasurePrefix eq '{prefix}' and MeasureNumber eq {number}"
            })
            
            if bill_sponsors:
                if isinstance(bill_sponsors, dict) and "value" in bill_sponsors:
                    bill_sponsor_records = bill_sponsors["value"]
                elif isinstance(bill_sponsors, list):
                    bill_sponsor_records = bill_sponsors
                else:
                    bill_sponsor_records = [bill_sponsors]
                    
                print(f"Found {len(bill_sponsor_records)} sponsors for {prefix}{number}:")
                
                for sponsor in bill_sponsor_records:
                    print(f"  • {sponsor.get('SponsorLevel', 'Unknown'):10} {sponsor.get('SponsorType', 'Unknown'):10} - {sponsor.get('LegislatoreCode', 'Unknown')}")
                    
            else:
                print(f"No sponsors found for {prefix}{number}")
        
        # 3. Get broader statistics on sponsor data
        print("\n3️⃣ GETTING BROADER SPONSOR STATISTICS...")
        
        all_sponsors = await client._make_request("MeasureSponsors", {
            "$filter": "SessionKey eq '2025R1'",
            "$top": 100  # Get more records for better analysis
        })
        
        if all_sponsors:
            if isinstance(all_sponsors, dict) and "value" in all_sponsors:
                all_sponsor_records = all_sponsors["value"]
            elif isinstance(all_sponsors, list):
                all_sponsor_records = all_sponsors
            else:
                all_sponsor_records = [all_sponsors]
                
            print(f"\n📊 SPONSOR STATISTICS (from {len(all_sponsor_records)} records):")
            
            # Count unique bills with sponsors
            unique_bills = set()
            legislators = set()
            committees = set()
            
            for record in all_sponsor_records:
                bill_key = f"{record.get('MeasurePrefix', '')}{record.get('MeasureNumber', '')}"
                unique_bills.add(bill_key)
                
                if record.get('LegislatoreCode'):
                    legislators.add(record.get('LegislatoreCode'))
                if record.get('CommitteeCode'):
                    committees.add(record.get('CommitteeCode'))
            
            print(f"  • Unique bills with sponsor data: {len(unique_bills)}")
            print(f"  • Unique legislators as sponsors: {len(legislators)}")
            print(f"  • Unique committees as sponsors: {len(committees)}")
            
            # Show sample legislators
            print(f"\n👥 SAMPLE LEGISLATORS:")
            for legislator in list(legislators)[:10]:
                print(f"  • {legislator}")
                
            # Show sample committees if any
            if committees:
                print(f"\n🏛️ SAMPLE COMMITTEES:")
                for committee in list(committees)[:5]:
                    print(f"  • {committee}")
        
        print("\n" + "=" * 80)
        print("🎯 MEASURE SPONSORS ANALYSIS COMPLETE")
        
    except Exception as e:
        print(f"❌ Error examining sponsors: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(examine_measure_sponsors())