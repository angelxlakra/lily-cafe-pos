#!/bin/bash

# Lily Cafe POS System - Development Startup Script
# This script starts both the backend and frontend servers

set -e  # Exit on error

echo "🍵 Starting Lily Cafe POS System..."
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}⚠️  .env file not found!${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created. Please update it with your configuration.${NC}"
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 18 or higher.${NC}"
    exit 1
fi

# Check UV
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV not found. Installing UV...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "${GREEN}✅ UV installed. Please restart your terminal and run this script again.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📦 Installing Backend Dependencies...${NC}"
cd backend
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    uv sync
else
    echo "Virtual environment exists, syncing dependencies..."
    uv sync
fi

# Check if database exists
if [ ! -f restaurant.db ]; then
    echo ""
    echo -e "${BLUE}🗄️  Initializing Database...${NC}"
    uv run python -m scripts.seed_data
fi

cd ..

echo ""
echo -e "${BLUE}📦 Installing Frontend Dependencies...${NC}"
cd frontend
if [ ! -d node_modules ]; then
    echo "Installing npm packages..."
    npm install
else
    echo "node_modules exists, skipping npm install"
fi
cd ..

echo ""
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo "=================================="
echo -e "${BLUE}🚀 Starting Servers...${NC}"
echo "=================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo -e "${RED}Press Ctrl+C to stop both servers${NC}"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${BLUE}🛑 Stopping servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo -e "${BLUE}Starting Backend Server...${NC}"
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 2

# Start frontend in background
echo -e "${BLUE}Starting Frontend Server...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
