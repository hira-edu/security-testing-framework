@echo off
:: Security Testing Framework - Test Environment Deployment Script
:: CMD/Batch Deployment for Controlled Testing Environments
:: WARNING: Only use in isolated test environments you own

setlocal EnableDelayedExpansion

:: Configuration
set "INSTALL_PATH=C:\SecurityTestFramework"
set "TARGET_PROCESS=LockDownBrowser.exe"
set "MONITORING_DURATION=0"
set "AUTO_START=1"
set "PERSISTENT=0"
set "HIDDEN=0"

:: Colors
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "RESET=[0m"

echo %CYAN%=========================================%RESET%
echo %CYAN%SECURITY TESTING FRAMEWORK DEPLOYMENT%RESET%
echo %CYAN%Test Environment Setup Script v1.0%RESET%
echo %CYAN%=========================================%RESET%
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%[!] This script requires Administrator privileges%RESET%
    echo %YELLOW%[*] Requesting elevated privileges...%RESET%
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo %GREEN%[+] Running with Administrator privileges%RESET%

:: Create installation directory
echo %YELLOW%[*] Creating installation directory...%RESET%
if not exist "%INSTALL_PATH%" (
    mkdir "%INSTALL_PATH%"
    echo %GREEN%[+] Created directory: %INSTALL_PATH%%RESET%
)

:: Download framework
echo %YELLOW%[*] Downloading Security Testing Framework...%RESET%
cd /d "%INSTALL_PATH%"

:: Check if Git is available
where git >nul 2>&1
if %errorLevel% equ 0 (
    echo %YELLOW%[*] Using Git to clone repository...%RESET%
    git clone https://github.com/hira-edu/security-testing-framework.git . >nul 2>&1
    if %errorLevel% equ 0 (
        echo %GREEN%[+] Repository cloned successfully%RESET%
    ) else (
        echo %RED%[!] Git clone failed%RESET%
        goto :DOWNLOAD_ZIP
    )
) else (
    :DOWNLOAD_ZIP
    echo %YELLOW%[*] Downloading as ZIP archive...%RESET%
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/hira-edu/security-testing-framework/archive/refs/heads/main.zip' -OutFile '%TEMP%\stf.zip' -UseBasicParsing}" >nul 2>&1

    if exist "%TEMP%\stf.zip" (
        echo %YELLOW%[*] Extracting files...%RESET%
        powershell -Command "Expand-Archive -Path '%TEMP%\stf.zip' -DestinationPath '%TEMP%' -Force" >nul 2>&1
        xcopy "%TEMP%\security-testing-framework-main\*" "%INSTALL_PATH%\" /E /Y /Q >nul 2>&1
        del "%TEMP%\stf.zip" >nul 2>&1
        rd /s /q "%TEMP%\security-testing-framework-main" >nul 2>&1
        echo %GREEN%[+] Files extracted successfully%RESET%
    ) else (
        echo %RED%[!] Download failed%RESET%
        echo Please download manually from: https://github.com/hira-edu/security-testing-framework
        pause
        exit /b 1
    )
)

:: Create requirements.txt if not exists
if not exist "requirements.txt" (
    echo %YELLOW%[*] Creating requirements.txt...%RESET%
    (
        echo psutil^>=5.8.0
        echo pywin32^>=300
        echo pillow^>=9.0.0
        echo numpy^>=1.20.0
        echo requests^>=2.26.0
        echo pyyaml^>=5.4.1
    ) > requirements.txt
)

:: Install Python dependencies
echo %YELLOW%[*] Installing Python dependencies...%RESET%
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt >nul 2>&1
if %errorLevel% equ 0 (
    echo %GREEN%[+] Dependencies installed%RESET%
) else (
    echo %YELLOW%[!] Some dependencies may have failed to install%RESET%
)

:: Create launcher script
echo %YELLOW%[*] Creating launcher scripts...%RESET%

:: Create start_monitoring.bat
(
echo @echo off
echo cd /d "%INSTALL_PATH%"
echo set PYTHONPATH=%INSTALL_PATH%
echo.
echo :: Kill any existing instances
echo taskkill /F /IM python.exe /FI "WINDOWTITLE eq SecurityTestFramework*" ^>nul 2^>^&1
echo.
echo :: Start with all features enabled
echo start "SecurityTestFramework" /MIN python launcher.py ^^
echo     --auto ^^
echo     --monitor ^^
echo     --stealth ^^
echo     --comprehensive ^^
echo     --target "%TARGET_PROCESS%" ^^
echo     --duration %MONITORING_DURATION% ^^
echo     --silent ^^
echo     --export "%INSTALL_PATH%\monitoring_data"
echo.
echo exit
) > "%INSTALL_PATH%\start_monitoring.bat"

echo %GREEN%[+] Created start_monitoring.bat%RESET%

