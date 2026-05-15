@echo off
cd /d "%~dp0"
python agent.py >> agent.log 2>&1
