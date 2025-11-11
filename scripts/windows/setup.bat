@echo off
REM ============================================
REM Lily Cafe POS - Initial Setup Script
REM Run this once to configure auto-updates
REM ============================================

title Lily Cafe POS - Setup
color 0B

REM Check for admin rights
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================
    echo    ADMINISTRATOR RIGHTS REQUIRED
    echo ============================================
    echo.
    echo This script needs administrator rights to:
    echo  - Setup automatic update scheduler
    echo  - Configure Windows Task Scheduler
    echo.
    echo Please right-click this file and select
    echo "Run as Administrator"
    echo.
    pause
    exit /b 1
)

REM Get project root (2 levels up from scripts/windows/)
set PROJECT_ROOT=%~dp0..\..
cd /d "%PROJECT_ROOT%"

echo.
echo ============================================
echo    LILY CAFE POS - INITIAL SETUP
echo ============================================
echo.
echo This will configure automatic updates for
echo your Lily Cafe POS system.
echo.
echo Installation path: %CD%
echo.
pause

echo.
echo ====================================
echo   STEP 1: AUTO-UPDATE CONFIGURATION
echo ====================================
echo.
echo When should updates run automatically?
echo Recommended: After closing time (e.g., 03:00)
echo.
set /p UPDATE_TIME="Enter time in 24-hour format (HH:MM): "

REM Validate time format
echo %UPDATE_TIME% | findstr /r "^[0-2][0-9]:[0-5][0-9]$" >nul
if errorlevel 1 (
    echo Invalid time format. Using default: 03:00
    set UPDATE_TIME=03:00
)

echo.
echo ====================================
echo   STEP 2: CREATING SCHEDULED TASK
echo ====================================
echo.
echo Setting up automatic updates to run at %UPDATE_TIME% daily...
echo.

REM Delete existing task if it exists
schtasks /query /tn "Lily Cafe POS Auto Update" >nul 2>&1
if not errorlevel 1 (
    echo Removing old scheduled task...
    schtasks /delete /tn "Lily Cafe POS Auto Update" /f >nul 2>&1
)

REM Create the scheduled task
schtasks /create ^
    /tn "Lily Cafe POS Auto Update" ^
    /tr "\"%CD%\scripts\windows\update.bat\"" ^
    /sc daily ^
    /st %UPDATE_TIME% ^
    /ru SYSTEM ^
    /rl HIGHEST ^
    /f >nul 2>&1

if errorlevel 1 (
    echo.
    echo ============================================
    echo    ERROR: Failed to create scheduled task
    echo ============================================
    echo.
    echo Please try:
    echo  1. Run this script as Administrator
    echo  2. Check Task Scheduler service is running
    echo  3. Contact your developer
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo    SUCCESS! Setup Complete
echo ============================================
echo.
echo Configuration:
echo  - Update time: Daily at %UPDATE_TIME%
echo  - Wake computer: Enabled
echo  - Run on battery: Enabled
echo  - Auto retry: Enabled
echo.

echo ====================================
echo   STEP 3: RUNNING INITIAL UPDATE
echo ====================================
echo.
echo Running initial update to ensure everything is configured...
echo.

call "%CD%\scripts\windows\update.bat"

if errorlevel 1 (
    echo.
    echo ============================================
    echo    WARNING: Initial update had issues
    echo ============================================
    echo.
    echo The scheduler is configured, but the initial
    echo update encountered some problems.
    echo.
    echo Check the logs folder for details.
    echo.
) else (
    echo.
    echo ============================================
    echo    ALL DONE!
    echo ============================================
    echo.
)

echo What happens next:
echo  1. Computer will wake at %UPDATE_TIME% daily
echo  2. Check for updates from developer
echo  3. Install updates if available
echo  4. Build frontend and install dependencies
echo  5. Log results to logs folder
echo.
echo You can:
echo  - Start POS: scripts\windows\start.bat
echo  - Manual update: scripts\windows\update.bat
echo  - View logs: scripts\windows\logs.bat
echo.
echo Keep your computer plugged in at night!
echo.

pause
