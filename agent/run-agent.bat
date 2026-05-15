@echo off
cd /d "%~dp0"
python "%~dp0agent.py" >> "%~dp0agent.log" 2>&1
