@echo off
REM ============================================
REM Lily Cafe POS - Auto Update Script
REM Run this manually or via Task Scheduler
REM ============================================

setlocal enabledelayedexpansion

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Set log file with timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set LOG_FILE=logs\update_%datetime:~0,8%_%datetime:~8,6%.log

echo ============================================ >> "%LOG_FILE%"
echo Lily Cafe POS Update Started >> "%LOG_FILE%"
echo Time: %date% %time% >> "%LOG_FILE%"
echo ============================================ >> "%LOG_FILE%"
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH >> "%LOG_FILE%"
    echo [ERROR] Cannot perform auto-update >> "%LOG_FILE%"
    exit /b 1
)

echo [INFO] Checking for updates... >> "%LOG_FILE%"

REM Fetch latest changes
git fetch origin main >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to fetch updates from remote >> "%LOG_FILE%"
    exit /b 1
)

REM Check if there are updates
git diff --quiet HEAD origin/main
if errorlevel 1 (
    echo [INFO] Updates found! Installing... >> "%LOG_FILE%"

    REM Store current commit for rollback
    for /f "tokens=*" %%i in ('git rev-parse HEAD') do set OLD_COMMIT=%%i
    echo [INFO] Current commit: %OLD_COMMIT% >> "%LOG_FILE%"

    REM Create backup of database
    if exist "backend\restaurant.db" (
        echo [INFO] Backing up database... >> "%LOG_FILE%"
        if not exist "backups" mkdir backups
        copy /Y "backend\restaurant.db" "backups\restaurant_pre_update_%datetime:~0,8%_%datetime:~8,6%.db" >> "%LOG_FILE%"
        if errorlevel 1 (
            echo [WARNING] Database backup failed >> "%LOG_FILE%"
        ) else (
            echo [INFO] Database backed up successfully >> "%LOG_FILE%"
        )
    )

    REM Pull updates
    echo [INFO] Pulling updates... >> "%LOG_FILE%"
    git pull origin main >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Git pull failed! >> "%LOG_FILE%"
        echo [INFO] Rolling back... >> "%LOG_FILE%"
        git reset --hard %OLD_COMMIT% >> "%LOG_FILE%" 2>&1
        exit /b 1
    )

    REM Get new commit
    for /f "tokens=*" %%i in ('git rev-parse HEAD') do set NEW_COMMIT=%%i
    echo [INFO] Updated to commit: %NEW_COMMIT% >> "%LOG_FILE%"

    REM Update backend dependencies
    echo [INFO] Updating backend dependencies... >> "%LOG_FILE%"
    cd backend
    uv sync >> "..\%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Backend dependency update failed >> "..\%LOG_FILE%"
        cd ..
        git reset --hard %OLD_COMMIT% >> "%LOG_FILE%" 2>&1
        exit /b 1
    )
    cd ..
    echo [INFO] Backend dependencies updated >> "%LOG_FILE%"

    REM Update frontend dependencies
    echo [INFO] Updating frontend dependencies... >> "%LOG_FILE%"
    cd frontend
    call npm install >> "..\%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [WARNING] Frontend dependency update had issues >> "..\%LOG_FILE%"
    ) else (
        echo [INFO] Frontend dependencies updated >> "%LOG_FILE%"
    )
    cd ..

    echo. >> "%LOG_FILE%"
    echo ============================================ >> "%LOG_FILE%"
    echo [SUCCESS] Update completed successfully! >> "%LOG_FILE%"
    echo [INFO] Please restart the POS system >> "%LOG_FILE%"
    echo ============================================ >> "%LOG_FILE%"

    REM Create restart flag for notification
    echo %NEW_COMMIT% > logs\pending_restart.flag

) else (
    echo [INFO] No updates available >> "%LOG_FILE%"
    echo [INFO] System is up to date >> "%LOG_FILE%"
)

echo. >> "%LOG_FILE%"
echo Update check completed at %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Keep only last 30 log files
for /f "skip=30 delims=" %%F in ('dir /b /o-d logs\update_*.log 2^>nul') do (
    del "logs\%%F" 2>nul
)

exit /b 0
