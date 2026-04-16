@echo off
setlocal enabledelayedexpansion
title Laser Hands - Setup & Launch (Standalone)
color 0B

:: Check if running from auto-startup after restart
set "startup_mode=0"
for /f "tokens=*" %%A in ('powershell -NoProfile -Command "try { Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'LaserHandsSetup' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty LaserHandsSetup } catch {}" 2^>nul') do (
    if "%%A" neq "" (
        set "startup_mode=1"
    )
)

if !startup_mode! equ 1 (
    echo [INFO] Resuming after system restart...
    echo.
)

echo.
echo =========================================
echo     LASER HANDS - Complete Setup
echo =========================================
echo.
echo This script will:
echo   1. Download Python 3.11 (if needed)
echo   2. Install Python (if needed)
echo   3. Download Laser Hands project files
echo   4. Launch the application
echo.
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
        echo result = shell.popup("Python 3.11 is not installed on your system." ^& vbCrLf ^& vbCrLf ^& "Would you like to automatically download and install Python?" ^& vbCrLf ^& vbCrLf ^& "This will take approximately 5-10 minutes.", 0, "Python Installation Required", 4 + 32
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
    echo =========================================
    echo      Downloading Python 3.11...
    echo =========================================
    echo.
    set "download_dir=%TEMP%\laser_hands_setup"
    if not exist "!download_dir!" mkdir "!download_dir!"
    cd /d "!download_dir!"
    
    :: Download Python installer with Timer and Progress Bar
    echo [PROGRESS] Initializing download...
    powershell -NoProfile -Command ^
        "$url = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe';" ^
        "$out = 'python-installer.exe';" ^
        "$start = Get-Date;" ^
        "Write-Host 'Download started at: ' -NoNewline; Write-Host ($start.ToString('HH:mm:ss')) -ForegroundColor Cyan;" ^
        "try {" ^
        "    $job = Start-BitsTransfer -Source $url -Destination $out -Asynchronous -ErrorAction Stop;" ^
        "    while ($job.State -eq 'Transferring' -or $job.State -eq 'Connecting' -or $job.State -eq 'Queued') {" ^
        "        $elapsed = (Get-Date) - $start;" ^
        "        $timeStr = '{0:D2}m {1:D2}s' -f [int][Math]::Floor($elapsed.TotalMinutes), $elapsed.Seconds;" ^
        "        $percent = if ($job.BytesTotal -gt 0) { ($job.BytesTransferred / $job.BytesTotal) * 100 } else { 0 };" ^
        "        $status = \"Elapsed: $timeStr | $([Math]::Round($job.BytesTransferred / 1MB, 1))MB / $([Math]::Round($job.BytesTotal / 1MB, 1))MB\";" ^
        "        Write-Progress -Activity 'Downloading Python 3.11 (Total: 5-15 mins)' -Status $status -PercentComplete $percent;" ^
        "        Start-Sleep -Seconds 1;" ^
        "    }" ^
        "    Complete-BitsTransfer -BitsJob $job;" ^
        "    $end = Get-Date; $total = $end - $start;" ^
        "    Write-Host '✓ Download Success!' -ForegroundColor Green;" ^
        "    Write-Host \"Total Time: $([int]$total.TotalMinutes)m $($total.Seconds)s\";" ^
        "} catch {" ^
        "    Write-Host '⚠ BITS method failed, trying fallback...' -ForegroundColor Yellow;" ^
        "    Invoke-WebRequest -Uri $url -OutFile $out;" ^
        "}"
    
    if not exist "python-installer.exe" (
        echo ⊗ All automated download methods failed.
        goto download_error
    )
    echo ✓ Method succeeded!
    goto python_install

:download_error
    
    echo.
    echo =========================================
    echo     [FAIL] Python Download Failed [ERROR]
    echo =========================================
    echo.
    echo All automated download methods failed.
    echo.
    echo Common causes:
    echo   - No internet connection
    echo   - Firewall blocking python.org
    echo   - Network proxy issues
    echo.
    echo Manual Installation:
    echo   1. Visit: https://www.python.org/downloads/release/python-3119/
    echo   2. Download: python-3.11.9-amd64.exe
    echo   3. Install with these settings:
    echo      - Check "Add Python to PATH" ^(IMPORTANT^)
    echo      - Install for all users ^(recommended^)
    echo   4. Run this batch file again
    echo.
    pause
    exit /b 1
    
:python_install
    if not exist "python-installer.exe" (
        echo Failed to download Python installer.
        echo Please visit https://www.python.org/downloads/ and install manually.
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
        echo ⊗ Downloaded file is corrupted (size: %file_size% bytes)
        echo Please try manual installation.
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
        echo     [PASS] Python Installed! [OK]
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
                echo [AUTO] System restart required to activate Python PATH
                echo [AUTO] Scheduling automatic restart...
                echo.
                
                :: Create a scheduled task to run this batch file on next startup
                set "script_path=%~f0"
                powershell -NoProfile -Command "try { New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'LaserHandsSetup' -Value '\"!script_path!\"' -Force | Out-Null; Write-Host 'Auto-start registered'; exit 0 } catch { exit 1 }" >nul 2>&1
                
                :: Immediate shutdown (0 seconds) with auto-restart
                shutdown /r /t 0 /c "Laser Hands: Auto-restart to activate Python" /d p:0:0
                exit /b 0
            )
        ) else (
            echo ✓ Python verified successfully!
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
        echo Error code: !install_result!
        echo.
        echo Try these solutions:
        echo   1. Run as Administrator ^(right-click batch file ^& select "Run as administrator"^)
        echo   2. Check disk space ^(need ^~150MB free^)
        echo   3. Install manually: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    
    :: Clean up installer
    del /f /q "python-installer.exe" >nul 2>&1
) else (
    echo =========================================
    echo.
    echo   [PASS] Python Already Installed [OK]
    echo.
    echo =========================================
    echo.
)

