@echo off
title Lily Cafe POS - Frontend Server
color 0B

echo ====================================
echo   LILY CAFE POS - FRONTEND SERVER
echo ====================================
echo.

cd /d "%~dp0frontend"

echo Starting frontend development server...
echo Frontend will be available at: http://localhost:5173
echo.
echo Make sure the backend is running before using the app!
echo.
echo Press Ctrl+C to stop the server
echo ====================================
echo.

npm run dev -- --host 0.0.0.0

pause
