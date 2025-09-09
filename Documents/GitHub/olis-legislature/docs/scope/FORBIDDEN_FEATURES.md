# Forbidden Features - What NOT to Build Yet

These features are explicitly forbidden in the current release slice. They may be added in future iterations.

## Design System Modifications
- ❌ Custom CSS variables beyond what's in design-system.css  
- ❌ New component patterns not in components.css
- ❌ Inline styles anywhere in the application
- ❌ External CSS frameworks (Bootstrap, Tailwind, etc)
- ❌ Custom fonts beyond system defaults

## Architecture Changes  
- ❌ Separate backend and frontend servers
- ❌ Database systems other than SQLite
- ❌ Authentication systems (login, sessions, etc)
- ❌ External API integrations
- ❌ Real-time features (websockets, server-sent events)

## Complex Features
- ❌ User management and permissions
- ❌ File upload/download functionality
- ❌ Advanced data visualization (charts, graphs)
- ❌ Export to multiple formats
- ❌ Search and filtering systems

## Development Complexity
- ❌ Build processes or bundling tools
- ❌ Testing frameworks and test suites
- ❌ CI/CD pipelines
- ❌ Docker containerization
- ❌ Environment configuration beyond .env.example

## UI/UX Enhancements
- ❌ Dark mode toggle
- ❌ Responsive mobile layouts
- ❌ Animation and transition effects
- ❌ Advanced form validation
- ❌ Drag and drop interfaces

## Current Focus: Template Integration Only

The current story focuses solely on demonstrating that:
1. Agents work correctly with the template
2. Documentation structure is in place
3. Basic dashboard follows design patterns
4. ./start.sh launches everything successfully

## Future Release Slices

### Slice 2: Basic Application Features
- Simple data display
- Basic form interactions
- Status monitoring

### Slice 3: Enhanced Functionality  
- Data persistence
- Basic CRUD operations
- Improved UX

### Slice 4: Full Application
- Advanced features from forbidden list
- Performance optimizations
- Production readiness

---

*Product Scope enforces this list. Builder cannot implement these features even if they seem "quick to add".*