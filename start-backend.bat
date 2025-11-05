@echo off
title Lily Cafe POS - Backend Server
color 0A

echo ====================================
echo   LILY CAFE POS - BACKEND SERVER
echo ====================================
echo.

cd /d "%~dp0backend"

echo Starting backend server...
echo Backend will be available at: http://localhost:8000
echo API documentation at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ====================================
echo.

uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