:: Create silent launcher
(
echo @echo off
echo cd /d "%INSTALL_PATH%"
echo set PYTHONPATH=%INSTALL_PATH%
echo.
echo :: Kill existing instances
echo taskkill /F /IM python.exe /FI "WINDOWTITLE eq SecurityTestFramework*" ^>nul 2^>^&1
echo.
echo :: Start hidden
echo powershell -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'launcher.py', '--auto', '--monitor', '--stealth', '--target', '%TARGET_PROCESS%', '--silent' -WindowStyle Hidden"
echo.
echo exit
) > "%INSTALL_PATH%\start_hidden.bat"

echo %GREEN%[+] Created start_hidden.bat%RESET%

:: Create VBScript launcher for completely silent execution
echo %YELLOW%[*] Creating silent launcher...%RESET%
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run chr^(34^) ^& "%INSTALL_PATH%\start_monitoring.bat" ^& chr^(34^), 0, False
echo Set WshShell = Nothing
) > "%INSTALL_PATH%\silent_start.vbs"

echo %GREEN%[+] Created silent_start.vbs%RESET%

:: Create scheduled task for auto-start
if "%AUTO_START%"=="1" (
    echo %YELLOW%[*] Creating scheduled task for automatic startup...%RESET%

    :: Delete existing task if exists
    schtasks /delete /tn "SecurityTestFramework" /f >nul 2>&1

    :: Create new task to run at startup
    schtasks /create /tn "SecurityTestFramework" /tr "wscript.exe '%INSTALL_PATH%\silent_start.vbs'" /sc onstart /ru SYSTEM /rl HIGHEST /f >nul 2>&1

    :: Create task to run at logon
    schtasks /create /tn "SecurityTestFramework_Logon" /tr "wscript.exe '%INSTALL_PATH%\silent_start.vbs'" /sc onlogon /ru "%USERNAME%" /rl HIGHEST /f >nul 2>&1

    echo %GREEN%[+] Scheduled tasks created%RESET%
    echo %GREEN%[+] Will auto-start at system boot and user logon%RESET%
)

:: Add registry persistence if requested
if "%PERSISTENT%"=="1" (
    echo %YELLOW%[*] Adding registry persistence...%RESET%

    :: Add to CurrentUser Run
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SecurityTestFramework" /t REG_SZ /d "wscript.exe '%INSTALL_PATH%\silent_start.vbs'" /f >nul 2>&1
    echo %GREEN%[+] Added to CurrentUser Run key%RESET%

    :: Add to LocalMachine Run (requires admin)
    reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "SecurityTestFramework" /t REG_SZ /d "wscript.exe '%INSTALL_PATH%\silent_start.vbs'" /f >nul 2>&1
    echo %GREEN%[+] Added to LocalMachine Run key%RESET%

    :: Add to Winlogon (advanced persistence)
    for /f "tokens=2*" %%a in ('reg query "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /v Userinit 2^>nul ^| find "Userinit"') do set "currentUserInit=%%b"
    reg add "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /v "Userinit" /t REG_SZ /d "%currentUserInit%,wscript.exe '%INSTALL_PATH%\silent_start.vbs'" /f >nul 2>&1
    echo %GREEN%[+] Added to Winlogon%RESET%
)

:: Add Windows Defender exclusions
echo %YELLOW%[*] Configuring Windows Defender exclusions...%RESET%
powershell -Command "Add-MpPreference -ExclusionPath '%INSTALL_PATH%' -Force" >nul 2>&1
powershell -Command "Add-MpPreference -ExclusionProcess 'python.exe' -Force" >nul 2>&1
echo %GREEN%[+] Defender exclusions configured%RESET%

