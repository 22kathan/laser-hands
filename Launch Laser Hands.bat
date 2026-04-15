@echo off
title Laser Hands Launcher
echo =========================================
echo       Starting Laser Hands Project
echo =========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python is not installed on this system
    echo.
    
    :: Show popup dialog asking for permission to download Python
    powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $result = [System.Windows.Forms.MessageBox]::Show('Python is not installed on your system.`nWould you like to automatically download and install Python?`n`nThis will download Python 3.11 from python.org', 'Python Installation Required', [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question); exit ([int]($result -eq 'No'))"
    
    if errorlevel 1 (
        echo User cancelled installation.
        pause
        exit /b 1
    )
    
    echo Downloading Python 3.11...
    cd /d "%TEMP%"
    
    :: Download Python installer
    powershell -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-installer.exe' -UseBasicParsing; Write-Host 'Download complete' } catch { Write-Host 'Download failed: $_'; exit 1 }"
    
    if errorlevel 1 (
        echo Failed to download Python installer.
        echo Please visit https://www.python.org/downloads/ and install Python manually.
        pause
        exit /b 1
    )
    
    if exist "python-installer.exe" (
        echo Installing Python (this will take a few moments)...
        :: Run installer silently with all features enabled and add to PATH
        start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
        
        echo.
        echo Python installation complete!
        timeout /t 2 /nobreak > NUL
        
        :: Verify Python installation
        python --version >nul 2>&1
        if errorlevel 1 (
            echo Failed to verify Python installation.
            pause
            exit /b 1
        )
        
        :: Clean up installer
        del /f /q "python-installer.exe" >nul 2>&1
        
        :: Return to original directory
        cd /d "%~dp0"
    ) else (
        echo Failed to download Python installer.
        echo Please visit https://www.python.org/downloads/ and install Python manually.
        pause
        exit /b 1
    )
) else (
    echo [OK] Python is installed
)

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
