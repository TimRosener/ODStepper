#!/usr/bin/env python3
"""
Script to examine the structure of bill data from OLIS API
"""

import asyncio
import json
from olis_client import OLISClient

async def examine_bill_structure():
    """Examine the data structure of bills and their history"""
    try:
        client = OLISClient()
        
        # Get measures from 2025 Regular Session
        print("🔍 Fetching sample bills from 2025 Regular Session...")
        measures = await client.get_measures("2025R1", limit=5)
        
        if measures:
            print(f"📊 Found {len(measures)} sample bills\n")
            
            # Show structure of first bill
            first_bill = measures[0]
            print("=" * 80)
            print("📄 SAMPLE BILL DATA STRUCTURE:")
            print("=" * 80)
            print(json.dumps(first_bill, indent=2, default=str))
            print("\n" + "=" * 80)
            
            # Get history for this bill
            print("📚 BILL HISTORY DATA STRUCTURE:")
            print("=" * 80)
            try:
                history = await client.get_measure_history(
                    first_bill['SessionKey'], 
                    first_bill['MeasurePrefix'], 
                    first_bill['MeasureNumber']
                )
                
                if history:
                    print(f"Found {len(history)} history actions")
                    print("\nLatest action:")
                    print(json.dumps(history[0], indent=2, default=str))
                    
                    print("\n📋 ALL AVAILABLE FIELDS IN MEASURE:")
                    for key in sorted(first_bill.keys()):
                        value = first_bill[key]
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"  • {key}: {value}")
                    
                    print("\n📋 ALL AVAILABLE FIELDS IN HISTORY ACTION:")
                    for key in sorted(history[0].keys()):
                        value = history[0][key]
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"  • {key}: {value}")
                        
                else:
                    print("No history found for this bill")
                    
            except Exception as e:
                print(f"Could not fetch history: {e}")
            
            # Show a few more bills with their current locations
            print("\n" + "=" * 80)
            print("📊 SAMPLE BILL LOCATIONS FOR STATUS ANALYSIS:")
            print("=" * 80)
            for i, bill in enumerate(measures[:5]):
                prefix = bill.get('MeasurePrefix', '')
                number = bill.get('MeasureNumber', '')
                location = bill.get('CurrentLocation', 'Unknown')
                print(f"{i+1}. {prefix}{number}: '{location}'")
            
        else:
            print("❌ No bills found")
            
    except Exception as e:
        print(f"❌ Error examining bill structure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(examine_bill_structure())