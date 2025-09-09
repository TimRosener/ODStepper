#!/usr/bin/env python3
"""
Comprehensive examination of testimony data in OLIS for "hot bills" analysis
"""

import asyncio
import json
from collections import Counter, defaultdict
from olis_client import OLISClient

async def examine_testimony_data():
    """Examine testimony data structure and analyze for hot bills ranking"""
    try:
        client = OLISClient()
        
        print("🔍 COMPREHENSIVE TESTIMONY DATA ANALYSIS")
        print("=" * 80)
        
        # 1. First, let's examine the testimony endpoint structure
        print("\n1️⃣ EXAMINING TESTIMONY DATA STRUCTURE...")
        
        # Get sample testimony data
        testimony_sample = await client._make_request("CommitteePublicTestimonies", {
            "$filter": "SessionKey eq '2025R1'",
            "$top": 10,
            "$orderby": "MeetingDate desc"
        })
        
        if testimony_sample:
            if isinstance(testimony_sample, dict) and "value" in testimony_sample:
                testimony_records = testimony_sample["value"]
            elif isinstance(testimony_sample, list):
                testimony_records = testimony_sample
            else:
                testimony_records = [testimony_sample]
                
            print(f"Found {len(testimony_records)} testimony records")
            
            if testimony_records:
                print("\n📊 TESTIMONY RECORD STRUCTURE:")
                first_record = testimony_records[0]
                for field, value in first_record.items():
                    if isinstance(value, str) and len(value) > 100:
                        display_value = f'"{value[:100]}..."'
                    elif value is None:
                        display_value = "null"
                    elif isinstance(value, str):
                        display_value = f'"{value}"'
                    else:
                        display_value = str(value)
                    print(f"  • {field:25} = {display_value}")
                
                print(f"\n📋 SAMPLE TESTIMONY RECORDS:")
                for i, record in enumerate(testimony_records[:5]):
                    bill_id = f"{record.get('MeasurePrefix', '')}{record.get('MeasureNumber', '')}"
                    position = record.get('TestimonyPosition', 'Unknown')
                    name = record.get('Name', 'Unknown')[:30] + "..." if len(record.get('Name', '')) > 30 else record.get('Name', 'Unknown')
                    org = record.get('Organization', 'N/A')[:25] + "..." if len(record.get('Organization', '')) > 25 else record.get('Organization', 'N/A')
                    print(f"  {i+1}. {bill_id:8} | {position:15} | {name:30} | {org}")
        
        # 2. Get larger sample to analyze testimony patterns
        print("\n2️⃣ ANALYZING TESTIMONY PATTERNS FOR HOT BILLS RANKING...")
        
        # Get more testimony records for analysis
        all_testimony = await client._make_request("CommitteePublicTestimonies", {
            "$filter": "SessionKey eq '2025R1'",
            "$top": 500,  # Get substantial sample
            "$orderby": "MeetingDate desc"
        })
        
        if all_testimony:
            if isinstance(all_testimony, dict) and "value" in all_testimony:
                all_records = all_testimony["value"]
            elif isinstance(all_testimony, list):
                all_records = all_testimony
            else:
                all_records = [all_testimony]
                
            print(f"\nAnalyzing {len(all_records)} testimony records for hot bills analysis...")
            
            # Analyze testimony by bill
            bill_testimony = defaultdict(list)
            
            for record in all_records:
                bill_key = f"{record.get('MeasurePrefix', '')}{record.get('MeasureNumber', '')}"
                bill_testimony[bill_key].append(record)
            
            print(f"\nFound testimony for {len(bill_testimony)} unique bills")
            
            # Calculate "hotness" scores
            bill_scores = []
            
            for bill_id, testimonies in bill_testimony.items():
                # Count total testimonies
                total_testimony = len(testimonies)
                
                # Count positions
                positions = Counter()
                for testimony in testimonies:
                    pos = testimony.get('TestimonyPosition', 'Unknown')
                    positions[pos] += 1
                
                # Calculate diversity score
                unique_positions = len([pos for pos in positions.keys() if pos and pos.lower() != 'unknown'])
                
                # Bonus for having both pro and con testimony (controversy factor)
                has_pro = any(pos and ('support' in pos.lower() or 'favor' in pos.lower()) for pos in positions.keys())
                has_con = any(pos and ('oppos' in pos.lower() or 'against' in pos.lower()) for pos in positions.keys())
                controversy_bonus = 1.5 if (has_pro and has_con) else 1.0
                
                # Calculate hotness score
                # Formula: (total_testimony * diversity_factor * controversy_bonus)
                diversity_factor = min(unique_positions / 3.0, 1.0) + 0.5  # Normalize diversity, minimum 0.5
                hotness_score = total_testimony * diversity_factor * controversy_bonus
                
                bill_scores.append({
                    'bill': bill_id,
                    'total_testimony': total_testimony,
                    'positions': dict(positions),
                    'unique_positions': unique_positions,
                    'has_controversy': has_pro and has_con,
                    'hotness_score': round(hotness_score, 2)
                })
            
            # Sort by hotness score
            bill_scores.sort(key=lambda x: x['hotness_score'], reverse=True)
            
            print(f"\n🔥 TOP 10 HOTTEST BILLS (by testimony volume and diversity):")
            print("Rank | Bill   | Total | Positions | Controversy | Score | Position Breakdown")
            print("-" * 80)
            
            for i, bill_data in enumerate(bill_scores[:10], 1):
                controversy = "Yes" if bill_data['has_controversy'] else "No"
                positions_str = ", ".join([f"{k}:{v}" for k, v in bill_data['positions'].items()][:3])
                if len(positions_str) > 40:
                    positions_str = positions_str[:37] + "..."
                
                print(f"{i:4} | {bill_data['bill']:6} | {bill_data['total_testimony']:5} | "
                      f"{bill_data['unique_positions']:9} | {controversy:11} | "
                      f"{bill_data['hotness_score']:5} | {positions_str}")
            
            # 3. Analyze what testimony positions are available
            print(f"\n3️⃣ TESTIMONY POSITION ANALYSIS:")
            
            all_positions = Counter()
            for record in all_records:
                pos = record.get('TestimonyPosition', 'Unknown')
                if pos:
                    all_positions[pos] += 1
            
            print(f"\nAll testimony positions found (top 10):")
            for position, count in all_positions.most_common(10):
                print(f"  • {position:30} : {count:4} testimonies")
            
            # 4. Sample detailed testimony for hottest bill
            if bill_scores:
                hottest_bill = bill_scores[0]['bill']
                print(f"\n4️⃣ DETAILED ANALYSIS OF HOTTEST BILL: {hottest_bill}")
                
                hottest_testimonies = bill_testimony[hottest_bill]
                print(f"Total testimonies: {len(hottest_testimonies)}")
                
                print(f"\nSample testimonies:")
                for i, testimony in enumerate(hottest_testimonies[:5]):
                    name = testimony.get('Name', 'Unknown')
                    org = testimony.get('Organization', 'N/A')
                    position = testimony.get('TestimonyPosition', 'Unknown')
                    date = testimony.get('MeetingDate', 'Unknown')[:10]  # Just date part
                    
                    print(f"  {i+1}. {name} ({org}) - {position} - {date}")
        
        print("\n" + "=" * 80)
        print("🎯 TESTIMONY ANALYSIS COMPLETE")
        
    except Exception as e:
        print(f"❌ Error analyzing testimony: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(examine_testimony_data())