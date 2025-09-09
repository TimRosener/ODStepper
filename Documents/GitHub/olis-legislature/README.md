# OLIS - Oregon Legislative Information System

A comprehensive web application for tracking Oregon legislative sessions, bills, and providing real-time legislative information with advanced analytics. Built with the company's unified design system and integrated with the official OLIS OData API.

## ✨ Current Features (December 2025)

- 🚀 **One-command startup** - Everything runs with `./start.sh`
- 🏛️ **Legislative session tracking** - View current and historical Oregon Legislature sessions (2023R1, 2024R1, 2025R1)
- 📊 **Bill statistics** - Real-time counts of bills by status, type, and committee
- 🔥 **Hot Bills Analytics** - Advanced testimony analysis with position breakdowns (In Favor, Against, Neutral)
- 🔄 **Dynamic session switching** - Select different sessions with automatic data updates
- 📋 **Expandable Bill Details** - Click-to-expand details showing position breakdowns, submitter types, and timeline analysis
- 🗂️ **Category Navigation** - Organized by Bill Status, Bill Types, House/Senate/Joint Committees
- 🏥 **System Health Monitoring** - Real-time API connection status and performance metrics
- 🎨 **Design Library** - Complete component showcase and design system documentation
- 🎨 **Unified design system** - Consistent styling across all company applications  
- 📦 **OLIS API integration** - Direct connection to Oregon's official legislative data with PositionOnMeasureId mapping
- 🌐 **Modern frontend** - Interactive SPA with robust client-side routing
- 📱 **Mobile responsive** - Works perfectly on all screen sizes

### 🗄️ NEW: Database Management System (September 2025)
- 🏗️ **PostgreSQL Integration** - Complete OLIS data mirroring with 25-field bill schema
- 👥 **Multi-tenant User Management** - Company-based access control with role-based permissions
- 🔐 **User Authentication System** - Secure user accounts with password hashing and session management
- 🏢 **Company Management** - Organize users by companies with configurable access levels
- ⭐ **User Preferences** - Personalized hot bills tracking, notification settings, and dashboard customization
- 📊 **Activity Tracking** - Comprehensive audit trails and user activity logging
- 🔔 **Alert System** - Configurable notifications for bill status changes and deadlines
- 📈 **Advanced Analytics** - Company-level bill priorities and tracking metrics
- 🔄 **Database Migrations** - Alembic-powered schema management and version control

### 🎉 NEW: Complete OLIS API Coverage (September 2025)
- 🏛️ **100% OLIS Integration** - All 13 major OLIS endpoints implemented and tested
- 📋 **Phase 3 Administrative Data** - Sponsors, amendments, floor schedules, and communications
- 🔗 **MeasureSponsors** - Complete bill sponsorship tracking with legislator relationships
- 📝 **CommitteeProposedAmendments** - Amendment proposals with documents and URLs
- 📅 **FloorSessionAgendaItems** - Floor session scheduling with chamber and completion status
- 📄 **FloorLetters** - Floor communications and document management
- ⚡ **Batch Processing** - Efficient handling of 200,000+ legislative records
- 🔄 **Comprehensive Sync** - Full synchronization across all legislative sessions
- 📊 **Advanced Statistics** - Complete tracking and reporting across all data types

## 🚀 Quick Start

1. **Start the application**:
   ```bash
   ./start.sh
   ```
2. **Open your browser** to http://localhost:8001
3. **Select a legislative session** from the dropdown (2025R1 recommended)
4. **Explore the hot bills** and click "Details" to see testimony breakdowns

The **start script** will:
- Create a Python virtual environment (if needed)
- Install dependencies automatically (FastAPI, requests, uvicorn, etc.)
- Start the backend API server on port 8001
- Open the OLIS dashboard
- Handle graceful shutdown with Ctrl+C

## 🏗️ Project Structure

