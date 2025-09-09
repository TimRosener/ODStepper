"""
OLIS OData API client
"""
import httpx
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import quote
from tenacity import retry, stop_after_attempt, wait_exponential

import os

logger = logging.getLogger(__name__)


class OLISClient:
    """Client for interacting with OLIS OData API"""
    
    def __init__(self):
        self.base_url = os.getenv("OLIS_BASE_URL", "https://api.oregonlegislature.gov/odata/ODataService.svc/")
        self.timeout = int(os.getenv("OLIS_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("OLIS_MAX_RETRIES", "3"))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to OLIS API"""
        url = f"{self.base_url}{endpoint}"
        
        # Add format parameter for JSON
        if params is None:
            params = {}
        params["$format"] = "json"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # OData wraps results in 'd' property
                if "d" in data:
                    return data["d"]
                return data
                
            except httpx.HTTPError as e:
                logger.error(f"OLIS API error: {e}")
                raise
    
    async def get_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of legislative sessions"""
        params = {
            "$top": limit,
            "$orderby": "BeginDate desc"
        }
        
        result = await self._make_request("LegislativeSessions", params)
        
        # Handle OData result format
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        elif isinstance(result, dict) and "results" in result:
            return result["results"]
        elif isinstance(result, list):
            return result
        else:
            return []
    
    async def get_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Get specific session by key"""
        endpoint = f"LegislativeSessions('{quote(session_key)}')"
        
        try:
            return await self._make_request(endpoint)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def get_measures(
        self, 
        session_key: str,
        prefix: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get measures for a session"""
        params = {
            "$filter": f"SessionKey eq '{session_key}'",
            "$top": limit,
            "$skip": offset,
            "$orderby": "MeasureNumber"
        }
        
        if prefix:
            params["$filter"] += f" and MeasurePrefix eq '{prefix}'"
        
        result = await self._make_request("Measures", params)
        
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        elif isinstance(result, dict) and "results" in result:
            return result["results"]
        elif isinstance(result, list):
            return result
        else:
            return []
    
    async def get_measure(
        self,
        session_key: str,
        prefix: str,
        number: int
    ) -> Optional[Dict[str, Any]]:
        """Get specific measure"""
        # OData composite key format
        endpoint = f"Measures(SessionKey='{quote(session_key)}',MeasurePrefix='{quote(prefix)}',MeasureNumber={number})"
        
        try:
            return await self._make_request(endpoint)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def get_all_measures(
        self,
        session_key: str,
        prefix: Optional[str] = None,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL measures for a session using pagination"""
        all_measures = []
        offset = 0
        
        logger.info(f"Fetching all measures for session {session_key}" + 
                   (f" with prefix {prefix}" if prefix else ""))
        
        while True:
            # Get a batch of measures
            batch = await self.get_measures(
                session_key=session_key,
                prefix=prefix,
                limit=batch_size,
                offset=offset
            )
            
            if not batch:
                # No more results
                break
                
            all_measures.extend(batch)
            
            # Log progress
            logger.info(f"Fetched {len(batch)} measures (total: {len(all_measures)})")
            
            # If we got fewer results than requested, we've reached the end
            if len(batch) < batch_size:
                break
                
            # Move to next batch
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_measures)} total measures for session {session_key}")
        return all_measures
    
    async def get_measure_history(
        self,
        session_key: str,
        prefix: str,
        number: int
    ) -> List[Dict[str, Any]]:
        """Get history actions for a measure"""
        params = {
            "$filter": f"SessionKey eq '{session_key}' and MeasurePrefix eq '{prefix}' and MeasureNumber eq {number}",
            "$orderby": "ActionDate desc"
        }
        
        result = await self._make_request("MeasureHistoryActions", params)
        
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        elif isinstance(result, dict) and "results" in result:
            return result["results"]
        elif isinstance(result, list):
            return result
        else:
            return []
    
    async def get_testimony(
        self,
        session_key: str,
        prefix: str,
        number: int
    ) -> List[Dict[str, Any]]:
        """Get public testimony for a measure"""
        params = {
            "$filter": f"SessionKey eq '{session_key}' and MeasurePrefix eq '{prefix}' and MeasureNumber eq {number}",
            "$orderby": "MeetingDate desc"
        }
        
        result = await self._make_request("CommitteePublicTestimonies", params)
        
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        elif isinstance(result, dict) and "results" in result:
            return result["results"]
        elif isinstance(result, list):
            return result
        else:
            return []
    
    async def get_committees(
        self,
        session_key: str
    ) -> List[Dict[str, Any]]:
        """Get committees for a session"""
        params = {
            "$filter": f"SessionKey eq '{session_key}'",
            "$orderby": "CommitteeName"
        }
        
        result = await self._make_request("Committees", params)
        
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        elif isinstance(result, dict) and "results" in result:
            return result["results"]
        elif isinstance(result, list):
            return result
        else:
            return []
    
    async def get_measure_documents(
        self,
        session_key: str,
        prefix: str,
        number: int
    ) -> List[Dict[str, Any]]:
        """Get documents for a measure"""
        params = {
            "$filter": f"SessionKey eq '{session_key}' and MeasurePrefix eq '{prefix}' and MeasureNumber eq {number}"
        }
        
        result = await self._make_request("MeasureDocuments", params)
        
        if isinstance(result, dict) and "value" in result:
            return result["value"]
        elif isinstance(result, dict) and "results" in result:
            return result["results"]
        elif isinstance(result, list):
            return result
        else:
            return []
    
    # =========================================================================
    # PHASE 1: LEGISLATORS & VOTING ENDPOINTS
    # =========================================================================
    
    async def get_all_legislators(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL legislators for a session using pagination"""
        all_legislators = []
        offset = 0
        
        logger.info(f"Fetching all legislators for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "LastName, FirstName"
            }
            
            batch = await self._make_request("Legislators", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_legislators.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} legislators (total: {len(all_legislators)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_legislators)} total legislators for session {session_key}")
        return all_legislators
    
    async def get_all_measure_votes(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL measure votes for a session using pagination"""
        all_votes = []
        offset = 0
        
        logger.info(f"Fetching all measure votes for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "ActionDate desc, MeasurePrefix, MeasureNumber"
            }
            
            batch = await self._make_request("MeasureVotes", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_votes.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} measure votes (total: {len(all_votes)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_votes)} total measure votes for session {session_key}")
        return all_votes
    
    async def get_all_committee_votes(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL committee votes for a session using pagination"""
        all_votes = []
        offset = 0
        
        logger.info(f"Fetching all committee votes for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "MeetingDate desc, CommitteeCode"
            }
            
            batch = await self._make_request("CommitteeVotes", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_votes.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} committee votes (total: {len(all_votes)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_votes)} total committee votes for session {session_key}")
        return all_votes
    
    async def get_all_committee_members(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL committee members for a session using pagination"""
        all_members = []
        offset = 0
        
        logger.info(f"Fetching all committee members for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "CommitteeCode, LegislatorCode"
            }
            
            batch = await self._make_request("CommitteeMembers", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_members.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} committee members (total: {len(all_members)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_members)} total committee members for session {session_key}")
        return all_members
    
    async def get_all_measure_history_actions(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL measure history actions for a session using pagination"""
        all_actions = []
        offset = 0
        
        logger.info(f"Fetching all measure history actions for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "ActionDate desc, MeasurePrefix, MeasureNumber"
            }
            
            batch = await self._make_request("MeasureHistoryActions", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_actions.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} history actions (total: {len(all_actions)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_actions)} total history actions for session {session_key}")
        return all_actions    
    # =========================================================================
    # PHASE 2: MEETINGS & DOCUMENTS ENDPOINTS
    # =========================================================================
    
    async def get_all_committee_meetings(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL committee meetings for a session using pagination"""
        all_meetings = []
        offset = 0
        
        logger.info(f"Fetching all committee meetings for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "MeetingDate desc, CommitteeCode"
            }
            
            batch = await self._make_request("CommitteeMeetings", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_meetings.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} committee meetings (total: {len(all_meetings)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_meetings)} total committee meetings for session {session_key}")
        return all_meetings
    
    async def get_all_committee_agenda_items(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL committee agenda items for a session using pagination"""
        all_agenda_items = []
        offset = 0
        
        logger.info(f"Fetching all committee agenda items for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "MeetingDate desc, CommitteeCode, PrintOrder"
            }
            
            batch = await self._make_request("CommitteeAgendaItems", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_agenda_items.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} agenda items (total: {len(all_agenda_items)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_agenda_items)} total agenda items for session {session_key}")
        return all_agenda_items
    
    async def get_all_measure_documents(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL measure documents for a session using pagination"""
        all_documents = []
        offset = 0
        
        logger.info(f"Fetching all measure documents for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "MeasurePrefix, MeasureNumber, VersionDescription"
            }
            
            batch = await self._make_request("MeasureDocuments", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_documents.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} measure documents (total: {len(all_documents)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_documents)} total measure documents for session {session_key}")
        return all_documents
    
    async def get_all_committee_meeting_documents(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL committee meeting documents for a session using pagination"""
        all_documents = []
        offset = 0
        
        logger.info(f"Fetching all committee meeting documents for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "MeetingDate desc, CommitteeCode, DocumentType"
            }
            
            batch = await self._make_request("CommitteeMeetingDocuments", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_documents.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} meeting documents (total: {len(all_documents)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_documents)} total meeting documents for session {session_key}")
        return all_documents
    
    # =========================================================================
    # PHASE 3: SPONSORS & ADMINISTRATIVE DATA
    # =========================================================================
    
    async def get_all_measure_sponsors(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL measure sponsors for a session using pagination"""
        all_sponsors = []
        offset = 0
        
        logger.info(f"Fetching all measure sponsors for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "MeasurePrefix, MeasureNumber, SponsorType"
            }
            
            batch = await self._make_request("MeasureSponsors", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_sponsors.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} measure sponsors (total: {len(all_sponsors)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_sponsors)} total measure sponsors for session {session_key}")
        return all_sponsors
    
    async def get_all_committee_proposed_amendments(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL committee proposed amendments for a session using pagination"""
        all_amendments = []
        offset = 0
        
        logger.info(f"Fetching all committee proposed amendments for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "MeetingDate desc, ProposedAmendmentId"
            }
            
            batch = await self._make_request("CommitteeProposedAmendments", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_amendments.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} committee proposed amendments (total: {len(all_amendments)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_amendments)} total committee proposed amendments for session {session_key}")
        return all_amendments
    
    async def get_all_floor_session_agenda_items(
        self,
        session_key: str,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get ALL floor session agenda items for a session using pagination"""
        all_items = []
        offset = 0
        
        logger.info(f"Fetching all floor session agenda items for session {session_key}")
        
        while True:
            params = {
                "$filter": f"SessionKey eq '{session_key}'",
                "$top": batch_size,
                "$skip": offset,
                "$orderby": "ScheduleDate desc, AgendaId"
            }
            
            batch = await self._make_request("FloorSessionAgendaItems", params)
            
            if isinstance(batch, dict) and "value" in batch:
                batch_results = batch["value"]
            elif isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_items.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} floor session agenda items (total: {len(all_items)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_items)} total floor session agenda items for session {session_key}")
        return all_items

    async def get_all_floor_letters(self, session_key: str, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch all floor letters for a session with pagination.
        Floor letters are official communications from the floor about legislative matters.
        """
        logger.info(f"Starting to fetch all floor letters for session {session_key}")
        all_items = []
        offset = 0
        
        while True:
            logger.info(f"Fetching floor letters batch with offset {offset}, batch_size {batch_size}")
            
            endpoint = f"FloorLetters?$filter=SessionKey eq '{session_key}'&$top={batch_size}&$skip={offset}&$orderby=LetterDate"
            
            try:
                batch = await self._get_paginated(endpoint)
            except Exception as e:
                logger.error(f"Error fetching floor letters batch at offset {offset}: {e}")
                break
            
            # Handle both direct lists and nested results
            if isinstance(batch, dict) and "results" in batch:
                batch_results = batch["results"]
            elif isinstance(batch, list):
                batch_results = batch
            else:
                batch_results = []
            
            if not batch_results:
                break
                
            all_items.extend(batch_results)
            logger.info(f"Fetched {len(batch_results)} floor letters (total: {len(all_items)})")
            
            if len(batch_results) < batch_size:
                break
                
            offset += batch_size
        
        logger.info(f"Completed: fetched {len(all_items)} total floor letters for session {session_key}")
        return all_items
