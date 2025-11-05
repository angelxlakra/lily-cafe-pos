@echo off
title Lily Cafe POS - Launcher
color 0E

echo ====================================
echo    LILY CAFE POS SYSTEM LAUNCHER
echo ====================================
echo.
echo Starting both Backend and Frontend servers...
echo.

REM Start Backend in a new window
echo [1/2] Starting Backend Server...
start "Lily Cafe - Backend" cmd /k "%~dp0start-backend.bat"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

REM Start Frontend in a new window
echo [2/2] Starting Frontend Server...
start "Lily Cafe - Frontend" cmd /k "%~dp0start-frontend.bat"

echo.
echo ====================================
echo BOTH SERVERS STARTED!
echo ====================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
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