```
olis-legislature/
├── backend/
│   ├── api.py                      # FastAPI app with OLIS endpoints
│   ├── olis_client.py             # Complete OLIS API client (13 endpoints)
│   ├── olis_sync_service.py       # Comprehensive sync service for all OLIS data
│   ├── testimony_analysis.py      # Hot bills analysis with position detection  
│   ├── bill_status.py             # Bill status categorization
│   ├── committee_mapping.py       # Committee categorization
│   ├── database_config.py         # PostgreSQL database configuration
│   ├── database/                   # Complete database management system
│   │   ├── models_with_analysis.py # All OLIS SQLAlchemy models (Phase 1-3)
│   │   ├── postgres_schema.sql    # Complete PostgreSQL schema definition
│   │   ├── alembic.ini            # Database migration configuration
│   │   └── migrations/            # Database migration scripts (8 migrations)
│   │       ├── env.py             # Alembic environment setup
│   │       ├── script.py.mako     # Migration script template
│   │       └── versions/          # Migration version files
│   ├── test_phase3.py             # Phase 3 endpoint testing suite
│   ├── examine_bill_schema.py     # OLIS API schema analysis tool
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── index.html                 # OLIS legislative dashboard
│   ├── app.js                     # Interactive JavaScript with SPA routing
│   ├── style.css                  # OLIS-specific styles
│   ├── health.html                # System health monitoring page
├── shared/                        # DO NOT MODIFY THESE FILES
│   ├── design-system.css          # Core design system variables
│   ├── components.css             # Reusable UI components
│   └── examples.html              # Design library and component guide
├── tests/
│   ├── smoke_test.py              # Quick system verification tests
│   ├── test_critical_features.py # Comprehensive integration tests
├── .validation/
│   ├── strict-validator.py       # Code quality enforcement
│   └── install-hooks.sh          # Git hooks installer
├── start.sh                       # One-command startup script
├── pre-modification-check.sh      # Safety check before changes
├── CRITICAL_FEATURES.md           # Protected functionality documentation
└── CLAUDE.md                      # AI agent instructions
```

## 🏛️ OLIS Legislative System

### Backend Features
- **OLIS API Integration** - Direct connection to Oregon's official legislative data
- **Hot Bills Analytics** - Advanced testimony analysis with position detection
- **Real-time Data Fetching** - Live session and bill data from OLIS servers
- **Position Mapping** - PositionOnMeasureId mapping (3981=neutral, 3982=in_favor, 3983=against)
- **Committee Categorization** - Automatic sorting by House, Senate, and Joint committees
- **Bill Status Tracking** - Real-time bill status across the legislative process
- **System Health Monitoring** - API connection status and performance metrics

### Frontend Features  
- **Interactive Dashboard** - Session overview with hot bills and statistics
- **Expandable Bill Details** - Click to reveal position breakdowns and submitter analysis
- **Dynamic Navigation** - Single-page app with smooth transitions between categories
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Real-time Updates** - Session switching with automatic data refresh
- **Design System** - Consistent UI components and styling

### API Endpoints

#### Core OLIS API
```
GET  /health                              # Health check
GET  /api/health/detailed                 # Detailed system health metrics
GET  /api/sessions                        # Available legislative sessions
GET  /api/sessions/{session}/stats        # Session statistics and bill counts
GET  /api/sessions/{session}/hot-bills    # Hot bills with position breakdowns
GET  /api/sessions/{session}/measures     # All bills/measures for session
```

#### NEW: Database Management API
```
# User Management
POST /api/auth/login                      # User authentication
POST /api/auth/logout                     # User logout
GET  /api/users/profile                   # User profile information
PUT  /api/users/profile                   # Update user profile
GET  /api/users/preferences               # User preferences
PUT  /api/users/preferences               # Update preferences

# Company Management
GET  /api/companies                       # List user's companies
POST /api/companies                       # Create new company
GET  /api/companies/{id}                  # Company details
PUT  /api/companies/{id}                  # Update company
GET  /api/companies/{id}/users            # Company users
POST /api/companies/{id}/users            # Add user to company

# Bill Tracking & Analytics
GET  /api/tracking/hot-bills              # User's tracked hot bills
POST /api/tracking/hot-bills              # Add bill to tracking
DELETE /api/tracking/hot-bills/{id}       # Remove from tracking
GET  /api/analytics/company/{id}          # Company bill analytics
GET  /api/alerts                          # User notifications
POST /api/alerts                          # Create alert rule
```

## 🗄️ Database Management System

### PostgreSQL Schema Architecture

The system implements a comprehensive PostgreSQL database that mirrors the complete OLIS API structure while adding multi-tenant user management capabilities:

#### Complete OLIS Data Mirror (13 Entity Types, 200,000+ Records)

