#!/usr/bin/env python3
"""
Analyze status patterns in OLIS bills to improve status categorization
"""

import asyncio
from collections import Counter
from olis_client import OLISClient

async def analyze_status_patterns():
    """Analyze CurrentLocation patterns to improve status categorization"""
    try:
        client = OLISClient()
        
        print("🔍 Analyzing bill status patterns from 2025 Regular Session...")
        measures = await client.get_measures("2025R1", limit=100)
        
        if measures:
            # Count all CurrentLocation values
            locations = [m.get('CurrentLocation', 'Unknown') for m in measures]
            location_counts = Counter(locations)
            
            print(f"📊 Analyzed {len(measures)} bills")
            print("\n" + "=" * 80)
            print("📋 CURRENT LOCATION PATTERNS (Top 20):")
            print("=" * 80)
            
            for location, count in location_counts.most_common(20):
                print(f"{count:3d} bills: '{location}'")
            
            # Also get some history examples
            print("\n" + "=" * 80)
            print("📚 SAMPLE HISTORY ACTION PATTERNS:")
            print("=" * 80)
            
            action_texts = []
            for i, measure in enumerate(measures[:10]):
                try:
                    history = await client.get_measure_history(
                        measure['SessionKey'], 
                        measure['MeasurePrefix'], 
                        measure['MeasureNumber']
                    )
                    if history:
                        latest_action = history[0]['ActionText']
                        action_texts.append(latest_action)
                        bill_id = f"{measure['MeasurePrefix']}{measure['MeasureNumber']}"
                        print(f"{bill_id}: '{latest_action}'")
                except Exception as e:
                    print(f"Could not get history for bill {i+1}: {e}")
                    
            # Count action patterns
            print("\n" + "=" * 80)
            print("📈 ACTION TEXT PATTERNS:")
            print("=" * 80)
            action_counts = Counter(action_texts)
            for action, count in action_counts.most_common():
                print(f"{count:2d}: '{action}'")
                
        else:
            print("❌ No bills found")
            
    except Exception as e:
        print(f"❌ Error analyzing patterns: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_status_patterns())