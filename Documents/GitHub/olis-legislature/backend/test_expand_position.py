#!/usr/bin/env python3
"""
Test using OData $expand to get position data through navigation properties
"""

import asyncio
import json
from olis_client import OLISClient

async def test_expand_position():
    client = OLISClient()
    print('🔍 Testing OData $expand to access position data...')
    
    # Try different expand approaches
    expand_tests = [
        # Direct expand attempt
        {
            'name': 'Direct PositionOnMeasure expand',
            'params': {
                '$filter': "SessionKey eq '2025R1'",
                '$top': 3,
                '$expand': 'PositionOnMeasure'
            }
        },
        # Try different navigation property names
        {
            'name': 'Position expand',
            'params': {
                '$filter': "SessionKey eq '2025R1'",
                '$top': 3, 
                '$expand': 'Position'
            }
        },
        # Multiple expands
        {
            'name': 'Committee expand (known to work)',
            'params': {
                '$filter': "SessionKey eq '2025R1'",
                '$top': 2,
                '$expand': 'Committee'
            }
        }
    ]
    
    for test in expand_tests:
        print(f"\n🧪 {test['name']}...")
        try:
            result = await client._make_request('CommitteePublicTestimonies', test['params'])
            
            if result and 'value' in result and result['value']:
                print(f"✅ SUCCESS! Got {len(result['value'])} records")
                
                # Check first record for expanded data
                first_record = result['value'][0]
                print(f"📋 Fields in first record: {len(first_record)}")
                
                # Look for position-related expanded data
                for field, value in first_record.items():
                    if isinstance(value, dict) and value:  # Expanded object
                        print(f"🔗 Expanded field '{field}':")
                        for sub_field, sub_value in value.items():
                            print(f"    {sub_field}: {sub_value}")
                    elif 'position' in field.lower():
                        print(f"🎯 Position field '{field}': {value}")
                        
            else:
                print("❌ No data returned")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
    
    # Try manual construction of position lookup
    print(f"\n🔍 Manual Position Lookup Test...")
    try:
        # Get testimony records with PositionOnMeasureId
        testimony = await client._make_request('CommitteePublicTestimonies', {
            '$filter': "SessionKey eq '2025R1'",
            '$top': 5
        })
        
        if testimony and 'value' in testimony:
            position_ids = []
            for record in testimony['value']:
                pos_id = record.get('PositionOnMeasureId')
                if pos_id and pos_id not in position_ids:
                    position_ids.append(pos_id)
            
            print(f"Found PositionOnMeasureId values: {position_ids}")
            
            # Try to construct a separate lookup (this will likely fail, but worth trying)
            if position_ids:
                print(f"Attempting to look up position ID {position_ids[0]}...")
                try:
                    position_lookup = await client._make_request('PositionOnMeasure', {
                        '$filter': f'PositionOnMeasureId eq {position_ids[0]}'
                    })
                    print(f"✅ Position lookup successful: {position_lookup}")
                except Exception as e:
                    print(f"❌ Position lookup failed: {str(e)[:100]}")
    
    except Exception as e:
        print(f"❌ Manual lookup error: {e}")
    
    # Check metadata for navigation properties
    print(f"\n🔍 Checking navigation properties in metadata...")
    try:
        import httpx
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get('https://api.oregonlegislature.gov/odata/ODataService.svc/$metadata')
            content = response.text
            
            # Look for CommitteePublicTestimony navigation properties
            import re
            nav_pattern = r'<NavigationProperty[^>]*Name="([^"]+)"[^>]*ToRole="([^"]+)"[^>]*FromRole="CommitteePublicTestimony"[^>]*/?>'
            nav_properties = re.findall(nav_pattern, content)
            
            if nav_properties:
                print("Available navigation properties from CommitteePublicTestimony:")
                for nav_name, to_role in nav_properties:
                    print(f"  {nav_name} -> {to_role}")
            else:
                print("No navigation properties found for CommitteePublicTestimony")
                
    except Exception as e:
        print(f"❌ Metadata check error: {e}")

if __name__ == "__main__":
    asyncio.run(test_expand_position())