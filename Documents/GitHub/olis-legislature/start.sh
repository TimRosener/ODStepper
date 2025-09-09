#!/bin/bash

# Make sure script is executable
if [ ! -x "$0" ]; then
    chmod +x "$0"
    echo "Made script executable. Running..."
fi

# Color codes for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Read configuration from .env file
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

APP_NAME=${APP_NAME:-"OLIS - Oregon Legislative Information System"}
PORT=${APP_PORT:-8001}

echo -e "${GREEN}🚀 Starting $APP_NAME...${NC}"
echo ""

# 1. Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Install Python 3 and try again"
    exit 1
fi

echo -e "${GREEN}✅ Checking dependencies...${NC}"
echo "   Python $(python3 --version | cut -d' ' -f2) ✓"

# 2. Setup virtual environment if needed
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 First time setup - creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r backend/requirements.txt
    echo "   Dependencies installed ✓"
else
    source venv/bin/activate
    echo "   Virtual environment ✓"
fi

# 3. Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port $PORT is already in use${NC}"
    echo "Another service is running. Stop it first or change ports."
    exit 1
fi

echo ""
echo -e "${BLUE}🔧 Starting backend API...${NC}"

# 4. Start the backend
cd backend
uvicorn api:app --reload --port $PORT --log-level warning &
BACKEND_PID=$!
cd ..

# 5. Wait for backend to be ready
echo "   Waiting for API to start..."
for i in {1..10}; do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Check if backend started successfully
if ! curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Failed to start backend${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "   INFO: Uvicorn running on http://127.0.0.1:$PORT"
echo ""

# 6. Open the dashboard
echo -e "${BLUE}🌐 Opening dashboard in browser...${NC}"
open "http://localhost:$PORT"
echo "   Dashboard: http://localhost:$PORT"

echo ""
echo -e "${GREEN}✨ $APP_NAME is running!${NC}"
echo "   "
echo "   Dashboard opened in your default browser"
echo "   API running at: http://localhost:$PORT/api"
echo "   "
echo -e "${NC}Press Ctrl+C to stop everything${NC}"
echo ""

# 7. Cleanup function for graceful shutdown
cleanup() {
    echo ""
    echo -e "${RED}🛑 Shutting down $APP_NAME...${NC}"
    echo "   Stopping API server... ✓"
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    echo "   Cleaning up... ✓"
    echo "   "
    echo -e "${NC}👋 $APP_NAME stopped. Run ./start.sh to start again.${NC}"
    exit 0
}

# Register the cleanup function to run on Ctrl+C
trap cleanup INT TERM

# 8. Keep running
wait $BACKEND_PID
