# CRITICAL FEATURES CHECKLIST - OLIS

## ⚠️ DO NOT BREAK THESE FEATURES

This document lists all critical functionality in the OLIS application that MUST remain functional.
Before making any changes, verify that these features still work properly.

---

## 🔥 Core Features

### 1. Session Overview Dashboard
- **URL**: `/`
- **Critical Elements**:
  - [ ] Session selector dropdown loads available sessions
  - [ ] Total bills count displays correctly
  - [ ] Bill status breakdown buttons work
  - [ ] Bill type breakdown buttons work
  - [ ] Committee breakdown buttons work
  - [ ] Navigation between bill categories works

### 2. Hot Bills Section
- **Location**: Main dashboard
- **Critical Elements**:
  - [ ] Hot bills are fetched from `/api/sessions/{session}/hot-bills`
  - [ ] Heat level indicators display (🔥🌶️🔶🟡)
  - [ ] Testimony count shows correctly
  - [ ] Position breakdown displays (👍 In Favor, 👎 Against, ⚖️ Neutral, ❓ Unknown)
  - [ ] Expandable details toggle works
  - [ ] Position data uses PositionOnMeasureId mapping

### 3. System Health Monitoring
- **URL**: `/system-health`
- **Critical Elements**:
  - [ ] Health API endpoint `/api/health/detailed` returns data
  - [ ] Service status indicator updates
  - [ ] Uptime displays correctly
  - [ ] Auto-refresh every 30 seconds works
  - [ ] Refresh button works

### 4. Design Library
- **URL**: `/examples`
- **Critical Elements**:
  - [ ] Page loads with OLIS branding
  - [ ] OLIS-specific components section displays
  - [ ] Component examples render correctly

---

## 📡 API Endpoints

### Critical Backend Endpoints
- [ ] `GET /api/sessions` - Returns legislative sessions
- [ ] `GET /api/sessions/{session}/stats` - Returns session statistics
- [ ] `GET /api/sessions/{session}/hot-bills` - Returns hot bills with position breakdowns
- [ ] `GET /api/sessions/{session}/measures` - Returns bills/measures
- [ ] `GET /api/health/detailed` - Returns system health metrics
- [ ] `GET /health` - Basic health check

---

## 🗂️ Critical Files

### Backend Files (DO NOT DELETE)
- `/backend/api.py` - Main FastAPI application
- `/backend/olis_client.py` - OLIS API client
- `/backend/testimony_analysis.py` - Hot bills analysis with position detection
- `/backend/bill_status.py` - Bill status categorization
- `/backend/committee_mapping.py` - Committee categorization

### Frontend Files (DO NOT DELETE)
- `/frontend/index.html` - Main dashboard
- `/frontend/app.js` - Core JavaScript functionality
- `/frontend/health.html` - System health page
- `/frontend/style.css` - OLIS-specific styles
- `/shared/examples.html` - Design library

---

## 🔍 Position Detection Logic

### Current Implementation
- Uses `PositionOnMeasureId` values from OLIS API
- Mapping:
  - ID 3981 → Neutral
  - ID 3982 → In Favor
  - ID 3983 → Against
- Located in: `/backend/testimony_analysis.py`
- Function: `analyze_testimony_position()`

---

## 🧪 Testing Checklist

Before committing any changes, verify:

### Quick Smoke Test
```bash
# 1. Check if server is running
curl http://localhost:8001/health

# 2. Check sessions load
curl http://localhost:8001/api/sessions

# 3. Check hot bills with position data
curl http://localhost:8001/api/sessions/2025R1/hot-bills?limit=2

# 4. Check health API
curl http://localhost:8001/api/health/detailed
```

### UI Verification
1. Open http://localhost:8001/
2. Select a session from dropdown
3. Verify hot bills display with position breakdowns
4. Click System Health - verify it shows real data
5. Click Design Library - verify OLIS components show

---

## 🚨 Common Issues & Fixes

