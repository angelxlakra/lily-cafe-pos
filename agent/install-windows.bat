@echo off
echo === Lily Cafe Print Agent Setup ===
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv .venv

echo Installing dependencies...
.venv\Scripts\pip install -r requirements.txt --quiet

if not exist .env (
    echo Copying .env.example to .env ...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit agent\.env with your backend URL and printer settings!
)

echo Creating run-agent.bat ...
(
    echo @echo off
    echo title Lily Cafe Print Agent
    echo echo Starting Lily Cafe Print Agent...
    echo .venv\Scripts\python agent.py
    echo pause
) > run-agent.bat

echo.
echo === Setup complete ===
echo Next steps:
echo   1. Edit agent\.env  ^(set BACKEND_URL and AGENT_API_KEY^)
echo   2. Double-click run-agent.bat to start
echo   3. To auto-start on boot: copy run-agent.bat shortcut to shell:startup
echo.
pause
