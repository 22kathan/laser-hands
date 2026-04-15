@echo off
setlocal enabledelayedexpansion
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
    
    :: Create VBScript popup dialog (more reliable across all Windows versions)
    set "vbsfile=%temp%\python_prompt.vbs"
    (
        echo Dim shell, result
        echo Set shell = CreateObject("WScript.Shell"
        echo result = shell.popup("Python is not installed on your system." ^& vbCrLf ^& vbCrLf ^& "Would you like to automatically download and install Python 3.11?" ^& vbCrLf ^& vbCrLf ^& "This will take a few minutes.", 0, "Python Installation Required", 4 + 32
        echo If result = 6 Then
        echo   WScript.Quit(0
        echo Else
        echo   WScript.Quit(1
        echo End If
    ) > "!vbsfile!"
    
    :: Show the VBScript popup dialog
    cscript.exe //nologo "!vbsfile!" >nul 2>&1
    set "python_choice=!errorlevel!"
    del /f /q "!vbsfile!" >nul 2>&1
    
    if !python_choice! equ 1 (
        echo User cancelled installation.
        pause
        exit /b 1
    )
    
    echo.
    echo Downloading Python 3.11...
    set "download_dir=%TEMP%\laser_hands_python"
    if not exist "!download_dir!" mkdir "!download_dir!"
    cd /d "!download_dir!"
    
    :: Download Python installer using multiple methods for reliability
    echo Attempting download method 1: PowerShell...
    powershell -Command "try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-installer.exe' -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
    
    if not errorlevel 1 goto python_install
    
    echo PowerShell download failed. Attempting method 2: curl...
    curl -L -o python-installer.exe "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" >nul 2>&1
    
    if not errorlevel 1 goto python_install
    
    echo curl download failed. Please install Python manually.
    echo.
    echo Visit: https://www.python.org/downloads/release/python-3119/
    echo Download: python-3.11.9-amd64.exe
    pause
    exit /b 1
    
:python_install
    if not exist "python-installer.exe" (
        echo Failed to download Python installer.
        echo Please visit https://www.python.org/downloads/ and install Python manually.
        pause
        exit /b 1
    )
    
    echo Download successful! Installing Python...
    echo This will take a few moments. Please wait...
    echo.
    
    :: Run installer silently with all features enabled and add to PATH
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    set "install_result=!errorlevel!"
    
    echo.
    if !install_result! equ 0 (
        echo =========================================
        echo.
        echo     [PASS] Python Downloaded! [OK]
        echo.
        echo =========================================
        echo.
        timeout /t 2 /nobreak > NUL
        
        :: Refresh environment variables
        for /f "tokens=2*" %%A in ('reg query HKLM\SYSTEM\CurrentControlSet\Control\Session" "Manager\Environment /v PATH ^| findstr /i path') do set "PATH=%%B"
        
        :: Verify Python installation
        python --version >nul 2>&1
        if errorlevel 1 (
            echo Verifying installation... (restart may be needed)
            timeout /t 3 /nobreak > NUL
        ) else (
            echo [OK] Python verified and ready!
            echo.
        )
    ) else (
        echo =========================================
        echo.
        echo  [FAIL] Installation failed! [ERROR]
        echo.
        echo =========================================
        echo.
        echo Installation failed with error code !install_result!
        echo Please install Python manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    :: Clean up installer
    del /f /q "python-installer.exe" >nul 2>&1
    
    :: Return to original directory
    cd /d "%~dp0"
) else (
    echo =========================================
    echo.
    echo   [PASS] Python Already Installed [OK]
    echo.
    echo =========================================
    echo.
)

echo.
echo [1/2] Starting OS Controller backend (Python)...
echo Installing required dependencies...
python -m pip install -q -r requirements.txt >nul 2>&1

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
