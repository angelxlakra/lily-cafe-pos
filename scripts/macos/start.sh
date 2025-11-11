#!/bin/bash

# ============================================
# Lily Cafe POS - Production Start Script
# Starts both servers with production builds
# ============================================

set -e  # Exit on error

# Get project root (2 levels up from scripts/macos/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "======================================"
echo "  LILY CAFE POS SYSTEM LAUNCHER"
echo "======================================"
echo ""
echo "Performing pre-flight checks..."
echo ""

# ====================
# Pre-flight Checks
# ====================

# Check 1: Frontend build exists
if [ ! -f "frontend/dist/index.html" ]; then
    echo -e "${RED}[X] Frontend not built!${NC}"
    echo ""
    echo "The frontend needs to be built before starting."
    echo "Run: ./scripts/macos/update.sh"
    echo ""
    echo "Or build manually:"
    echo "  cd frontend"
    echo "  npm run build"
    echo ""
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Frontend build found"

# Check 2: Backend virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo -e "${RED}[X] Backend virtual environment not found!${NC}"
    echo ""
    echo "Please run: ./scripts/macos/update.sh"
    echo ""
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Backend environment found"

# Check 3: Database exists
if [ ! -f "backend/restaurant.db" ]; then
    echo -e "${YELLOW}[!] Warning: Database not found${NC}"
    echo ""
    echo "The database will be created on first run."
    echo ""
    read -p "Press Enter to continue..."
fi

echo ""
echo "======================================"
echo "All checks passed!"
echo "======================================"
echo ""
echo "Starting both Backend and Frontend servers..."
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${BLUE}Stopping servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo -e "${BLUE}[1/2] Starting Backend Server...${NC}"
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 2

# Start frontend preview server in background
echo -e "${BLUE}[2/2] Starting Frontend Preview Server...${NC}"
cd frontend
npm run preview -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo "======================================"
echo "BOTH SERVERS STARTED!"
echo "======================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:4173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Wait a few seconds for servers to start,"
echo "then open: http://localhost:4173"
echo ""
echo -e "${RED}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
