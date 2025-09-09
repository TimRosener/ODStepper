#!/usr/bin/env python3
"""
Quick test script for Phase 3 OLIS integration
"""
import asyncio
import logging
from olis_client import OLISClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_phase3_endpoints():
    """Test Phase 3 endpoints to ensure they're working"""
    client = OLISClient()
    
    # Test with a recent session (2023 Regular Session)
    test_session = "2023R1"
    
    try:
        logger.info("Testing Phase 3 OLIS endpoints...")
        
        # Test MeasureSponsors - limit to first batch only
        logger.info("1. Testing MeasureSponsors endpoint...")
        endpoint = f"MeasureSponsors?$filter=SessionKey eq '{test_session}'&$top=3&$skip=0&$orderby=MeasurePrefix,MeasureNumber,SponsorType&$format=json"
        sponsors_batch = await client._make_request(endpoint)
        sponsors = sponsors_batch.get('value', []) if isinstance(sponsors_batch, dict) else sponsors_batch[:3]
        logger.info(f"   Found {len(sponsors)} measure sponsors (sample)")
        if sponsors:
            logger.info(f"   Sample sponsor: {sponsors[0].get('MeasureSponsorId')} - {sponsors[0].get('MeasurePrefix')}{sponsors[0].get('MeasureNumber')}")
        
        # Test CommitteeProposedAmendments - limit to first batch only
        logger.info("2. Testing CommitteeProposedAmendments endpoint...")
        endpoint = f"CommitteeProposedAmendments?$filter=SessionKey eq '{test_session}'&$top=3&$skip=0&$orderby=MeetingDate&$format=json"
        amendments_batch = await client._make_request(endpoint)
        amendments = amendments_batch.get('value', []) if isinstance(amendments_batch, dict) else amendments_batch[:3]
        logger.info(f"   Found {len(amendments)} committee proposed amendments (sample)")
        if amendments:
            logger.info(f"   Sample amendment: {amendments[0].get('ProposedAmendmentId')} - {amendments[0].get('Meaning')}")
        
        # Test FloorSessionAgendaItems - limit to first batch only
        logger.info("3. Testing FloorSessionAgendaItems endpoint...")
        endpoint = f"FloorSessionAgendaItems?$filter=SessionKey eq '{test_session}'&$top=3&$skip=0&$orderby=ScheduleDate&$format=json"
        agenda_batch = await client._make_request(endpoint)
        agenda_items = agenda_batch.get('value', []) if isinstance(agenda_batch, dict) else agenda_batch[:3]
        logger.info(f"   Found {len(agenda_items)} floor session agenda items (sample)")
        if agenda_items:
            logger.info(f"   Sample agenda item: {agenda_items[0].get('AgendaId')} - {agenda_items[0].get('OrderOfBusiness')}")
        
        # Test FloorLetters - limit to first batch only
        logger.info("4. Testing FloorLetters endpoint...")
        endpoint = f"FloorLetters?$filter=SessionKey eq '{test_session}'&$top=3&$skip=0&$orderby=LetterDate&$format=json"
        letters_batch = await client._make_request(endpoint)
        letters = letters_batch.get('value', []) if isinstance(letters_batch, dict) else letters_batch[:3]
        logger.info(f"   Found {len(letters)} floor letters (sample)")
        if letters:
            logger.info(f"   Sample letter: {letters[0].get('FloorLetterId')} - {letters[0].get('LetterTitle')[:50]}...")
        
        logger.info("✅ All Phase 3 endpoints tested successfully!")
        
    except Exception as e:
        logger.error(f"❌ Phase 3 test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_phase3_endpoints())