**Phase 1: Core Legislative Data**
- **Legislative Sessions** - Current and historical Oregon Legislature sessions
- **Measures (Bills)** - Complete 25-field bill structure with identification, content, status, dates
- **Legislators** - Legislative members with party, district, and chamber information
- **MeasureVotes** - Floor voting records with individual legislator positions
- **CommitteeVotes** - Committee voting records with member positions

**Phase 2: Meetings & Documents**  
- **CommitteeMembers** - Committee membership assignments and roles
- **MeasureHistoryActions** - Complete bill action history and timeline
- **CommitteeMeetings** - Meeting schedules with audio/video URLs
- **CommitteeAgendaItems** - Detailed meeting agendas with bill references
- **MeasureDocuments** - Bill documents, analysis, and fiscal impacts
- **CommitteeMeetingDocuments** - Meeting minutes, exhibits, and materials

**Phase 3: Administrative & Workflow**
- **MeasureSponsors** - Bill sponsorship with primary/co-sponsor relationships
- **CommitteeProposedAmendments** - Amendment proposals with documents and URLs
- **FloorSessionAgendaItems** - Floor session scheduling with chamber tracking
- **FloorLetters** - Floor communications and official correspondence

#### Multi-Tenant User Management
```sql
-- Core user system
users: id, company_id, username, email, password_hash, role, created_at
companies: id, name, subscription_type, max_users, created_at

-- User preferences and tracking
user_preferences: user_id, hot_bills_enabled, notification_settings
user_bill_tracking: user_id, measure_id, priority_level, notes
user_alerts: user_id, alert_type, conditions, is_active

-- Company-level features
company_bill_priorities: company_id, measure_id, priority_score
activity_logs: user_id, action_type, resource_type, metadata
```

### Database Migration System

**Alembic Integration** - Professional database version control:
```bash
# Initialize database (first time)
cd backend/database
alembic init migrations

# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Check current version
alembic current

# Migration history
alembic history
```

### Key Database Features

- **Row-Level Security** - Companies can only access their own data
- **JSONB Storage** - Flexible storage for preferences and metadata
- **Full-Text Search** - Efficient bill content searching
- **UUID Primary Keys** - Globally unique identifiers throughout
- **Audit Trails** - Complete activity logging with timestamps
- **Hot Bills Algorithm** - Advanced scoring based on testimony volume and recency
- **Position Code Mapping** - OLIS position codes (3981, 3982, 3983) to human-readable formats

### Environment Configuration

Database connection managed via environment variables:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/olis_tracker
```

## 🔧 Recent Updates & Status (September 2025)

### ✅ Recently Fixed Issues
- **Hot Bills Details Toggle** - Fixed view details button functionality using event delegation instead of inline onclick
- **Navigation System** - Fixed Session Overview submenu disappearing after visiting System Health/Design Library pages
- **Modal System Revert** - Reverted from modal approach back to inline expandable details per user preference
- **Bill Titles Display** - Added bill titles within each hot bill block with responsive text overflow
- **Quick Navigation Cleanup** - Removed redundant Quick Navigation section from main dashboard

### 🎯 Current System Status
- **Server**: Running on port 8001
- **Hot Bills API**: Functional with position breakdowns (3981=neutral, 3982=in_favor, 3983=against)
- **Session Data**: 3 available sessions (2023R1, 2024R1, 2025R1)
- **Navigation**: Single-page app with proper sidebar state management
- **Testing**: Comprehensive smoke tests and critical feature validation
- **Design System**: OLIS-specific styling with shared component system

### 🔍 Testing & Validation
```bash
# Quick system verification
python tests/smoke_test.py

# Comprehensive feature testing  
pytest tests/test_critical_features.py -v

# Pre-modification safety check
./pre-modification-check.sh
```

## 🎨 Design System

### Colors & Status Indicators
- **Running/Success**: Green (`--success`)
- **Stopped/Error**: Red (`--danger`)  
- **Pending/Warning**: Yellow (`--warning`)
- **Info**: Blue (`--info`)
- **Primary**: Brand blue (`--primary`)

### Component Usage
Always import stylesheets in this exact order:
```html
<link rel="stylesheet" href="/shared/design-system.css">
<link rel="stylesheet" href="/shared/components.css">
<link rel="stylesheet" href="/static/style.css">
```

### Available Components
- **Cards** with headers and bodies
- **Buttons** (primary, secondary, success, danger, ghost)
- **Badges** for status indicators
- **Forms** with inputs, textareas, selects
- **Tables** with hover states
- **Alerts** for notifications
- **Loading states** with spinners and skeletons
- **Navigation** bars
- **Grid layouts** (2 and 3 column)

View the complete component library at `/examples` when running.

## 💾 Storage System

The template includes a robust SQLite-based storage system:

```python
from storage import Storage

