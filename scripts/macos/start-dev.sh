#!/bin/bash

# ============================================
# Lily Cafe POS - Development Start Script
# Starts both servers in development mode
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
echo "  LILY CAFE POS - DEVELOPMENT MODE"
echo "======================================"
echo ""
echo "Performing pre-flight checks..."
echo ""

# ====================
# Pre-flight Checks
# ====================

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[X] Python 3 not found${NC}"
    echo "Please install Python 3.11 or higher"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Python 3 found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}[X] Node.js not found${NC}"
    echo "Please install Node.js 18 or higher"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Node.js found"

# Check UV
if ! command -v uv &> /dev/null; then
    echo -e "${RED}[X] UV not found${NC}"
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "${GREEN}UV installed${NC}"
    echo "Please restart your terminal and run this script again"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} UV found"

# Check backend virtual environment
if [ ! -d "backend/.venv" ]; then
    echo -e "${YELLOW}[!]${NC} Backend environment not found"
    echo "Creating virtual environment..."
    cd backend
    uv sync --extra printer
    cd ..
    echo -e "${GREEN}[OK]${NC} Backend environment created"
else
    echo -e "${GREEN}[OK]${NC} Backend environment found"
fi

# Check frontend node_modules
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}[!]${NC} Frontend dependencies not installed"
    echo "Installing npm packages..."
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}[OK]${NC} Frontend dependencies installed"
else
    echo -e "${GREEN}[OK]${NC} Frontend dependencies found"
fi

# Check database
if [ ! -f "backend/restaurant.db" ]; then
    echo -e "${YELLOW}[!]${NC} Database not found"
    echo "The database will be created on first run"
fi

echo ""
echo "======================================"
echo "All checks passed!"
echo "======================================"
echo ""
echo "Starting Development Servers..."
echo "(Hot-reload enabled)"
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
echo -e "${BLUE}[1/2] Starting Backend Server (Development)...${NC}"
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 2

# Start frontend in background
echo -e "${BLUE}[2/2] Starting Frontend Server (Development)...${NC}"
cd frontend
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo "======================================"
echo "BOTH SERVERS STARTED (DEV MODE)!"
echo "======================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Development Features:"
echo "  - Hot-reload enabled"
echo "  - Source maps enabled"
echo "  - Detailed error messages"
echo ""
echo -e "${RED}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
