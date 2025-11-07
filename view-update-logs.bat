@echo off
REM ============================================
REM Lily Cafe POS - Update Log Viewer
REM View recent update logs
REM ============================================

echo.
echo ============================================
echo    Lily Cafe POS - Update Logs
echo ============================================
echo.

if not exist "logs" (
    echo No logs directory found.
    echo Updates have not been run yet.
    pause
    exit /b 0
)

REM Count log files
set count=0
for %%f in (logs\update_*.log) do set /a count+=1

if %count%==0 (
    echo No update logs found.
    echo Updates have not been run yet.
    pause
    exit /b 0
)

echo Found %count% update log(s)
echo.

REM Show last 5 logs
echo Recent update logs:
echo.
set counter=0
for /f "delims=" %%f in ('dir /b /o-d logs\update_*.log') do (
    set /a counter+=1
    if !counter! leq 5 (
        echo [!counter!] %%f
    )
)

echo.
echo ============================================
echo.
set /p choice="Enter log number to view (1-5) or press Enter to view latest: "

if "%choice%"=="" set choice=1

set counter=0
for /f "delims=" %%f in ('dir /b /o-d logs\update_*.log') do (
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
pause
