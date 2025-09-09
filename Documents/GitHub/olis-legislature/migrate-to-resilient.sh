#!/bin/bash

# Migration script to update existing projects to resilient services

echo "🔄 Migrating to resilient service..."

# Backup old start.sh
if [ -f "start.sh" ]; then
    mv start.sh start.sh.backup
    echo "✅ Backed up old start.sh to start.sh.backup"
fi

# Create symlink for compatibility
ln -sf service-manager.sh start.sh
echo "✅ Created compatibility link from start.sh to service-manager.sh"

# Create logs directory
mkdir -p logs
echo "✅ Created logs directory"

# Make executable
chmod +x service-manager.sh
chmod +x start.sh

# Check if we have the service-manager.sh file
if [ ! -f "service-manager.sh" ]; then
    echo "❌ service-manager.sh not found. Please copy it from the starter template."
    exit 1
fi

# Update .gitignore if it exists
if [ -f ".gitignore" ]; then
    if ! grep -q ".service.pid" .gitignore; then
        echo "" >> .gitignore
        echo "# Service management files" >> .gitignore
        echo ".service.pid" >> .gitignore
        echo ".supervisor.pid" >> .gitignore
        echo ".stop-requested" >> .gitignore
        echo "logs/" >> .gitignore
        echo "" >> .gitignore
        echo "# Keep old backup" >> .gitignore
        echo "start.sh.backup" >> .gitignore
        echo "✅ Updated .gitignore with service management files"
    else
        echo "ℹ️  .gitignore already contains service management entries"
    fi
fi

# Check if backend has the required health endpoints
if [ -f "backend/api.py" ]; then
    if ! grep -q "/api/health/detailed" backend/api.py; then
        echo "⚠️  Warning: backend/api.py missing detailed health endpoints"
        echo "   Please add the health endpoints from the updated template"
        echo "   Required endpoints:"
        echo "   - /api/health/detailed"
        echo "   - /api/internal/log-restart"
        echo "   - startup/shutdown event handlers"
    else
        echo "✅ Backend has required health endpoints"
    fi
else
    echo "⚠️  Warning: backend/api.py not found"
fi

echo ""
echo "✨ Migration complete!"
echo ""
echo "You can now use either:"
echo "  ./start.sh                    (compatibility)"
echo "  ./service-manager.sh start    (recommended)"
echo ""
echo "New commands available:"
echo "  ./service-manager.sh status   - Check health"
echo "  ./service-manager.sh restart  - Restart service"
echo "  ./service-manager.sh logs     - View logs"
echo "  ./service-manager.sh logs -f  - Follow logs"
echo "  ./service-manager.sh stop     - Stop service"
echo "  ./service-manager.sh clean    - Cleanup orphaned processes"
echo ""
echo "🚀 Your service now has:"
echo "   • Auto-recovery from crashes"
echo "   • Background operation (survives terminal close)"
echo "   • Health monitoring with detailed metrics"
echo "   • Proper logging to logs/ directory"
echo "   • Simple management commands"
echo ""
echo "Test it out: ./service-manager.sh start"