echo.
echo =========================================
echo   Downloading Laser Hands Project...
echo =========================================
echo.

:: Create project directory in user's Documents
set "project_dir=%USERPROFILE%\Documents\Laser Hands"
if not exist "!project_dir!" (
    echo Creating project directory...
    mkdir "!project_dir!"
)
cd /d "!project_dir!"

:: Download project files from GitHub
echo Downloading latest files from GitHub...
git --version >nul 2>&1
if errorlevel 1 (
    echo Installing git (one-time setup)...
    powershell -Command "Write-Host 'Git not found. Please install from: https://git-scm.com/download/win'" >nul 2>&1
    echo.
    echo Please install git: https://git-scm.com/download/win
    echo After installation, run this batch file again.
    pause
    exit /b 1
)

: Check if repo already exists
if exist ".git" (
    echo Repository already exists. Updating...
    git pull origin main >nul 2>&1
) else (
    echo Cloning Laser Hands repository...
    git clone https://github.com/22kathan/laser-hands.git . >nul 2>&1
)

if not exist "index.html" (
    echo Failed to download project files.
    echo Please download manually from: https://github.com/22kathan/laser-hands
    pause
    exit /b 1
)

echo ✓ Project files downloaded successfully!
echo.

:: Install Python dependencies
echo.
echo =========================================
echo   Installing Dependencies...
echo =========================================
echo.
echo Installing required Python packages...
python -m pip install -q -r requirements.txt >nul 2>&1

if errorlevel 1 (
    echo Warning: Some packages could not be installed
    echo Continuing anyway...
) else (
    echo ✓ All dependencies installed!
)

echo.
echo =========================================
echo   Launching Laser Hands...
echo =========================================
echo.

:: Run the launcher batch file
if exist "Launch Laser Hands.bat" (
    :: Clean up startup registry entry before calling launcher
    powershell -NoProfile -Command "try { Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'LaserHandsSetup' -ErrorAction SilentlyContinue | Out-Null } catch {}" >nul 2>&1
    
    call "Launch Laser Hands.bat"
) else (
    echo Error: Launch Laser Hands.bat not found
    echo Project files may not have downloaded correctly
    pause
    exit /b 1
)

:: Final cleanup
powershell -NoProfile -Command "try { Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'LaserHandsSetup' -ErrorAction SilentlyContinue | Out-Null } catch {}" >nul 2>&1

pause
exit /b 0
