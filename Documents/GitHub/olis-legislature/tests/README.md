# OLIS Integration Tests

This directory contains integration tests and safeguards to prevent regression when updating the OLIS system.

## Purpose

These tests directly address the critical safeguard requirement: **"ensure that when we are updating one section of the system, that we are not eliminating functionality in another"**

## Test Files

### `smoke_test.py` - Quick Verification
- **Purpose**: Fast automated version of the smoke test checklist from `CRITICAL_FEATURES.md`
- **Usage**: Run before and after making changes
- **Runtime**: ~10-15 seconds
- **Command**: `python tests/smoke_test.py`

**What it tests**:
- ✅ Server health endpoint
- ✅ Legislative sessions API
- ✅ Hot bills with position breakdowns (validates PositionOnMeasureId mapping)
- ✅ Detailed health metrics API
- ✅ Main dashboard loads with OLIS content (not template placeholders)
- ✅ System health page connects to real API
- ✅ Design library shows OLIS components

### `test_critical_features.py` - Comprehensive Testing
- **Purpose**: Full integration test suite using pytest
- **Usage**: Thorough testing with detailed assertions
- **Runtime**: ~30-60 seconds
- **Command**: `pytest tests/test_critical_features.py -v`

**What it tests**:
- 🔍 All critical API endpoints from `CRITICAL_FEATURES.md`
- 🔍 Position detection logic (validates ID mapping 3981=neutral, 3982=in_favor, 3983=against)
- 🔍 UI page content verification (ensures no template placeholders)
- 🔍 Data structure validation for hot bills and session stats

## Installation

Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

Or if using a virtual environment:
```bash
source venv/bin/activate
pip install -r tests/requirements.txt
```

## Running Tests

### Quick Smoke Test (Recommended for regular use)
```bash
# Quick verification - use this before/after changes
python tests/smoke_test.py
```

### Full Integration Tests
```bash
# Comprehensive testing
pytest tests/test_critical_features.py -v

# Run specific test classes
pytest tests/test_critical_features.py::TestCriticalEndpoints -v
pytest tests/test_critical_features.py::TestPositionDetectionLogic -v
pytest tests/test_critical_features.py::TestUIPages -v
```

### Integration with Development Workflow

Add to your pre-change checklist:
```bash
# 1. Run smoke test before changes
python tests/smoke_test.py

# 2. Make your changes
# ... development work ...

# 3. Run smoke test after changes
python tests/smoke_test.py

# 4. If smoke test passes, optionally run full test suite
pytest tests/test_critical_features.py -v
```

## Test Requirements

**Server must be running** at `http://localhost:8001` for tests to work:
```bash
# Start the OLIS server (from project root)
cd backend
python -m uvicorn api:app --reload --port 8001
```

## Expected Results

### Healthy System
```
🔍 OLIS Critical Features Smoke Test
==================================================
1️⃣  Testing server health...
   ✅ Server is running

2️⃣  Testing sessions API...
   ✅ Found 3 legislative sessions

3️⃣  Testing hot bills with position breakdowns...
   ✅ Position mapping working: 45 known, 12 unknown positions

4️⃣  Testing detailed health API...
   ✅ Detailed health API working

5️⃣  Testing UI pages...
   ✅ Main dashboard loads with OLIS content
   ✅ System health page loads with real API connection
   ✅ Design library page loads with OLIS content

📊 SMOKE TEST SUMMARY
✅ Passed: 7
⚠️  Warnings: 0
❌ Failed: 0

✅ ALL TESTS PASSED - System ready for changes
```

### System with Issues
```
📊 SMOKE TEST SUMMARY
✅ Passed: 4
⚠️  Warnings: 1
❌ Failed: 2

❌ CRITICAL ISSUES DETECTED:
   • Hot bills API (status: 500)
   • System health page (may show template content)

🔧 ACTION REQUIRED: Review failed tests before proceeding with changes
```

## Protected Features

These tests specifically verify the features that were broken when updating other parts:

1. **Position Detection**: Ensures `PositionOnMeasureId` mapping works (3981=neutral, 3982=in_favor, 3983=against)
2. **System Health Page**: Verifies it shows real OLIS data, not template content
3. **Design Library**: Ensures it shows OLIS components, not generic examples
4. **Hot Bills Display**: Validates position breakdowns appear correctly
5. **API Connectivity**: Confirms all critical endpoints remain functional

## Maintenance

Update tests when:
- ✅ New critical features are added to `CRITICAL_FEATURES.md`
- ✅ API endpoints change
- ✅ Position ID mapping is updated
- ✅ New UI pages are added
- ✅ Critical bugs are discovered and fixed

## Integration with CI/CD

These tests are designed to be run in automated pipelines:
```bash
# Example CI script
python tests/smoke_test.py || exit 1
pytest tests/test_critical_features.py || exit 1
```