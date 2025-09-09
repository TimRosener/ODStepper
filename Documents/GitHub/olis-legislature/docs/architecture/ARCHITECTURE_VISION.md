# Architecture Vision - The "Car" We're Building Toward

This document describes the long-term technical vision for applications built with the AI Agent Company starter template.

## Core Principles

### Design System First
- Consistent visual language across all applications
- CSS variables provide theming and customization
- Component patterns ensure predictable UX
- No application breaks the shared design system

### Progressive Enhancement
- Start with working dashboard (skateboard)
- Add features incrementally (scooter → bicycle → car)
- Each iteration remains deployable via ./start.sh
- Never break existing functionality

### Local-First Architecture
- Applications run locally on Mac
- Single FastAPI server serves everything
- SQLite for simple data persistence  
- Docker optional but not required
- Human-friendly ./start.sh startup

## Technical Vision

### Frontend Evolution
- **Skateboard**: Static dashboard with real-time updates
- **Scooter**: Interactive controls and basic forms
- **Bicycle**: Rich components and data visualization
- **Car**: Advanced UX with complex interactions

### Backend Evolution  
- **Skateboard**: Basic API endpoints and health checks
- **Scooter**: CRUD operations and data storage
- **Bicycle**: Advanced querying and business logic
- **Car**: Integration with external services

### Data Evolution
- **Skateboard**: In-memory or simple SQLite
- **Scooter**: Structured SQLite with migrations  
- **Bicycle**: PostgreSQL with SQLAlchemy ORM and basic relationships
- **Car**: Multi-tenant PostgreSQL with advanced features:
  - Row-level security and access control
  - Full-text search and advanced indexing
  - Database migrations with Alembic
  - Audit trails and activity logging
  - Real-time data synchronization
  - Analytics and reporting capabilities

## Constraints That Never Change

1. **Design System**: /shared/ files remain untouched
2. **Single Server**: FastAPI serves both API and frontend
3. **Local Deployment**: ./start.sh must work at every stage  
4. **Component Patterns**: Use established card/button/badge patterns
5. **Status Colors**: Semantic color usage (success/danger/warning/info)
6. **NEW: Database Architecture Principles**:
   - Schema changes always managed through Alembic migrations
   - Multi-tenant systems use row-level security
   - UUID primary keys for all production tables
   - Async SQLAlchemy patterns for all database operations
   - Never expose raw database credentials or queries to frontend

## Integration Patterns

### With Claude Code Agents
- Architecture Guardian enforces these patterns
- Product Scope ensures incremental delivery
- Builder implements within constraints
- Process Observer captures violations for learning

### With Local Development
- Each application maintains its own git repo
- Template patterns provide consistency
- Human testing validates each iteration
- Feedback drives next iteration planning

## Success Metrics

- Applications look consistent across the suite
- ./start.sh always works for any application
- Features can be added without architectural rewrites
- Human can understand and modify any application
- **NEW: Database System Metrics**:
  - Database migrations run cleanly on any environment
  - Multi-tenant access controls prevent data leakage
  - Schema changes don't break existing functionality
  - Database performance scales with data growth
  - Backup and recovery procedures are reliable

---

*This vision guides all architectural decisions while allowing feature flexibility.*