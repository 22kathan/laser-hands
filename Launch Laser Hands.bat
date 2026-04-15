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
    echo [1/3] Attempting download method 1: PowerShell Invoke-WebRequest...
    powershell -NoProfile -Command "try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-installer.exe' -UseBasicParsing -TimeoutSec 120; if (Test-Path 'python-installer.exe') { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    
    if not errorlevel 1 (
        echo ✓ Method 1 succeeded!
        goto python_install
    )
    
    echo ⊗ Method 1 failed. [2/3] Attempting download method 2: curl...
    curl -L --max-time 120 -o python-installer.exe "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" >nul 2>&1
    
    if exist "python-installer.exe" (
        echo ✓ Method 2 succeeded!
        goto python_install
    )
    
    echo ⊗ Method 2 failed. [3/3] Attempting download method 3: BitsTransfer (Windows only)...
    powershell -NoProfile -Command "try { Start-BitsTransfer -Source 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -Destination 'python-installer.exe' -Timeout 120; if (Test-Path 'python-installer.exe') { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    
    if exist "python-installer.exe" (
        echo ✓ Method 3 succeeded!
        goto python_install
    )
    
    echo.
    echo =========================================
    echo     [FAIL] Python Download Failed [ERROR]
    echo =========================================
    echo.
    echo All automated download methods failed.
    echo Possible causes:
    echo   - No internet connection
    echo   - Firewall blocking python.org
    echo   - Network proxy issues
    echo.
    echo Solution: Install Python manually
    echo.
    echo Visit: https://www.python.org/downloads/release/python-3119/
    echo Download: python-3.11.9-amd64.exe
    echo Install with: python-3.11.9-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
    echo.
    pause
    exit /b 1
    
:python_install
    if not exist "python-installer.exe" (
        echo Failed to download Python installer.
        echo Please visit https://www.python.org/downloads/ and install Python manually.
        pause
        exit /b 1
    )
    
    echo.
    echo =========================================
    echo      Installing Python 3.11...
    echo =========================================
    echo.
    echo This will take a few moments. Please wait...
    echo Checking file integrity...
    
    :: Verify file size is reasonable (should be > 20MB)
    for %%A in (python-installer.exe) do set "file_size=%%~zA"
    if %file_size% LSS 20000000 (
        echo ⊗ Downloaded file appears corrupted (too small: %file_size% bytes)
        echo Please try manual installation: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo ✓ File integrity check passed
    echo.
    echo Running installer...
    
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
        echo Verifying installation...
        timeout /t 3 /nobreak > NUL
        
        :: Method 1: Refresh PATH from registry (PowerShell)
        echo Refreshing system PATH variables...
        powershell -NoProfile -Command "try { [Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('PATH', 'User'), 'Process'); Write-Host 'PATH refreshed'; exit 0 } catch { exit 1 }" >nul 2>&1
        
        :: Test Python in current session
        python --version >nul 2>&1
        if errorlevel 1 (
            echo ⊗ Python not found in current PATH
            echo.
            echo ✓ Python is installed but needs PATH refresh
            echo ✓ Attempting to add Python to PATH manually...
            
            :: Find Python installation directory
            for /f "delims=" %%A in ('powershell -NoProfile -Command "Get-ChildItem 'C:\Program Files\Python*' -Directory | Select-Object -First 1 -ExpandProperty FullName" 2^>nul') do set "PY_PATH=%%A"
            
            if defined PY_PATH (
                echo ✓ Found Python at: !PY_PATH!
                set "PATH=!PY_PATH!;!PY_PATH!\Scripts;!PATH!"
                echo ✓ Added Python to PATH
            ) else (
                echo.
                echo ⊠ IMPORTANT: Your system requires a restart to recognize Python
                echo.
                echo The Python installation is complete, but Windows needs to reload
                echo system configuration. Please:
                echo.
                echo   1. Save your work on other applications
                echo   2. Click OK to restart
                echo   3. Run this batch file again after restart
                echo.
                pause
                shutdown /r /t 30 /c "Laser Hands: Restarting to activate Python installation"
                exit /b 0
            )
        ) else (
            echo ✓ Python verified and ready!
            echo ✓ Python version: 
            python --version
            echo.
        )
    ) else (
        echo =========================================
        echo.
        echo  [FAIL] Installation failed! [ERROR]
        echo.
        echo =========================================
        echo.
        echo Installation failed with error code: !install_result!
        echo.
        echo Common solutions:
        echo   1. Run as Administrator (right-click batch file ^& select "Run as administrator")
        echo   2. Check disk space (need ~150MB free)
        echo   3. Try manual installation: https://www.python.org/downloads/
        echo.
        echo For detailed help, visit:
        echo   https://github.com/22kathan/laser-hands
        echo.
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
