#!/usr/bin/env python3
"""
Examine complete bill data schema from OLIS
"""

import asyncio
import json
from olis_client import OLISClient

async def examine_bill_schema():
    """Examine all available fields in OLIS bill data"""
    try:
        client = OLISClient()
        
        print("🔍 Examining complete bill data schema from 2025 Regular Session...")
        measures = await client.get_measures("2025R1", limit=3)  # Get just a few bills
        
        if measures and len(measures) > 0:
            sample_bill = measures[0]
            
            print(f"\n📊 COMPLETE BILL DATA SCHEMA:")
            print(f"Sample Bill: {sample_bill.get('MeasurePrefix', '')}{sample_bill.get('MeasureNumber', '')}")
            print("=" * 80)
            
            # Sort fields alphabetically for easier reading
            sorted_fields = sorted(sample_bill.keys())
            
            print(f"\n🔢 TOTAL FIELDS AVAILABLE: {len(sorted_fields)}")
            print("\n📋 ALL AVAILABLE FIELDS:")
            
            for i, field in enumerate(sorted_fields, 1):
                value = sample_bill.get(field)
                # Truncate long values for readability
                if isinstance(value, str) and len(value) > 100:
                    display_value = f'"{value[:100]}..."'
                elif value is None:
                    display_value = "null"
                elif isinstance(value, str):
                    display_value = f'"{value}"'
                else:
                    display_value = str(value)
                    
                print(f"{i:2d}. {field:25} = {display_value}")
            
            print("\n" + "=" * 80)
            print("📊 SAMPLE COMPLETE BILL RECORD:")
            print("=" * 80)
            
            # Show full JSON for the first bill
            print(json.dumps(sample_bill, indent=2, ensure_ascii=False))
            
            print("\n" + "=" * 80)
            print("🔍 FIELD ANALYSIS:")
            print("=" * 80)
            
            # Categorize fields by type
            metadata_fields = []
            identification_fields = []
            status_fields = []
            committee_fields = []
            content_fields = []
            date_fields = []
            author_fields = []
            other_fields = []
            
            for field in sorted_fields:
                field_lower = field.lower()
                
                if 'committee' in field_lower or 'comm' in field_lower:
                    committee_fields.append(field)
                elif any(word in field_lower for word in ['date', 'time']):
                    date_fields.append(field)
                elif any(word in field_lower for word in ['author', 'sponsor', 'chief', 'prime']):
                    author_fields.append(field)
                elif any(word in field_lower for word in ['status', 'location', 'action', 'current', 'stage']):
                    status_fields.append(field)
                elif any(word in field_lower for word in ['number', 'prefix', 'key', 'id', 'session']):
                    identification_fields.append(field)
                elif any(word in field_lower for word in ['title', 'caption', 'summary', 'digest', 'text']):
                    content_fields.append(field)
                elif any(word in field_lower for word in ['url', 'link', 'measure']):
                    metadata_fields.append(field)
                else:
                    other_fields.append(field)
            
            categories = [
                ("🔢 IDENTIFICATION FIELDS", identification_fields),
                ("📄 CONTENT FIELDS", content_fields),
                ("📍 STATUS & LOCATION FIELDS", status_fields),
                ("🏛️ COMMITTEE FIELDS", committee_fields),
                ("👥 AUTHOR/SPONSOR FIELDS", author_fields),
                ("📅 DATE/TIME FIELDS", date_fields),
                ("🔗 METADATA/URL FIELDS", metadata_fields),
                ("❓ OTHER FIELDS", other_fields)
            ]
            
            for category_name, fields in categories:
                if fields:
                    print(f"\n{category_name} ({len(fields)} fields):")
                    for field in fields:
                        value = sample_bill.get(field)
                        if isinstance(value, str) and len(value) > 50:
                            display_value = f'"{value[:50]}..."'
                        elif value is None:
                            display_value = "null"
                        elif isinstance(value, str):
                            display_value = f'"{value}"'
                        else:
                            display_value = str(value)
                        print(f"  • {field:25} = {display_value}")
                        
        else:
            print("❌ No bills found")
            
    except Exception as e:
        print(f"❌ Error examining bill schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(examine_bill_schema())