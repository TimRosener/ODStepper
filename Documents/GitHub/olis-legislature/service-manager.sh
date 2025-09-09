#!/bin/bash

# Service Manager for Resilient Local Services
# Provides auto-recovery, health monitoring, and simple controls

SERVICE_NAME="${PWD##*/}"  # Use current directory name as service name
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="${SERVICE_DIR}/.service.pid"
SUPERVISOR_PIDFILE="${SERVICE_DIR}/.supervisor.pid"
PORT=8000
MAX_RESTARTS=10
RESTART_DELAY=5

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# Ensure logs directory exists
mkdir -p logs

# Function to check if service is running
is_running() {
    if [ -f "${PIDFILE}" ]; then
        PID=$(cat "${PIDFILE}")
        if kill -0 $PID 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to check if supervisor is running
is_supervisor_running() {
    if [ -f "${SUPERVISOR_PIDFILE}" ]; then
        SPID=$(cat "${SUPERVISOR_PIDFILE}")
        if kill -0 $SPID 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Check if port is available
check_port() {
    if command -v lsof > /dev/null; then
        if lsof -i :$PORT > /dev/null 2>&1; then
            echo -e "${RED}❌ Port $PORT is already in use${NC}"
            echo -e "   Use: ${YELLOW}lsof -i :$PORT${NC} to see what's using it"
            return 1
        fi
    fi
    return 0
}

# Start the actual service
start_service() {
    # Check port availability first
    if ! check_port; then
        return 1
    fi
    
    # Setup Python environment if needed
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}📦 First time setup - creating virtual environment...${NC}"
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to create virtual environment${NC}"
            return 1
        fi
        source venv/bin/activate
        pip install -q -r backend/requirements.txt
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to install requirements${NC}"
            return 1
        fi
    else
        source venv/bin/activate
    fi
    
    # Start the FastAPI service
    cd backend
    nohup uvicorn api:app --reload --port $PORT --log-level warning > ../logs/service.log 2>&1 &
    local SERVICE_PID=$!
    echo $SERVICE_PID > "${PIDFILE}"
    cd ..
    
    # Wait a moment to verify it started
    sleep 3
    if kill -0 $SERVICE_PID 2>/dev/null; then
        # Also verify it's actually responding
        for i in {1..5}; do
            if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
                return 0
            fi
            sleep 1
        done
        # Process running but not responding - kill it
        kill $SERVICE_PID 2>/dev/null
        rm -f "${PIDFILE}"
        return 1
    else
        rm -f "${PIDFILE}"
        return 1
    fi
}

# Supervisor function that monitors and restarts service
run_supervisor() {
    local restart_count=0
    local last_restart=$(date +%s)
    
    echo "[$(date)] Supervisor started for $SERVICE_NAME" >> logs/supervisor.log
    
    while true; do
        if [ -f "${SERVICE_DIR}/.stop-requested" ]; then
            echo "[$(date)] Stop requested, supervisor exiting" >> logs/supervisor.log
            if is_running; then
                kill $(cat "${PIDFILE}") 2>/dev/null
                rm -f "${PIDFILE}"
            fi
            rm -f "${SERVICE_DIR}/.stop-requested"
            rm -f "${SUPERVISOR_PIDFILE}"
            exit 0
        fi
        
        if ! is_running; then
            current_time=$(date +%s)
            time_since_last=$((current_time - last_restart))
            
            # Reset counter if it's been more than an hour since last restart
            if [ $time_since_last -gt 3600 ]; then
                restart_count=0
            fi
            
            if [ $restart_count -lt $MAX_RESTARTS ]; then
                restart_count=$((restart_count + 1))
                echo "[$(date)] Service down, attempting restart #$restart_count" >> logs/supervisor.log
                
                if start_service; then
                    echo "[$(date)] Service restarted successfully" >> logs/supervisor.log
                    last_restart=$(date +%s)
                    
                    # Log restart to database via API call (once service is up)
                    sleep 3
                    curl -s -X POST "http://localhost:$PORT/api/internal/log-restart" \
                         -H "Content-Type: application/json" \
                         -d "{\"count\": $restart_count}" > /dev/null 2>&1
                else
                    echo "[$(date)] Failed to restart service" >> logs/supervisor.log
                    sleep $((RESTART_DELAY * restart_count))  # Exponential backoff
                fi
            else
                echo "[$(date)] Max restarts ($MAX_RESTARTS) reached. Supervisor stopping." >> logs/supervisor.log
                rm -f "${SUPERVISOR_PIDFILE}"
                exit 1
            fi
        else
            # Service is running - do a quick health check
            if ! curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
                echo "[$(date)] Service process alive but not responding to health checks" >> logs/supervisor.log
                # Kill unresponsive process to trigger restart
                kill $(cat "${PIDFILE}") 2>/dev/null
                rm -f "${PIDFILE}"
            fi
        fi
        
        sleep $RESTART_DELAY
    done
}

# Start command
start() {
    if is_supervisor_running; then
        echo -e "${YELLOW}⚠️  Service supervisor already running${NC}"
        status
        return 0
    fi
    
    echo -e "${GREEN}🚀 Starting $SERVICE_NAME...${NC}"
    
    # Start the supervisor in background
    run_supervisor &
    SUPERVISOR_PID=$!
    echo $SUPERVISOR_PID > "${SUPERVISOR_PIDFILE}"
    
    # Wait for service to be ready
    echo -e "${BLUE}⏳ Waiting for service to be ready...${NC}"
    for i in {1..15}; do
        if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $SERVICE_NAME is running!${NC}"
            echo -e "   Dashboard: ${BLUE}http://localhost:$PORT${NC}"
            echo -e "   Logs: ${BLUE}logs/service.log${NC}"
            echo ""
            echo -e "Use ${GREEN}./service-manager.sh status${NC} to check health"
            echo -e "Use ${GREEN}./service-manager.sh stop${NC} to stop service"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}❌ Service failed to start. Check logs/service.log${NC}"
    echo -e "   Common issues:"
    echo -e "   • Port $PORT already in use: ${YELLOW}lsof -i :$PORT${NC}"
    echo -e "   • Python issues: Check logs/service.log"
    echo -e "   • Missing dependencies: Try deleting venv/ and restart"
    return 1
}

