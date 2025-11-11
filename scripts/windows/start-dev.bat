@echo off
REM ============================================
REM Lily Cafe POS - Development Start Script
REM Starts both servers in development mode
REM with hot-reload for development
REM ============================================

title Lily Cafe POS - Development Mode
color 0D

REM Get project root (2 levels up from scripts/windows/)
set PROJECT_ROOT=%~dp0..\..
cd /d "%PROJECT_ROOT%"

echo ====================================
echo  LILY CAFE POS - DEVELOPMENT MODE
echo ====================================
echo.
echo Performing pre-flight checks...
echo.

REM ====================
REM Pre-flight Checks
REM ====================

REM Check 1: Backend virtual environment exists
if not exist "backend\.venv" (
    echo [X] Backend virtual environment not found!
    echo.
    echo Creating virtual environment and installing dependencies...
    cd backend
    uv sync --extra printer
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create virtual environment!
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Backend environment created
) else (
    echo [OK] Backend environment found
)

REM Check 2: Frontend node_modules exists
if not exist "frontend\node_modules" (
    echo [!] Frontend dependencies not installed!
    echo.
    echo Installing npm packages...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install frontend dependencies!
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies found
)

REM Check 3: Database exists
if not exist "backend\restaurant.db" (
    echo [!] Database not found
    echo.
    echo The database will be created on first run.
    echo Run seed script if needed: cd backend ^&^& uv run python -m scripts.seed_data
    echo.
)

echo.
echo ====================================
echo All checks passed!
echo ====================================
echo.
echo Starting Development Servers...
echo (Hot-reload enabled)
echo.

REM ====================
REM Start Backend (Dev Mode)
REM ====================
echo [1/2] Starting Backend Server (Development)...
start "Lily Cafe - Backend (Dev)" cmd /k "cd /d "%PROJECT_ROOT%\backend" && echo ==================================== && echo   LILY CAFE POS - BACKEND (DEV) && echo ==================================== && echo. && echo Starting backend with hot-reload... && echo Backend: http://localhost:8000 && echo API Docs: http://localhost:8000/docs && echo. && echo File changes will auto-reload && echo Press Ctrl+C to stop the server && echo ==================================== && echo. && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to initialize
timeout /t 3 /nobreak > nul

REM ====================
REM Start Frontend (Dev Mode)
REM ====================
echo [2/2] Starting Frontend Server (Development)...
start "Lily Cafe - Frontend (Dev)" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && echo ==================================== && echo   LILY CAFE POS - FRONTEND (DEV) && echo ==================================== && echo. && echo Starting frontend with hot-reload... && echo Frontend: http://localhost:5173 && echo. && echo File changes will auto-reload && echo Press Ctrl+C to stop the server && echo ==================================== && echo. && npm run dev -- --host 0.0.0.0"

echo.
echo ====================================
echo BOTH SERVERS STARTED (DEV MODE)!
echo ====================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Development Features:
echo  - Hot-reload enabled
echo  - Source maps enabled
echo  - Detailed error messages
echo.
echo Wait 10-15 seconds for servers to start,
echo then open: http://localhost:5173
echo.
echo Close the Backend and Frontend windows
echo to stop the servers.
echo ====================================
echo.
echo This window can be closed safely.
echo.

pause