### Issue: Position breakdowns show all "unknown"
- **Cause**: PositionOnMeasureId mapping broken
- **Fix**: Check `analyze_testimony_position()` in `testimony_analysis.py`

### Issue: System Health shows template content
- **Cause**: JavaScript not connecting to API
- **Fix**: Check health.html JavaScript and `/api/health/detailed` endpoint

### Issue: Hot bills not displaying
- **Cause**: API endpoint or frontend JavaScript issue
- **Fix**: Check browser console for errors, verify API returns data

---

## 📝 Pre-Modification Checklist

### 🛡️ AUTOMATED SAFEGUARD WORKFLOW

**BEFORE making ANY changes to the system:**

```bash
# Run the automated pre-modification safety check
./pre-modification-check.sh
```

This script will:
- ✅ Verify the server is running
- ✅ Check virtual environment and test dependencies
- ✅ Run comprehensive smoke tests
- ✅ Block unsafe modifications if issues are found
- ✅ Provide clear next steps

### Manual Pre-Modification Checklist

If you prefer manual verification:
1. [ ] Run the quick smoke test: `python tests/smoke_test.py`
2. [ ] Note which feature you're modifying
3. [ ] Identify potentially affected features
4. [ ] Make your changes
5. [ ] Re-run the smoke test
6. [ ] Verify all critical features still work
7. [ ] Test the specific feature you modified

### 🧪 Available Testing Tools

1. **Pre-Modification Check** (Recommended):
   ```bash
   ./pre-modification-check.sh
   ```
   - Comprehensive safety check before making changes
   - Blocks unsafe modifications automatically
   - Provides clear pass/fail status

2. **Quick Smoke Test**:
   ```bash
   source venv/bin/activate
   python tests/smoke_test.py
   ```
   - 10-15 second verification
   - Tests all critical endpoints and UI pages

3. **Full Integration Tests**:
   ```bash
   source venv/bin/activate
   pytest tests/test_critical_features.py -v
   ```
   - Comprehensive testing with detailed assertions
   - 30-60 second runtime

---

## 🔒 Protected Patterns

### DO NOT CHANGE without careful review:
- Position ID mapping (3981, 3982, 3983)
- API endpoint structure
- Session key format (e.g., "2025R1")
- Hot bills scoring algorithm
- Database path configuration

---

## 📚 Documentation

Keep these documents updated:
- This file (CRITICAL_FEATURES.md)
- README.md - for setup and usage
- CLAUDE.md - for AI agent instructions

---

## 🔧 Recent Fixes & Updates (September 8, 2025)

### ✅ Issues Resolved This Session
1. **Hot Bills Details Toggle Fixed** 
   - **Issue**: View details button not working due to inline onclick breaking with special characters
   - **Solution**: Replaced inline onclick with event delegation using data attributes
   - **Status**: ✅ Fixed and tested

2. **Navigation System Enhanced**
   - **Issue**: Session Overview subpages disappearing after visiting System Health/Design Library
   - **Solution**: Enhanced `navigateToPage()` and `updateSidebarNavigation()` functions
   - **Status**: ✅ Fixed and tested

3. **Modal System Reverted**
   - **Issue**: Modal system not opening as expected
   - **Solution**: Reverted to original expandable inline details per user preference
   - **Status**: ✅ Reverted successfully

4. **Bill Titles Added**
   - **Enhancement**: Added bill titles to hot bills display with responsive overflow
   - **Status**: ✅ Implemented

5. **Quick Navigation Removed**
   - **Enhancement**: Cleaned up redundant Quick Navigation section
   - **Status**: ✅ Completed

### 🎯 Current System Health
- All critical features verified working ✅
- Hot bills API returning data with position breakdowns ✅
- Navigation system robust and consistent ✅
- Expandable details functioning properly ✅
- System health and design library pages accessible ✅

---

Last Updated: 2025-09-08
Version: 2.0