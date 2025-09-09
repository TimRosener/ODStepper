#!/usr/bin/env python3
"""
Examine testimony data fields for actual Position information
"""

import asyncio
import json
from olis_client import OLISClient

async def examine_testimony_fields():
    client = OLISClient()
    print('🔍 Examining testimony data fields for Position information...')
    
    # Get a sample of testimony records
    testimony_data = await client._make_request('CommitteePublicTestimonies', {
        '$filter': "SessionKey eq '2025R1'",
        '$top': 5,
        '$orderby': 'MeetingDate desc'
    })
    
    if testimony_data and 'value' in testimony_data and testimony_data['value']:
        print(f'\nFound {len(testimony_data["value"])} testimony records')
        print('\n📋 FULL FIELD STRUCTURE:')
        
        for i, record in enumerate(testimony_data['value'][:2]):
            print(f'\n--- Record {i+1} ---')
            for field, value in sorted(record.items()):
                if isinstance(value, str) and len(value) > 100:
                    display_value = f'"{value[:100]}..."'
                elif value is None:
                    display_value = 'null'
                elif isinstance(value, str):
                    display_value = f'"{value}"'
                else:
                    display_value = str(value)
                print(f'{field:30} = {display_value}')
        
        # Look for Position-related fields
        print('\n🎯 POSITION-RELATED FIELDS:')
        first_record = testimony_data['value'][0]
        position_fields = [field for field in first_record.keys() if 'position' in field.lower()]
        if position_fields:
            for field in position_fields:
                print(f'✓ Found position field: {field} = "{first_record[field]}"')
        else:
            print('❌ No fields containing "position" found in field names')
        
        # Check for common position indicators
        potential_fields = ['Position', 'TestimonyPosition', 'PositionIndicator', 'Stance', 'Support']
        print('\n🔍 CHECKING FOR POTENTIAL POSITION FIELDS:')
        for field in potential_fields:
            if field in first_record:
                print(f'✓ {field}: "{first_record[field]}"')
            else:
                print(f'❌ {field}: Not found')
        
        # Show all field names for manual inspection
        print(f'\n📝 ALL AVAILABLE FIELDS ({len(first_record)} total):')
        field_names = sorted(first_record.keys())
        for i in range(0, len(field_names), 3):
            row = field_names[i:i+3]
            print('   ' + ' | '.join(f'{field:25}' for field in row))
                
    else:
        print('❌ No testimony data found')

    # Also check if we can get specific HB2025 testimony
    print('\n\n🎯 CHECKING SPECIFIC HB2025 TESTIMONY:')
    try:
        hb2025_testimony = await client._make_request('CommitteePublicTestimonies', {
            '$filter': "SessionKey eq '2025R1' and MeasurePrefix eq 'HB' and MeasureNumber eq 2025",
            '$top': 3
        })
        
        if hb2025_testimony and 'value' in hb2025_testimony:
            print(f'Found {len(hb2025_testimony["value"])} HB2025 testimony records')
            for i, record in enumerate(hb2025_testimony['value'][:1]):
                print(f'\n--- HB2025 Record {i+1} ---')
                # Focus on potential position fields
                important_fields = ['Name', 'Organization', 'Topic', 'Position', 'TestimonyPosition', 'PositionIndicator']
                for field in important_fields:
                    if field in record:
                        value = record[field]
                        if isinstance(value, str) and len(value) > 100:
                            display_value = f'"{value[:100]}..."'
                        else:
                            display_value = f'"{value}"' if isinstance(value, str) else str(value)
                        print(f'{field:20} = {display_value}')
        else:
            print('❌ No HB2025 testimony found')
    except Exception as e:
        print(f'❌ Error getting HB2025 testimony: {e}')

if __name__ == "__main__":
    asyncio.run(examine_testimony_fields())