@echo off
REM ============================================
REM Lily Cafe POS - Manual Update Script
REM Double-click this to update immediately
REM ============================================

echo.
echo ============================================
echo    Lily Cafe POS - Manual Update
echo ============================================
echo.
echo This will:
echo  1. Check for updates from the server
echo  2. Backup your database
echo  3. Install updates if available
echo  4. Update dependencies
echo.
echo Make sure the POS system is NOT running!
echo.
pause

echo.
echo Starting update process...
echo.

call auto-update.bat

if errorlevel 1 (
    echo.
    echo ============================================
    echo    UPDATE FAILED!
    echo ============================================
    echo.
    echo Please check the log file in the logs folder
    echo or contact your developer.
    echo.
    pause
    exit /b 1
)

REM Check if restart is needed
if exist "logs\pending_restart.flag" (
    echo.
    echo ============================================
    echo    UPDATE SUCCESSFUL!
    echo ============================================
    echo.
    echo Updates have been installed.
    echo Please restart the POS system:
    echo  1. Close this window
    echo  2. Double-click start-both.bat
    echo.
    del "logs\pending_restart.flag"
) else (
    echo.
    echo ============================================
    echo    NO UPDATES AVAILABLE
    echo ============================================
    echo.
    echo Your system is already up to date!
    echo.
)

pause
