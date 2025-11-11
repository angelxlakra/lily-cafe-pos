@echo off
REM ============================================
REM Lily Cafe POS - Log Viewer
REM View recent update logs
REM ============================================

setlocal enabledelayedexpansion

REM Get project root (2 levels up from scripts/windows/)
set PROJECT_ROOT=%~dp0..\..
cd /d "%PROJECT_ROOT%"

title Lily Cafe POS - Update Logs
color 0E

echo.
echo ============================================
echo    Lily Cafe POS - Update Logs
echo ============================================
echo.

if not exist "logs" (
    echo No logs directory found.
    echo Updates have not been run yet.
    echo.
    pause
    exit /b 0
)

REM Count log files
set count=0
for %%f in (logs\update_*.log) do set /a count+=1

if %count%==0 (
    echo No update logs found.
    echo Updates have not been run yet.
    echo.
    pause
    exit /b 0
)

echo Found %count% update log(s)
echo.

REM Show last 5 logs
echo Recent update logs:
echo.
set counter=0
for /f "delims=" %%f in ('dir /b /o-d logs\update_*.log 2^>nul') do (
    set /a counter+=1
    if !counter! leq 5 (
        echo [!counter!] %%f
    )
)

echo.
echo ============================================
echo.
set /p choice="Enter log number to view (1-5) or press Enter for latest: "

if "%choice%"=="" set choice=1

REM Validate input
if "%choice%" lss "1" set choice=1
if "%choice%" gtr "5" set choice=5

set counter=0
for /f "delims=" %%f in ('dir /b /o-d logs\update_*.log 2^>nul') do (
    set /a counter+=1
    if !counter!==%choice% (
        echo.
        echo ============================================
        echo    Viewing: %%f
        echo ============================================
        echo.
        type "logs\%%f"
        echo.
        echo ============================================
        goto :done
    )
)

:done
echo.
echo To view all logs, check the logs\ folder
echo.
pause
