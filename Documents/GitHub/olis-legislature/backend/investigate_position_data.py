#!/usr/bin/env python3
"""
Investigate PositionOnMeasure data to get actual position values
"""

import asyncio
import json
from olis_client import OLISClient

async def investigate_position_data():
    client = OLISClient()
    print('🔍 Investigating PositionOnMeasure data structure...')
    
    # First, get some PositionOnMeasureId values from testimony
    print('\n1️⃣ Getting testimony records with PositionOnMeasureId...')
    testimony_data = await client._make_request('CommitteePublicTestimonies', {
        '$filter': "SessionKey eq '2025R1'",
        '$top': 10,
        '$orderby': 'MeetingDate desc'
    })
    
    position_ids = []
    if testimony_data and 'value' in testimony_data:
        for record in testimony_data['value']:
            pos_id = record.get('PositionOnMeasureId')
            if pos_id and pos_id not in position_ids:
                position_ids.append(pos_id)
        
        print(f'Found position IDs: {position_ids[:5]}')
    
    # Now try to get PositionOnMeasure data
    print('\n2️⃣ Attempting to access PositionOnMeasure endpoint...')
    try:
        position_data = await client._make_request('PositionOnMeasure', {
            '$top': 5
        })
        
        if position_data and 'value' in position_data and position_data['value']:
            print(f'✓ SUCCESS! Found {len(position_data["value"])} position records')
            
            print('\n📋 POSITION DATA STRUCTURE:')
            first_pos = position_data['value'][0]
            for field, value in sorted(first_pos.items()):
                print(f'{field:25} = "{value}"')
            
            print(f'\n📝 ALL POSITION RECORDS:')
            for i, pos in enumerate(position_data['value']):
                pos_id = pos.get('PositionOnMeasureId', 'Unknown')
                position_text = pos.get('Position', pos.get('PositionText', pos.get('Name', 'Unknown')))
                print(f'{i+1}. ID: {pos_id} | Position: "{position_text}"')
                
        else:
            print('❌ No position data returned')
            
    except Exception as e:
        print(f'❌ Error accessing PositionOnMeasure: {e}')
    
    # Try specific position IDs if we have them
    if position_ids:
        print(f'\n3️⃣ Trying to get specific position record ID {position_ids[0]}...')
        try:
            specific_pos = await client._make_request('PositionOnMeasure', {
                '$filter': f"PositionOnMeasureId eq {position_ids[0]}"
            })
            
            if specific_pos and 'value' in specific_pos and specific_pos['value']:
                print('✓ Found specific position record:')
                pos_record = specific_pos['value'][0]
                for field, value in sorted(pos_record.items()):
                    print(f'{field:25} = "{value}"')
            else:
                print('❌ No specific position record found')
                
        except Exception as e:
            print(f'❌ Error getting specific position: {e}')
    
    # Try different endpoint names
    print('\n4️⃣ Trying alternative position endpoint names...')
    alternative_endpoints = [
        'Positions', 
        'MeasurePositions', 
        'TestimonyPositions',
        'PositionTypes',
        'PositionLookup'
    ]
    
    for endpoint in alternative_endpoints:
        try:
            print(f'\nTrying {endpoint}...')
            alt_data = await client._make_request(endpoint, {'$top': 3})
            
            if alt_data and 'value' in alt_data and alt_data['value']:
                print(f'✓ SUCCESS with {endpoint}! Found {len(alt_data["value"])} records')
                first_record = alt_data['value'][0]
                for field, value in sorted(first_record.items()):
                    if isinstance(value, str) and len(value) > 50:
                        display_value = f'"{value[:50]}..."'
                    else:
                        display_value = f'"{value}"' if isinstance(value, str) else str(value)
                    print(f'  {field:20} = {display_value}')
                break
            else:
                print(f'❌ {endpoint}: No data')
                
        except Exception as e:
            print(f'❌ {endpoint}: {str(e)[:50]}...')

if __name__ == "__main__":
    asyncio.run(investigate_position_data())