@echo off
setlocal enabledelayedexpansion

:: Security Testing Framework - CMD Installer
:: Usage: curl -L https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.bat | cmd
:: Or download and run: install.bat

:: Configuration
set "REPO_OWNER=hira-edu"
set "REPO_NAME=security-testing-framework"
set "APP_NAME=SecurityTestingFramework"
set "INSTALL_PATH=%LOCALAPPDATA%\SecurityTestingFramework"

:: Check parameters
if "%1"=="--portable" (
    set "INSTALL_PATH=%CD%"
    set "PORTABLE=1"
)
if "%1"=="--help" goto :help

:: Banner
echo.
echo =============================================================================
echo      Security Testing Framework - Windows Installer
echo                  Professional Security Tools
echo =============================================================================
echo.

:: Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Not running as administrator.
    echo Some features may be limited. For full functionality, run as Administrator.
    echo.
)

:: Step 1: Check prerequisites
echo [1/6] Checking prerequisites...

:: Check for curl
where curl >nul 2>&1
if %errorlevel% equ 0 (
    set "DOWNLOADER=curl"
    echo   Found: curl
) else (
    :: Check for PowerShell
    where powershell >nul 2>&1
    if %errorlevel% equ 0 (
        set "DOWNLOADER=powershell"
        echo   Found: PowerShell
    ) else (
        echo ERROR: Neither curl nor PowerShell found!
        echo Please install one of them or download manually from:
        echo https://github.com/%REPO_OWNER%/%REPO_NAME%/releases
        pause
        exit /b 1
    )
)

:: Step 2: Get latest release URL
echo [2/6] Fetching latest release information...

:: Construct download URL (direct to latest release)
set "DOWNLOAD_URL=https://github.com/%REPO_OWNER%/%REPO_NAME%/releases/latest/download/%APP_NAME%.exe"
echo   Download URL: %DOWNLOAD_URL%

:: Step 3: Create installation directory
echo [3/6] Preparing installation directory...

if not defined PORTABLE (
    if not exist "%INSTALL_PATH%" (
        mkdir "%INSTALL_PATH%"
    )
)
echo   Install path: %INSTALL_PATH%

:: Step 4: Download the executable
echo [4/6] Downloading Security Testing Framework...

set "EXE_PATH=%INSTALL_PATH%\%APP_NAME%.exe"

if "%DOWNLOADER%"=="curl" (
    curl -L -o "%EXE_PATH%" "%DOWNLOAD_URL%"
    if !errorlevel! neq 0 (
        echo ERROR: Download failed!
        goto :error
    )
) else (
    :: Use PowerShell to download
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%EXE_PATH%' -UseBasicParsing}"
    if !errorlevel! neq 0 (
        echo ERROR: Download failed!
        goto :error
    )
)

:: Step 5: Verify download
echo [5/6] Verifying download...

if exist "%EXE_PATH%" (
    for %%A in ("%EXE_PATH%") do set "FILE_SIZE=%%~zA"
    set /a "FILE_SIZE_MB=!FILE_SIZE! / 1048576"
    echo   File size: ~!FILE_SIZE_MB! MB
    echo   Download complete!
) else (
    echo ERROR: Download verification failed!
    goto :error
)

:: Step 6: Create shortcuts (unless portable)
if not defined PORTABLE (
    echo [6/6] Creating shortcuts...

    :: Create desktop shortcut using PowerShell
    powershell -Command "& {$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\Security Testing Framework.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.WorkingDirectory = '%INSTALL_PATH%'; $s.Description = 'Professional Security Testing Framework'; $s.Save()}" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   Desktop shortcut created
    )

    :: Create Start Menu entry
    set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Security Testing Framework"
    if not exist "%START_MENU%" mkdir "%START_MENU%"

    powershell -Command "& {$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\Security Testing Framework.lnk'); $s.TargetPath = '%EXE_PATH%'; $s.WorkingDirectory = '%INSTALL_PATH%'; $s.Description = 'Professional Security Testing Framework'; $s.Save()}" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   Start menu entry created
    )

    :: Create uninstaller
    echo @echo off > "%INSTALL_PATH%\uninstall.bat"
    echo echo Uninstalling Security Testing Framework... >> "%INSTALL_PATH%\uninstall.bat"
    echo del "%EXE_PATH%" 2^>nul >> "%INSTALL_PATH%\uninstall.bat"
    echo del "%USERPROFILE%\Desktop\Security Testing Framework.lnk" 2^>nul >> "%INSTALL_PATH%\uninstall.bat"
    echo rmdir /s /q "%START_MENU%" 2^>nul >> "%INSTALL_PATH%\uninstall.bat"
    echo rmdir /s /q "%INSTALL_PATH%" 2^>nul >> "%INSTALL_PATH%\uninstall.bat"
    echo echo Uninstallation complete! >> "%INSTALL_PATH%\uninstall.bat"
    echo pause >> "%INSTALL_PATH%\uninstall.bat"
    echo   Uninstaller created
)

:: Success message
echo.
echo =============================================================================
echo           INSTALLATION COMPLETED SUCCESSFULLY!
echo =============================================================================
echo.
echo Installed to: %EXE_PATH%

if not defined PORTABLE (
    echo Uninstall: Run %INSTALL_PATH%\uninstall.bat
)

echo.
echo To run the framework:
echo   - Double-click the desktop shortcut
echo   - Or run: %EXE_PATH%
echo.

:: Ask to run now
set /p "RUN_NOW=Would you like to run Security Testing Framework now? (Y/N): "
if /i "%RUN_NOW%"=="Y" (
    echo Starting Security Testing Framework...
    start "" "%EXE_PATH%"
)

echo.
pause
exit /b 0

:error
echo.
echo =============================================================================
echo                      INSTALLATION FAILED
echo =============================================================================
echo.
echo Troubleshooting:
echo   1. Check your internet connection
echo   2. Try running as Administrator
echo   3. Check if antivirus is blocking the download
echo   4. Try downloading manually from:
echo      https://github.com/%REPO_OWNER%/%REPO_NAME%/releases
echo.
pause
exit /b 1

:help
echo.
echo Security Testing Framework - Installer
echo.
echo Usage: install.bat [options]
echo.
echo Options:
echo   --portable    Install to current directory (portable mode)
echo   --help        Show this help message
echo.
echo Examples:
echo   install.bat                 Install to AppData with shortcuts
echo   install.bat --portable      Install to current directory
echo.
pause
exit /b 0