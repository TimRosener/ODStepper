# Current Story - System Health & Demo Page Separation

**Status**: in_progress  
**Assigned to**: Builder  
**Release Slice**: First Working Example

## Story Description

Separate system health monitoring from demo application functionality by creating distinct pages with clear purposes. This makes the template structure clearer and provides better real system monitoring.

## Acceptance Criteria

1. ✅ Agent definitions are in place (.claude/agents/)
2. ✅ Documentation structure is created (docs/ with LESSONS.md)
3. ✅ Home page introduces this as a "starter template for new projects"
4. ⏳ **NEW**: System Health page shows ACTUAL template service metrics
5. ⏳ **NEW**: Demo page focuses purely on showcasing design components in action  
6. ⏳ **NEW**: Navigation includes "System Health" as a menu item
7. ✅ ./start.sh works with new structure
8. ⏳ All CSS imports follow the required pattern

## Implementation Details

### Page Structure (Updated)
- **Home Page** (`/`) - Template introduction and overview (KEEP AS IS)
- **System Health Page** (`/health`) - ACTUAL system metrics and monitoring
- **Template Demo Page** (`/demo`) - Working example showcasing design components
- **Design Library** (`/examples`) - Component reference (KEEP AS IS)

### System Health Page (`/health`)
- **Real System Metrics**: FastAPI status, database health, actual uptime
- **Service Monitoring**: Backend health checks, error rates, response times
- **Database Status**: SQLite connection, schema version, storage stats  
- **Template Metrics**: Agent coordination status, process health
- **NOT demo data**: Remove task-specific metrics, focus on infrastructure

### Template Demo Page (`/demo`) - Refinement
- **Keep**: Existing task management functionality as design showcase
- **Purpose**: Demonstrate design system components in real application context
- **Focus**: Show cards, forms, buttons, status indicators working together
- **Label clearly**: "This is a demo application showcasing the template"

### Navigation Structure (Updated Order)
1. Home (template introduction)
2. **System Health** (NEW - actual system monitoring)
3. Template Demo (existing functionality, clearer purpose)
4. Design Library (component reference)

### System Health Content Requirements
- **Service Status**: FastAPI server health, port, uptime since startup
- **Database Health**: SQLite connection, file size, schema status
- **Performance**: Response times, error rates, memory usage
- **Agent Status**: Which agents are active/configured
- **Real Metrics**: No task counts, focus on infrastructure health

## Files to Create/Modify

### New Files
- Create `frontend/health.html` - System health monitoring page
- Add route in `backend/api.py` for `/health` page serving

### Modified Files  
- Update `frontend/index.html` - Update navigation to include System Health
- Update `frontend/demo.html` - Add clear labeling as demo application
- Update `backend/api.py` - Add `/health` route, enhance `/api/status` for real metrics
- Update `frontend/app.js` - Handle new routing, fetch real system data for health page

## Design Requirements
- Use existing card components for system health display
- Status indicators with proper colors (running=green, error=red)
- Follow button patterns for navigation
- No custom CSS variables or inline styles
- Maintain sidebar navigation structure
- Use stats-grid pattern for health metrics

## API Requirements

### Enhanced System Status Endpoint  
- `/api/status` should return REAL system metrics:
  - Actual service uptime (not "0d 0h 0m")
  - Database health and connection status
  - FastAPI server status and response times
  - Error rates and recent error counts
  - Memory usage and system resources
  - Agent process status

### Separate Demo Data
- Keep task management endpoints for demo functionality
- Clearly separate system health from demo application data

## Definition of Done
- [ ] System Health page accessible at `/health` shows real infrastructure metrics
- [ ] Navigation includes "System Health" as second menu item
- [ ] Demo page clearly labeled as template showcase (not system status)
- [ ] Home page remains template introduction with basic overview
- [ ] All system health indicators show actual service status
- [ ] ./start.sh starts everything successfully
- [ ] No design system violations
- [ ] API endpoints return real system data (not placeholder values)

## Success Criteria
- Developer can monitor actual template service health at `/health`
- Demo page serves as clear example of design system usage
- Navigation structure makes the separation obvious
- System administrators can use `/health` for real monitoring
- Template purpose is immediately clear to new developers

---

*This story separates infrastructure monitoring from application demonstration, making the template more useful for both learning and real deployment monitoring.*