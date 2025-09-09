"""
OLIS OData API client
"""
import httpx
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import quote
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class OLISClient:
    """Client for interacting with OLIS OData API"""
    
    def __init__(self):
        self.base_url = settings.OLIS_BASE_URL
        self.timeout = settings.OLIS_TIMEOUT
        self.max_retries = settings.OLIS_MAX_RETRIES
    
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