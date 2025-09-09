#!/usr/bin/env python3
"""
Integration tests for critical OLIS features

These tests verify that critical functionality remains working after changes.
Based on CRITICAL_FEATURES.md checklist.
"""

import asyncio
import httpx
import pytest
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8001"
TIMEOUT = 30.0


class TestCriticalEndpoints:
    """Test all critical API endpoints listed in CRITICAL_FEATURES.md"""
    
    @pytest.fixture
    async def client(self):
        """HTTP client for API testing"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            yield client
    
    async def test_health_endpoint(self, client):
        """Test basic health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_detailed_health_endpoint(self, client):
        """Test detailed health metrics endpoint"""
        response = await client.get("/api/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
        
        # Check required health metrics
        health_data = data["data"]
        assert "status" in health_data
        assert "uptime_seconds" in health_data
        assert "memory_mb" in health_data
    
    async def test_sessions_endpoint(self, client):
        """Test legislative sessions endpoint"""
        response = await client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least current session
        assert len(data) > 0
        
        # Check session structure
        session = data[0]
        assert "SessionKey" in session
        assert "SessionName" in session
    
    async def test_session_stats_endpoint(self, client):
        """Test session statistics endpoint"""
        # First get available sessions
        sessions_response = await client.get("/api/sessions")
        sessions = sessions_response.json()
        
        if sessions:
            session_key = sessions[0]["SessionKey"]
            response = await client.get(f"/api/sessions/{session_key}/stats")
            assert response.status_code == 200
            data = response.json()
            
            # Check stats structure
            assert "total_bills" in data
            assert "bill_status_breakdown" in data
            assert "bill_type_breakdown" in data
            assert "committee_breakdown" in data
    
    async def test_hot_bills_endpoint(self, client):
        """Test hot bills endpoint with position breakdowns"""
        # First get available sessions
        sessions_response = await client.get("/api/sessions")
        sessions = sessions_response.json()
        
        if sessions:
            session_key = sessions[0]["SessionKey"]
            response = await client.get(f"/api/sessions/{session_key}/hot-bills?limit=5")
            assert response.status_code == 200
            data = response.json()
            
            # Check hot bills structure
            assert "hot_bills" in data
            assert "total_testimonies" in data
            assert "bills_with_testimony" in data
            
            # Check position breakdown in hot bills
            if data["hot_bills"]:
                hot_bill = data["hot_bills"][0]
                assert "position_breakdown" in hot_bill
                assert "testimony_count" in hot_bill
                assert "heat_level" in hot_bill
                
                # Verify position mapping is working
                positions = hot_bill["position_breakdown"]
                assert "in_favor" in positions
                assert "against" in positions
                assert "neutral" in positions
                assert "unknown" in positions
    
    async def test_measures_endpoint(self, client):
        """Test measures/bills endpoint"""
        # First get available sessions
        sessions_response = await client.get("/api/sessions")
        sessions = sessions_response.json()
        
        if sessions:
            session_key = sessions[0]["SessionKey"]
            response = await client.get(f"/api/sessions/{session_key}/measures?limit=10")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


class TestPositionDetectionLogic:
    """Test the critical position detection logic"""
    
    def test_position_mapping_constants(self):
        """Verify position ID mapping constants are correct"""
        # Import the actual function from testimony_analysis
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
        
        from testimony_analysis import analyze_testimony_position
        
        # Test known position IDs
        test_cases = [
            ({"PositionOnMeasureId": 3981}, "neutral"),
            ({"PositionOnMeasureId": 3982}, "in_favor"),
            ({"PositionOnMeasureId": 3983}, "against"),
            ({"PositionOnMeasureId": 9999}, "unknown"),  # Unknown ID
            ({}, "unknown"),  # Missing ID
            ({"PositionOnMeasureId": None}, "unknown"),  # Null ID
        ]
        
        for testimony_record, expected_position in test_cases:
            result = analyze_testimony_position(testimony_record)
            assert result == expected_position, f"Failed for {testimony_record}: expected {expected_position}, got {result}"


class TestUIPages:
    """Test critical UI pages load correctly"""
    
    @pytest.fixture
    async def client(self):
        """HTTP client for UI testing"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT, follow_redirects=True) as client:
            yield client
    
    async def test_main_dashboard_loads(self, client):
        """Test main dashboard loads without errors"""
        response = await client.get("/")
        assert response.status_code == 200
        content = response.text
        
        # Check for OLIS-specific content
        assert "OLIS" in content
        assert "Oregon Legislative Information System" in content
        assert "Session Overview" in content
        
        # Should NOT contain template placeholders
        assert "[App Name]" not in content
        assert "Starter Template" not in content
    
    async def test_system_health_page_loads(self, client):
        """Test System Health page loads with OLIS content"""
        response = await client.get("/system-health")
        assert response.status_code == 200
        content = response.text
        
        # Check for OLIS-specific health content
        assert "OLIS" in content
        assert "System Health" in content
        assert "Service Status" in content
        
        # Should NOT contain template placeholders
        assert "[App Name]" not in content
        assert "Starter Template" not in content
        
        # Should have JavaScript to connect to API
        assert "/api/health/detailed" in content
        assert "fetchHealthData" in content
    
    async def test_design_library_loads(self, client):
        """Test Design Library loads with OLIS components"""
        response = await client.get("/examples")
        assert response.status_code == 200
        content = response.text
        
        # Check for OLIS-specific design library content
        assert "OLIS" in content
        assert "Design Library" in content
        
        # Should NOT contain generic template content
        assert "[App Name]" not in content
        assert "Starter Template" not in content
        
        # Should have OLIS-specific components
        assert "Hot Bills" in content or "OLIS Components" in content


# Test runner configuration
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])