# Stop command
stop() {
    if ! is_supervisor_running; then
        echo -e "${YELLOW}⚠️  Service not running${NC}"
        return 0
    fi
    
    echo -e "${RED}🛑 Stopping $SERVICE_NAME...${NC}"
    
    # Signal supervisor to stop
    touch "${SERVICE_DIR}/.stop-requested"
    
    # Wait for graceful shutdown
    local count=0
    while [ $count -lt 10 ]; do
        if ! is_supervisor_running; then
            echo -e "${GREEN}✅ Service stopped${NC}"
            rm -f "${PIDFILE}" "${SUPERVISOR_PIDFILE}" "${SERVICE_DIR}/.stop-requested"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if needed
    echo -e "${YELLOW}⚠️  Force stopping...${NC}"
    [ -f "${SUPERVISOR_PIDFILE}" ] && kill -9 $(cat "${SUPERVISOR_PIDFILE}") 2>/dev/null
    [ -f "${PIDFILE}" ] && kill -9 $(cat "${PIDFILE}") 2>/dev/null
    rm -f "${PIDFILE}" "${SUPERVISOR_PIDFILE}" "${SERVICE_DIR}/.stop-requested"
    
    echo -e "${GREEN}✅ Service stopped${NC}"
}

# Status command
status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE} $SERVICE_NAME Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if is_supervisor_running; then
        echo -e "Supervisor: ${GREEN}● Running${NC} (PID: $(cat ${SUPERVISOR_PIDFILE}))"
    else
        echo -e "Supervisor: ${RED}● Stopped${NC}"
    fi
    
    if is_running; then
        echo -e "Service:    ${GREEN}● Running${NC} (PID: $(cat ${PIDFILE}))"
        
        # Check actual health endpoint
        if HEALTH=$(curl -s http://localhost:$PORT/api/health/detailed 2>/dev/null); then
            echo -e "Health:     ${GREEN}● Healthy${NC}"
            
            # Parse and display health metrics if available
            if command -v python3 > /dev/null; then
                echo "$HEALTH" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        data = data['data']
    uptime_min = int(data.get('uptime_seconds', 0)) // 60
    uptime_hours = uptime_min // 60
    uptime_display = f'{uptime_hours}h {uptime_min % 60}m' if uptime_hours > 0 else f'{uptime_min}m'
    print(f'Uptime:     {uptime_display}')
    print(f'Memory:     {data.get(\"memory_mb\", 0):.1f} MB')
    print(f'Restarts:   {data.get(\"restart_count\", 0)} total')
    if data.get('last_restart'):
        print(f'Last Start: {data.get(\"last_restart\", \"Unknown\")[:19]}')
    print(f'Errors/hr:  {data.get(\"errors_last_hour\", 0)}')
except Exception as e: 
    pass
" 2>/dev/null
            fi
        else
            echo -e "Health:     ${YELLOW}● Not responding${NC}"
        fi
        
        echo -e "\nEndpoints:"
        echo -e "  Dashboard:  ${BLUE}http://localhost:$PORT${NC}"
        echo -e "  API Health: ${BLUE}http://localhost:$PORT/health${NC}"
        echo -e "  API Status: ${BLUE}http://localhost:$PORT/api/status${NC}"
    else
        echo -e "Service:    ${RED}● Stopped${NC}"
    fi
    
    # Show recent log entries
    if [ -f "logs/supervisor.log" ]; then
        echo -e "\n${BLUE}Recent Events:${NC}"
        tail -n 3 logs/supervisor.log | while IFS= read -r line; do
            echo "  $line"
        done
    fi
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Restart command
restart() {
    echo -e "${YELLOW}🔄 Restarting $SERVICE_NAME...${NC}"
    stop
    sleep 2
    start
}

# Logs command
logs() {
    if [ "$1" == "-f" ] || [ "$1" == "--follow" ]; then
        echo -e "${BLUE}Following logs (Ctrl+C to stop)...${NC}"
        tail -f logs/service.log
    else
        echo -e "${BLUE}━━━ Recent Service Logs ━━━${NC}"
        tail -n 20 logs/service.log 2>/dev/null || echo "No logs yet"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "Use ${GREEN}./service-manager.sh logs -f${NC} to follow logs"
    fi
}

# Health command
health() {
    if curl -s http://localhost:$PORT/api/health/detailed > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Service is not healthy${NC}"
        return 1
    fi
}

# Clean command - cleanup orphaned processes and files
clean() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Kill any orphaned processes
    if [ -f "${PIDFILE}" ]; then
        PID=$(cat "${PIDFILE}")
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            echo "Killed service process $PID"
        fi
    fi
    
    if [ -f "${SUPERVISOR_PIDFILE}" ]; then
        SPID=$(cat "${SUPERVISOR_PIDFILE}")
        if kill -0 $SPID 2>/dev/null; then
            kill $SPID
            echo "Killed supervisor process $SPID"
        fi
    fi
    
    # Remove pid files
    rm -f "${PIDFILE}" "${SUPERVISOR_PIDFILE}" "${SERVICE_DIR}/.stop-requested"
    
    # Rotate old logs if they're too big
    if [ -f "logs/service.log" ] && [ $(wc -c < "logs/service.log") -gt 10485760 ]; then  # 10MB
        mv logs/service.log logs/service.log.old
        echo "Rotated large service log"
    fi
    
    if [ -f "logs/supervisor.log" ] && [ $(wc -c < "logs/supervisor.log") -gt 1048576 ]; then  # 1MB
        mv logs/supervisor.log logs/supervisor.log.old
        echo "Rotated large supervisor log"
    fi
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Main command handler
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    health)
        health
        ;;
    clean)
        clean
        ;;
    *)
        echo -e "${BLUE}🤖 AI Agent Service Manager${NC}"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|health|clean}"
        echo ""
        echo "Commands:"
        echo "  start    - Start service with auto-recovery"
        echo "  stop     - Stop service and supervisor"
        echo "  restart  - Restart service"
        echo "  status   - Show detailed service status"
        echo "  logs     - Show recent logs (-f to follow)"
        echo "  health   - Quick health check"
        echo "  clean    - Clean up orphaned processes and logs"
        echo ""
        echo "The service will automatically restart if it crashes."
        echo "Logs are saved to: logs/"
        echo ""
        echo -e "Quick start: ${GREEN}./service-manager.sh start${NC}"
        exit 1
        ;;
esac