:: Create configuration file with maximum capabilities
echo %YELLOW%[*] Creating maximum capability configuration...%RESET%
(
echo {
echo     "version": "1.0.0",
echo     "build_time": "%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%",
echo     "security_level": "HIGH",
echo     "enable_logging": true,
echo     "stealth_mode": true,
echo     "auto_update": true,
echo     "modules": {
echo         "screen_capture": true,
echo         "process_monitor": true,
echo         "api_hooks": true,
echo         "memory_scanner": true,
echo         "network_monitor": true,
echo         "gui": false
echo     },
echo     "capture": {
echo         "method": "enhanced_capture",
echo         "fallback_chain": [
echo             "windows_graphics_capture",
echo             "dxgi_desktop_duplication",
echo             "direct3d_capture",
echo             "gdi_capture"
echo         ],
echo         "frame_rate": 60,
echo         "quality": "high",
echo         "compression": true,
echo         "compression_level": 6,
echo         "hardware_acceleration": true,
echo         "buffer_size": 10485760
echo     },
echo     "hooks": {
echo         "directx": {
echo             "enabled": true,
echo             "versions": [ "11", "12" ],
echo             "interfaces": [ "IDXGISwapChain", "ID3D11Device", "ID3D12Device" ]
echo         },
echo         "windows_api": {
echo             "enabled": true,
echo             "functions": [
echo                 "SetForegroundWindow",
echo                 "GetForegroundWindow",
echo                 "CreateProcess",
echo                 "TerminateProcess"
echo             ]
echo         },
echo         "keyboard": {
echo             "enabled": true,
echo             "blocked_keys": [ "F12", "VK_SNAPSHOT" ],
echo             "hotkeys": {
echo                 "ctrl+alt+s": "screenshot",
echo                 "ctrl+alt+q": "quit"
echo             }
echo         },
echo         "process": {
echo             "enabled": false
echo         }
echo     },
echo     "performance": {
echo         "monitoring": true,
echo         "sampling_interval": 1000,
echo         "memory_tracking": true,
echo         "leak_threshold": 1048576,
echo         "optimization": {
echo             "memory_pool": true,
echo             "thread_pool": true,
echo             "hardware_acceleration": true
echo         },
echo         "limits": {
echo             "max_cpu_usage": 80.0,
echo             "max_memory_usage": 1073741824,
echo             "max_frame_rate": 60
echo         }
echo     },
echo     "security": {
echo         "anti_detection": true,
echo         "obfuscation": false,
echo         "integrity_checking": true
echo     },
echo     "logging": {
echo         "level": "medium",
echo         "file": "undownunlock.log",
echo         "console_output": true
echo     },
echo     "bypass_methods": {
echo         "enabled": true,
echo         "package_root": "src.external.bypass_methods",
echo         "native": {
echo             "dll": "native/bypass_methods/dll/UndownUnlockDXHook.dll",
echo             "auto_stage": true
echo         },
echo         "features": {
echo             "capture": true,
echo             "api_hooks": true,
echo             "security": true,
echo             "gui": false
echo         }
echo     },
echo     "targets": [
echo         "%TARGET_PROCESS%"
echo     ]
echo }
) > "%INSTALL_PATH%\config.json"

echo %GREEN%[+] Configuration created with all features enabled%RESET%

:: Create uninstaller
echo %YELLOW%[*] Creating uninstaller...%RESET%
(
echo @echo off
echo echo Removing Security Testing Framework...
echo.
echo :: Stop processes
echo taskkill /F /IM python.exe /FI "PATH eq %INSTALL_PATH%*" ^>nul 2^>^&1
echo.
echo :: Remove scheduled tasks
echo schtasks /delete /tn "SecurityTestFramework" /f ^>nul 2^>^&1
echo schtasks /delete /tn "SecurityTestFramework_Logon" /f ^>nul 2^>^&1
echo.
echo :: Remove registry entries
echo reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "SecurityTestFramework" /f ^>nul 2^>^&1
echo reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "SecurityTestFramework" /f ^>nul 2^>^&1
echo.
echo :: Remove Defender exclusions
echo powershell -Command "Remove-MpPreference -ExclusionPath '%INSTALL_PATH%' -Force" ^>nul 2^>^&1
echo.
echo :: Remove files
echo rd /s /q "%INSTALL_PATH%" ^>nul 2^>^&1
echo.
echo echo Security Testing Framework removed
echo pause
) > "%INSTALL_PATH%\uninstall.bat"

echo %GREEN%[+] Created uninstall.bat%RESET%

:: Start monitoring if auto-start is enabled
if "%AUTO_START%"=="1" (
    echo %YELLOW%[*] Starting monitoring framework...%RESET%

    if "%HIDDEN%"=="1" (
        start wscript.exe "%INSTALL_PATH%\silent_start.vbs"
    ) else (
        start /min cmd /c "%INSTALL_PATH%\start_monitoring.bat"
    )

    timeout /t 2 /nobreak >nul
    echo %GREEN%[+] Monitoring started%RESET%
)

:: Display summary
echo.
echo %GREEN%=========================================%RESET%
echo %GREEN%DEPLOYMENT COMPLETE%RESET%
echo %GREEN%=========================================%RESET%
echo.
echo Framework Location: %INSTALL_PATH%
echo Start Manually: %INSTALL_PATH%\start_monitoring.bat
echo Start Hidden: %INSTALL_PATH%\silent_start.vbs
echo View Logs: %INSTALL_PATH%\monitoring_data\
echo Uninstall: %INSTALL_PATH%\uninstall.bat
echo.

if "%AUTO_START%"=="1" (
    echo %GREEN%[✓] Monitoring is now active%RESET%
    echo %GREEN%[✓] Will auto-start on system boot%RESET%
)

if "%PERSISTENT%"=="1" (
    echo %GREEN%[✓] Persistence mechanisms enabled%RESET%
)

echo.
echo Press any key to exit...
pause >nul
