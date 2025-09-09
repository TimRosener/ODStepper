#!/usr/bin/env python3
"""
Extract CommitteePublicTestimony entity definition from OLIS metadata
"""

import asyncio
import httpx
import re

async def extract_testimony_entity():
    print('🔍 Extracting CommitteePublicTestimony entity definition...')
    
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.oregonlegislature.gov/odata/ODataService.svc/$metadata', timeout=30)
        content = response.text
        
        # Find the CommitteePublicTestimony EntityType definition
        pattern = r'<EntityType Name="CommitteePublicTestimony">.*?</EntityType>'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            entity_def = match.group(0)
            print('\n📋 CommitteePublicTestimony Entity Definition:')
            print(entity_def)
            
            # Extract just the Property definitions
            property_pattern = r'<Property Name="([^"]+)" Type="([^"]+)"[^>]*/?>'
            properties = re.findall(property_pattern, entity_def)
            
            print('\n📝 Available Properties:')
            for prop_name, prop_type in properties:
                print(f'  {prop_name:25} : {prop_type}')
                
            # Look for position-related properties
            position_props = [prop for prop in properties if 'position' in prop[0].lower()]
            if position_props:
                print('\n🎯 Position-related Properties:')
                for prop_name, prop_type in position_props:
                    print(f'  ✓ {prop_name:25} : {prop_type}')
            else:
                print('\n❌ No direct position properties found')
                
        else:
            print('❌ CommitteePublicTestimony entity not found')

if __name__ == "__main__":
    asyncio.run(extract_testimony_entity())