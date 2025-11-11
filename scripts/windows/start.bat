@echo off
REM ============================================
REM Lily Cafe POS - Production Start Script
REM Starts both servers with production builds
REM ============================================

title Lily Cafe POS - Launcher
color 0E

REM Get project root (2 levels up from scripts/windows/)
set PROJECT_ROOT=%~dp0..\..
cd /d "%PROJECT_ROOT%"

echo ====================================
echo    LILY CAFE POS SYSTEM LAUNCHER
echo ====================================
echo.
echo Performing pre-flight checks...
echo.

REM ====================
REM Pre-flight Checks
REM ====================

REM Check 1: Frontend build exists
if not exist "frontend\dist\index.html" (
    echo [X] Frontend not built!
    echo.
    echo The frontend needs to be built before starting.
    echo Run: scripts\windows\update.bat
    echo.
    echo Or build manually:
    echo   cd frontend
    echo   npm run build
    echo.
    pause
    exit /b 1
)
echo [OK] Frontend build found

REM Check 2: Backend virtual environment exists
if not exist "backend\.venv" (
    echo [X] Backend virtual environment not found!
    echo.
    echo Please run: scripts\windows\update.bat
    echo.
    pause
    exit /b 1
)
echo [OK] Backend environment found

REM Check 3: Check if pywin32 is installed (for printer support)
cd backend
uv pip list 2>nul | find "pywin32" >nul
if errorlevel 1 (
    echo [!] Warning: pywin32 not installed - printing may not work
    echo.
    echo To fix this, run: scripts\windows\update.bat
    echo Or manually: cd backend ^&^& uv sync --extra printer
    echo.
    echo Continue anyway? (Printing will not work)
    pause
) else (
    echo [OK] Printer support (pywin32) installed
)
cd ..

REM Check 4: Database exists
if not exist "backend\restaurant.db" (
    echo [!] Warning: Database not found
    echo.
    echo The database will be created on first run.
    echo.
    pause
) else (
    echo [OK] Database found
)

echo.
echo ====================================
echo All checks passed!
echo ====================================
echo.
echo Starting both Backend and Frontend servers...
echo.

REM ====================
REM Start Backend
REM ====================
echo [1/2] Starting Backend Server...
start "Lily Cafe - Backend (Production)" cmd /k "cd /d "%PROJECT_ROOT%\backend" && echo ==================================== && echo   LILY CAFE POS - BACKEND SERVER && echo ==================================== && echo. && echo Starting backend server... && echo Backend: http://localhost:8000 && echo API Docs: http://localhost:8000/docs && echo. && echo Press Ctrl+C to stop the server && echo ==================================== && echo. && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM Wait for backend to initialize
timeout /t 3 /nobreak > nul

REM ====================
REM Start Frontend (Preview Server)
REM ====================
echo [2/2] Starting Frontend Preview Server...
start "Lily Cafe - Frontend (Production)" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && echo ==================================== && echo   LILY CAFE POS - FRONTEND SERVER && echo ==================================== && echo. && echo Starting frontend preview server... && echo Frontend: http://localhost:4173 && echo. && echo Serving production build from dist/ && echo. && echo Press Ctrl+C to stop the server && echo ==================================== && echo. && npm run preview -- --host 0.0.0.0"

echo.
echo ====================================
echo BOTH SERVERS STARTED!
echo ====================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:4173
echo API Docs: http://localhost:8000/docs
echo.
echo Wait 10-15 seconds for servers to start,
echo then open: http://localhost:4173
echo.
echo Close the Backend and Frontend windows
echo to stop the servers.
echo ====================================
echo.
echo This window can be closed safely.
echo.

pause
