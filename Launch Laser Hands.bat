@echo off
title Laser Hands Launcher
echo =========================================
echo       Starting Laser Hands Project
echo =========================================
echo.

echo [1/2] Starting OS Controller backend (Python)...
:: Run the python script in a new console window so it stays open
start "OS Controller" cmd /c "python os_controller.py"

echo [2/2] Opening the Web Interface...
:: Wait a brief moment to ensure the websocket server is up
timeout /t 2 /nobreak > NUL

:: Open the index.html in the default web browser
start "" "index.html"

echo.
echo Launch sequence complete. You can close this window.
timeout /t 3 > NUL
exit
