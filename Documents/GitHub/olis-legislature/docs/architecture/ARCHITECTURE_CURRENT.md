# Current Architecture - Implementation Patterns for This Iteration

This document defines HOW to implement features within the current iteration of the AI Agent Company starter template.

## Current Stack

### Required Technology Choices
- **Backend**: FastAPI (Python 3.8+)
- **Frontend**: Vanilla HTML/JS/CSS (no framework)
- **Database**: PostgreSQL with SQLAlchemy ORM (OLIS production system)
- **Database Legacy**: SQLite via storage.py (simple apps)
- **Database Migrations**: Alembic for version control
- **Deployment**: ./start.sh script
- **Design**: CSS variables + component patterns

### File Structure (Enforced)
```
project-name/
├── backend/
│   ├── api.py          # FastAPI app (serves API + frontend)
│   ├── storage.py      # Simple SQLite operations (legacy)
│   ├── database/       # NEW: PostgreSQL system (production)
│   │   ├── models.py   # SQLAlchemy ORM models
│   │   ├── schema.sql  # PostgreSQL schema definition
│   │   ├── alembic.ini # Migration configuration
│   │   └── migrations/ # Database version control
│   └── requirements.txt
├── frontend/
│   ├── index.html      # Dashboard (imports shared CSS)
│   ├── app.js          # Client-side logic
│   └── style.css       # Page-specific styles ONLY
├── shared/             # DO NOT MODIFY
│   ├── design-system.css
│   └── components.css
├── .claude/
│   └── agents/         # Agent definitions
├── docs/               # Process documentation
│   ├── LESSONS.md
│   ├── architecture/
│   └── scope/
├── start.sh            # One-command startup
└── CLAUDE.md           # Combined instructions
```

## Implementation Patterns

### HTML Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>App Name</title>
    <link rel="stylesheet" href="/shared/design-system.css">
    <link rel="stylesheet" href="/shared/components.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
```

### Component Usage
```html
<!-- Status Indicators -->
<div class="status-indicator">
    <span class="status-dot running"></span>
    <span class="badge badge-success">Running</span>
</div>

<!-- Cards -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Feature Name</h3>
    </div>
    <div class="card-body">
        Content goes here
    </div>
</div>

<!-- Buttons -->
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary</button>
```

### FastAPI Patterns
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from storage import Storage

app = FastAPI()
storage = Storage()

# Serve frontend files
app.mount("/shared", StaticFiles(directory="../shared"), name="shared")
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Health check (required)
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Dashboard (required)
@app.get("/")
async def dashboard():
    return FileResponse("../frontend/index.html")

# API endpoints
@app.get("/api/status")
async def get_status():
    return {"running": True, "data": storage.get_data()}
```

### Storage Patterns

#### Legacy SQLite (Simple Apps)
```python
from storage import Storage

storage = Storage()
storage.log_event("action", {"key": "value"})
storage.set_state("setting", "value")
data = storage.get_state("setting")
```

#### NEW: PostgreSQL with SQLAlchemy (Production)
```python
from database.models import User, Company, Measure
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def get_user_bills(session: AsyncSession, user_id: str):
    """Get user's tracked bills with company access control"""
    result = await session.execute(
        select(Measure)
        .join(UserBillTracking)
        .where(UserBillTracking.user_id == user_id)
    )
    return result.scalars().all()

async def create_user(session: AsyncSession, user_data: dict):
    """Create new user with proper validation"""
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

#### Database Migration Patterns
```python
# Always use Alembic for schema changes
# backend/database/migrations/env.py handles auto-discovery

# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply to database
alembic upgrade head

# Check current version
alembic current
```

### Status Color Mapping
- **Running/Success**: `--success` color, `badge-success` class
- **Stopped/Error**: `--danger` color, `badge-danger` class  
- **Starting/Warning**: `--warning` color, `badge-warning` class
- **Unknown/Info**: `--info` color, `badge-info` class

## Current Constraints

### What You MUST Do
- Import CSS in exact order shown above
- Use existing component patterns from components.css
- Serve frontend through FastAPI (no separate servers)
- Include health check endpoint
- Make ./start.sh work with your changes
- **NEW: Database Requirements**
  - Use Alembic for all schema changes
  - Follow SQLAlchemy async patterns
  - Implement proper row-level security for multi-tenant systems
  - Use UUID primary keys for all new tables
  - Include proper foreign key constraints and indexes

### What You CANNOT Do
- Modify /shared/design-system.css or /shared/components.css
- Use inline styles or create new CSS variables
- Create separate backend/frontend servers
- Use external CSS frameworks
- Break existing component patterns
- **NEW: Database Restrictions**
  - Never modify the database schema manually (always use Alembic)
  - Don't expose raw SQL queries to frontend (use ORM)
  - Never store sensitive data without proper hashing
  - Don't bypass company-level access controls

## Error Handling Patterns
```javascript
// Frontend
async function callAPI(endpoint) {
    try {
        const response = await fetch(`/api/${endpoint}`);
        const data = await response.json();
        if (data.error) {
            showAlert(data.error, 'danger');
            return null;
        }
        return data;
    } catch (error) {
        showAlert('Connection error', 'danger');
        return null;
    }
}
```

```python
# Backend
@app.post("/api/action")
async def perform_action():
    try:
        result = do_something()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

*These patterns must be followed exactly. Architecture Guardian enforces compliance.*