storage = Storage()

# Log events for activity tracking
storage.log_event("task_created", {"task_id": 1, "title": "New Task"})

# Store application state
storage.set_state("app_config", {"theme": "dark"})

# Retrieve state with defaults
config = storage.get_state("app_config", {"theme": "light"})

# Get recent events
events = storage.get_events(limit=10)

# Database statistics
stats = storage.get_stats()
```

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Available variables:
- `APP_NAME` - Application display name
- `APP_PORT` - Server port (default: 8000)
- `DATABASE_PATH` - SQLite database location
- `ENABLE_DEBUG` - Debug mode toggle
- `AUTO_REFRESH_INTERVAL` - Frontend refresh rate

## 🔧 Development Guide

### Adding New Features

1. **Backend**: Add endpoints to `backend/api.py`
   ```python
   @app.get("/api/my-feature")
   async def my_feature():
       return {"data": "example"}
   ```

2. **Frontend**: Add JavaScript to `frontend/app.js`
   ```javascript
   async function loadMyFeature() {
       const response = await fetch(`${API_BASE_URL}/my-feature`);
       const data = await response.json();
       // Update UI
   }
   ```

3. **Styling**: Add page-specific styles to `frontend/style.css` only

### Best Practices
- **Use design system variables** for colors and spacing
- **Follow existing patterns** for API endpoints
- **Log important events** using the Storage class
- **Handle errors gracefully** with try/catch blocks
- **Update metrics** to reflect application state

## 📱 Responsive Design

The template automatically adapts to different screen sizes:
- **Desktop**: Full 3-column grid layout
- **Tablet**: Responsive grid that stacks when needed
- **Mobile**: Single column with optimized spacing

## 🚀 Quick Customization for New Apps

### Step 1: Update App Branding
- Change title in `frontend/index.html`
- Update API title and description in `backend/api.py`
- Modify `APP_NAME` in `start.sh`

### Step 2: Replace the Example Task Management System
**Look for comments marked with `# EXAMPLE:` in the code**

1. **Backend (`backend/api.py`)**:
   - Replace the `TaskCreate` and `Task` models with your data models
   - Replace task-related endpoints (`/api/tasks/*`) with your API endpoints
   - Keep the patterns: use Storage class, proper error handling, event logging

2. **Frontend (`frontend/app.js`)**:
   - Replace task management functions with your application logic
   - Keep the patterns: async/await, error handling, UI updates
   - Update the dashboard to match your application's purpose

3. **Templates (`frontend/index.html`)**:
   - Replace task creation form and task list with your UI
   - Keep using the design system components and classes

### Step 3: Keep the Foundation
- **Don't modify** `shared/` files (design system)
- **Keep using** the Storage class for persistence
- **Follow existing patterns** for consistency

## ❌ What NOT to Do

- ❌ Modify files in `shared/` directory
- ❌ Add inline styles or custom colors
- ❌ Change the basic project structure
- ❌ Use different component patterns
- ❌ Add complex build processes

## 🛠️ Troubleshooting

### Port 8000 Already in Use
```bash
lsof -i :8000          # Find what's using the port
kill -9 <PID>          # Kill the process
```

### Python/Virtual Environment Issues
```bash
rm -rf venv            # Remove virtual environment
./start.sh             # Recreate and restart
```

### Frontend Not Loading
- Check browser console for JavaScript errors
- Verify API endpoints respond: `curl http://localhost:8000/health`
- Ensure all CSS files are loading properly

### Database Issues
- Database is created automatically in `data/app.db`
- Delete `data/` folder to reset all data
- Check storage operations with `python3 backend/storage.py`

## 🎯 Use Cases

This template is perfect for building:
- **Development tools** and utilities
- **Monitoring dashboards** for local services
- **Data processing interfaces** 
- **Automation control panels**
- **Local service management tools**

## 📈 Performance

- **Fast startup**: < 5 seconds from cold start
- **Low memory**: ~50MB RAM usage
- **Efficient database**: SQLite with proper indexing
- **Minimal dependencies**: Only essential packages

---

**🤖 Built for AI Agent Company** - Consistent, reliable, beautiful applications that just work.