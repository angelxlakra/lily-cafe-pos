@echo off
REM ============================================
REM Lily Cafe POS - Update Script
REM Checks for updates, builds, and installs
REM Can be run manually or via Task Scheduler
REM ============================================

setlocal enabledelayedexpansion

REM Determine if running in interactive mode
set INTERACTIVE=0
echo %cmdcmdline% | find /i "%~0" >nul
if not errorlevel 1 set INTERACTIVE=1

REM Get script directory (2 levels up from scripts/windows/)
set SCRIPT_DIR=%~dp0..\..
cd /d "%SCRIPT_DIR%"

REM Store absolute project root path
set PROJECT_ROOT=%CD%

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Set log file with timestamp (absolute path)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set LOG_FILE=%PROJECT_ROOT%\logs\update_%datetime:~0,8%_%datetime:~8,6%.log

if %INTERACTIVE%==1 (
    echo.
    echo ============================================
    echo    Lily Cafe POS - Update System
    echo ============================================
    echo.
    echo This will:
    echo  1. Check for updates from the server
    echo  2. Backup your database
    echo  3. Install updates if available
    echo  4. Update backend dependencies
    echo  5. Build frontend for production
    echo  6. Install printer drivers (pywin32)
    echo.
    echo Make sure the POS system is NOT running!
    echo.
    pause
    echo.
    echo Starting update process...
    echo.
)

echo ============================================ >> "%LOG_FILE%"
echo Lily Cafe POS Update Started >> "%LOG_FILE%"
echo Time: %date% %time% >> "%LOG_FILE%"
echo ============================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH >> "%LOG_FILE%"
    echo [ERROR] Cannot perform auto-update >> "%LOG_FILE%"
    if %INTERACTIVE%==1 (
        echo.
        echo ERROR: Git is not installed!
        echo Please install Git and try again.
        pause
    )
    exit /b 1
)

echo [INFO] Checking for updates... >> "%LOG_FILE%"
if %INTERACTIVE%==1 echo [1/7] Checking for updates...

REM Fetch latest changes
git fetch origin main >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to fetch updates from remote >> "%LOG_FILE%"
    if %INTERACTIVE%==1 (
        echo ERROR: Failed to fetch updates!
        echo Check your internet connection.
        pause
    )
    exit /b 1
)

REM Check if there are updates
git diff --quiet HEAD origin/main
if errorlevel 1 (
    echo [INFO] Updates found! Installing... >> "%LOG_FILE%"
    if %INTERACTIVE%==1 echo [2/7] Updates found! Installing...

    REM Store current commit for rollback
    for /f "tokens=*" %%i in ('git rev-parse HEAD') do set OLD_COMMIT=%%i
    echo [INFO] Current commit: %OLD_COMMIT% >> "%LOG_FILE%"

    REM Create backup of database
    if exist "backend\restaurant.db" (
        echo [INFO] Backing up database... >> "%LOG_FILE%"
        if %INTERACTIVE%==1 echo [3/7] Backing up database...
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
    if %INTERACTIVE%==1 echo [4/7] Pulling updates from server...
    git pull origin main >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Git pull failed! >> "%LOG_FILE%"
        echo [INFO] Rolling back... >> "%LOG_FILE%"
        git reset --hard %OLD_COMMIT% >> "%LOG_FILE%" 2>&1
        if %INTERACTIVE%==1 (
            echo ERROR: Update failed! Rolling back...
            pause
        )
        exit /b 1
    )

    REM Get new commit
    for /f "tokens=*" %%i in ('git rev-parse HEAD') do set NEW_COMMIT=%%i
    echo [INFO] Updated to commit: %NEW_COMMIT% >> "%LOG_FILE%"

    REM Update backend dependencies (including printer support)
    echo [INFO] Updating backend dependencies... >> "%LOG_FILE%"
    if %INTERACTIVE%==1 echo [5/7] Updating backend dependencies and printer drivers...
    cd backend
    uv sync --extra printer >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Backend dependency update failed >> "%LOG_FILE%"
        cd ..
        git reset --hard %OLD_COMMIT% >> "%LOG_FILE%" 2>&1
        if %INTERACTIVE%==1 (
            echo ERROR: Dependency update failed! Rolling back...
            pause
        )
        exit /b 1
    )
    cd ..
    echo [INFO] Backend dependencies updated (including pywin32 for printing) >> "%LOG_FILE%"

    REM Update and build frontend
    echo [INFO] Updating and building frontend... >> "%LOG_FILE%"
    if %INTERACTIVE%==1 echo [6/7] Updating and building frontend for production...
    cd frontend
    call npm install >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [WARNING] Frontend dependency update had issues >> "%LOG_FILE%"
    ) else (
        echo [INFO] Frontend dependencies updated >> "%LOG_FILE%"
    )

    REM Build frontend for production
    echo [INFO] Building frontend... >> "%LOG_FILE%"
    call npm run build >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Frontend build failed >> "%LOG_FILE%"
        cd ..
        git reset --hard %OLD_COMMIT% >> "%LOG_FILE%" 2>&1
        if %INTERACTIVE%==1 (
            echo ERROR: Frontend build failed! Rolling back...
            pause
        )
        exit /b 1
    )
    echo [INFO] Frontend built successfully >> "%LOG_FILE%"
    cd ..

    if %INTERACTIVE%==1 echo [7/7] Finalizing update...

    echo. >> "%LOG_FILE%"
    echo ============================================ >> "%LOG_FILE%"
    echo [SUCCESS] Update completed successfully! >> "%LOG_FILE%"
    echo [INFO] Backend dependencies: Updated >> "%LOG_FILE%"
    echo [INFO] Printer drivers (pywin32): Installed >> "%LOG_FILE%"
    echo [INFO] Frontend: Built and ready >> "%LOG_FILE%"
    echo [INFO] Please restart the POS system >> "%LOG_FILE%"
    echo ============================================ >> "%LOG_FILE%"

    REM Create restart flag for notification
    echo %NEW_COMMIT% > logs\pending_restart.flag

    if %INTERACTIVE%==1 (
        echo.
        echo ============================================
        echo    UPDATE SUCCESSFUL!
        echo ============================================
        echo.
        echo Updates have been installed.
        echo.
        echo Changes:
        echo  - Backend dependencies updated
        echo  - Printer drivers (pywin32) installed
        echo  - Frontend built for production
        echo.
        echo Please restart the POS system:
        echo  1. Close this window
        echo  2. Run: scripts\windows\start.bat
        echo.
        del "logs\pending_restart.flag"
    )

) else (
    echo [INFO] No updates available >> "%LOG_FILE%"
    echo [INFO] System is up to date >> "%LOG_FILE%"

    if %INTERACTIVE%==1 (
        echo.
        echo ============================================
        echo    NO UPDATES AVAILABLE
        echo ============================================
        echo.
        echo Your system is already up to date!
        echo.
    )
)

echo. >> "%LOG_FILE%"
echo Update check completed at %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Keep only last 30 log files
for /f "skip=30 delims=" %%F in ('dir /b /o-d "%PROJECT_ROOT%\logs\update_*.log" 2^>nul') do (
    del "%PROJECT_ROOT%\logs\%%F" 2>nul
)

if %INTERACTIVE%==1 pause

exit /b 0
