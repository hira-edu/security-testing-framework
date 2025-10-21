@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: Bypass Methods Framework - One-Click Windows Installer
:: =============================================================================
:: This script automatically detects the best installation method and
:: installs the framework with minimal user interaction
:: =============================================================================

echo.
echo =============================================================================
echo 🚀 Bypass Methods Framework - One-Click Windows Installer
echo =============================================================================
echo Production-ready DirectX and Windows API hooking framework
echo Automated installation for Windows users
echo =============================================================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ WARNING: Not running as administrator
    echo Some features may be limited. For best results, run as administrator.
    echo.
    pause
)

:: Check PowerShell execution policy
powershell -Command "Get-ExecutionPolicy" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ WARNING: PowerShell execution policy may be restricted
    echo Attempting to set execution policy for current user...
    powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
)

:: Check if PowerShell script exists
if exist "scripts\build_windows.ps1" (
    echo ✅ PowerShell build script found
    echo Using PowerShell build method (recommended)
    echo.
    
    :: Run PowerShell script
    powershell -ExecutionPolicy Bypass -File "scripts\build_windows.ps1"
    set "BUILD_RESULT=%errorlevel%"
) else (
    echo ⚠️ PowerShell script not found, using batch method
    echo.
    
    :: Check if batch script exists
    if exist "scripts\build_windows.bat" (
        echo ✅ Batch build script found
        echo Using batch build method
        echo.
        
        :: Run batch script
        call "scripts\build_windows.bat"
        set "BUILD_RESULT=%errorlevel%"
    ) else (
        echo ❌ ERROR: No build scripts found
        echo Please ensure you have downloaded the complete framework
        pause
        exit /b 1
    )
)

:: Check build result
if %BUILD_RESULT% equ 0 (
    echo.
    echo =============================================================================
    echo 🎉 INSTALLATION COMPLETED SUCCESSFULLY!
    echo =============================================================================
    echo.
    echo ✅ The Bypass Methods Framework has been installed successfully!
    echo.
    echo 🚀 NEXT STEPS:
    echo 1. Double-click 'launch_framework.bat' to start the framework
    echo 2. Or use the desktop shortcut: "Bypass Methods Framework"
    echo 3. Or use the start menu entry
    echo.
    echo 📚 DOCUMENTATION:
    echo • User Guide: docs\USER_GUIDE.md
    echo • API Reference: docs\API_REFERENCE.md
    echo • Architecture: docs\ARCHITECTURE.md
    echo.
    echo 🆘 SUPPORT:
    echo • Issues: GitHub Issues
    echo • Discussions: GitHub Discussions
    echo • Security: SECURITY.md
    echo.
    echo =============================================================================
    echo.
    
    :: Ask if user wants to launch the framework
    set /p "LAUNCH=Do you want to launch the framework now? (y/n): "
    if /i "%LAUNCH%"=="y" (
        echo.
        echo 🚀 Launching Bypass Methods Framework...
        if exist "launch_framework.bat" (
            start "" "launch_framework.bat"
        ) else (
            echo ⚠️ Launch script not found, trying alternative method...
            if exist "venv\Scripts\activate.bat" (
                start "" cmd /k "call venv\Scripts\activate.bat && python python\tools\gui_controller.py"
            ) else (
                echo ❌ ERROR: Could not launch framework
                echo Please run manually: python python\tools\gui_controller.py
            )
        )
    )
    
    echo.
    echo Installation completed successfully!
    echo Thank you for using Bypass Methods Framework!
    echo.
    pause
    
) else (
    echo.
    echo =============================================================================
    echo ❌ INSTALLATION FAILED
    echo =============================================================================
    echo.
    echo The installation encountered errors. Please check the log files:
    echo • build_log_*.txt - Detailed build log
    echo.
    echo 🔧 TROUBLESHOOTING:
    echo 1. Run as administrator
    echo 2. Check Windows Defender/firewall settings
    echo 3. Ensure you have internet connection
    echo 4. Check available disk space (requires ~2GB)
    echo 5. Try running the build script manually
    echo.
    echo 📞 SUPPORT:
    echo • Check the log files for specific error messages
    echo • Create an issue on GitHub with the log file
    echo • Check the troubleshooting guide in docs\TROUBLESHOOTING.md
    echo.
    echo =============================================================================
    echo.
    pause
    exit /b 1
) 