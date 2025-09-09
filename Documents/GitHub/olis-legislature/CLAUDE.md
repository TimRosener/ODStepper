# OLIS - Oregon Legislative Information System
## AI Agent Instructions & Project Guidelines

## 🏛️ Project Overview
OLIS is a comprehensive web application that tracks Oregon legislative sessions, provides bill analytics, and displays real-time legislative information through integration with Oregon's official OLIS OData API.

## 🔒 CRITICAL: Protected Features & Files

### NEVER Break These Core Features:
1. **Hot Bills Analytics** - Advanced testimony position detection (PositionOnMeasureId: 3981=neutral, 3982=in_favor, 3983=against)
2. **Session Overview Dashboard** - Main dashboard with session selection and statistics
3. **Expandable Bill Details** - Click-to-expand details with position breakdowns 
4. **Single-Page App Navigation** - Sidebar navigation with proper state management
5. **System Health Monitoring** - Real-time API status and performance metrics
6. **Design Library** - Component showcase at `/examples`

### PROTECTED FILES - DO NOT MODIFY:
- `/shared/design-system.css` - Core design system variables
- `/shared/components.css` - Reusable UI components  
- `/shared/examples.html` - Design library reference
- `/backend/testimony_analysis.py` - Hot bills analysis logic
- `/backend/bill_status.py` - Bill status categorization
- `/backend/committee_mapping.py` - Committee categorization

## 🎯 Current System Architecture

### Backend (FastAPI on Port 8001)
- **api.py** - Main FastAPI application with OLIS endpoints
- **olis_client.py** - OLIS API client and data fetching
- **testimony_analysis.py** - Hot bills scoring with position detection
- **bill_status.py** - Bill status categorization logic
- **committee_mapping.py** - Committee categorization logic

### Frontend (Single-Page Application)
- **index.html** - Main OLIS legislative dashboard
- **app.js** - Interactive JavaScript with SPA routing and event delegation
- **style.css** - OLIS-specific styles following design system
- **health.html** - System health monitoring page

### API Endpoints (DO NOT BREAK)
```
GET  /health                              # Health check
GET  /api/health/detailed                 # System health metrics
GET  /api/sessions                        # Available legislative sessions
GET  /api/sessions/{session}/stats        # Session statistics
GET  /api/sessions/{session}/hot-bills    # Hot bills with position breakdowns
GET  /api/sessions/{session}/measures     # All bills/measures for session
```

## 🔧 Recent Fixes & Current Status (September 8, 2025)

### ✅ Recently Resolved Issues:
1. **Hot Bills Details Toggle** - Fixed using event delegation instead of inline onclick
2. **Navigation System** - Fixed submenu disappearing after visiting external pages
3. **Modal System** - Reverted to expandable inline details per user preference
4. **Bill Titles** - Added responsive bill title display in hot bills
5. **Quick Navigation** - Removed redundant navigation section

### 🎯 Current Working Features:
- Hot bills analytics with position breakdowns ✅
- Expandable bill details (click ▼ Details button) ✅ 
- Session switching with automatic data refresh ✅
- Sidebar navigation with proper state management ✅
- System health monitoring at `/system-health` ✅
- Design library at `/examples` ✅

## 🚨 AI Agent Guidelines

### Before Making ANY Changes:
1. **Run pre-modification check**: `./pre-modification-check.sh`
2. **Read CRITICAL_FEATURES.md** to understand protected functionality
3. **Check current system status** with smoke tests: `python tests/smoke_test.py`

### When Implementing Changes:
- **ALWAYS** use the design system variables (--primary, --space-4, etc.)
- **NEVER** use inline styles or hardcoded colors
- **FOLLOW** existing patterns in app.js for JavaScript functionality
- **PRESERVE** the single-page app routing and event delegation patterns
- **MAINTAIN** the PositionOnMeasureId mapping (3981=neutral, 3982=in_favor, 3983=against)

### After Changes:
- **RUN** smoke tests to verify nothing broke: `python tests/smoke_test.py`
- **TEST** critical features manually in browser
- **UPDATE** documentation if necessary

## 🔍 Testing & Validation

### Quick System Verification:
```bash
# Verify server running and all endpoints working
python tests/smoke_test.py

# Comprehensive feature testing
pytest tests/test_critical_features.py -v

# Safety check before modifications
./pre-modification-check.sh
```

### Manual Testing Checklist:
1. Navigate to http://localhost:8001/
2. Select 2025R1 session from dropdown
3. Verify hot bills load with position breakdowns
4. Click "Details" button on any hot bill - should expand inline
5. Navigate to System Health - should work and show real data
6. Navigate to Design Library - should work and show OLIS components
7. Return to Session Overview - submenu should reappear properly

## 🎨 Design System Usage

### Required CSS Import Order:
```html
<link rel="stylesheet" href="/shared/design-system.css">
<link rel="stylesheet" href="/shared/components.css">
<link rel="stylesheet" href="/static/style.css">
```

### OLIS-Specific Colors:
- Hot bills heat levels: 🔥 Blazing, 🌶️ Very Hot, 🔶 Moderate, 🟡 Warm
- Position indicators: 👍 In Favor, 👎 Against, ⚖️ Neutral, ❓ Unknown
- Status indicators: Use design system success/warning/danger colors

## 🚨 Common Pitfalls to Avoid

### JavaScript Issues:
- ❌ Don't use inline onclick handlers - use event delegation
- ❌ Don't break the SPA routing system 
- ❌ Don't modify the sidebar navigation state management
- ❌ Don't hardcode bill IDs or session keys

### CSS Issues:
- ❌ Don't use inline styles or custom colors
- ❌ Don't modify protected files in `/shared/`
- ❌ Don't break responsive design patterns
- ❌ Don't override design system components

### Backend Issues:
- ❌ Don't break the PositionOnMeasureId mapping
- ❌ Don't modify the hot bills scoring algorithm
- ❌ Don't change API endpoint signatures
- ❌ Don't break the OLIS API integration

## 🔄 Future Enhancement Guidelines

When adding new features:
1. **Follow existing patterns** in testimony_analysis.py and app.js
2. **Use the design system** components and variables consistently
3. **Add appropriate tests** to critical feature test suite
4. **Update CRITICAL_FEATURES.md** if adding protected functionality
5. **Maintain responsive design** and accessibility standards

## 📚 Key Documentation Files

- **README.md** - Project overview, setup instructions, current features
- **CRITICAL_FEATURES.md** - Protected functionality and testing checklist
- **This file (CLAUDE.md)** - AI agent instructions and project guidelines

## 🎯 Success Criteria

The OLIS system is successful when:
- All legislative data loads correctly from Oregon's OLIS API
- Hot bills analysis provides accurate position breakdowns
- Navigation is smooth and consistent across all pages
- System health monitoring shows real-time API status
- All critical features pass automated and manual testing
- Design system provides consistent visual experience
- Performance remains fast and responsive

---

## 🤖 Remember: 
This is a production legislative information system. Stability and accuracy are paramount. Always test thoroughly and preserve the existing functionality that users depend on.

Last Updated: September 8, 2025 
Version: 2.0