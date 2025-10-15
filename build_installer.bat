@echo off
echo.
echo =====================================================================
echo Security Testing Framework - Single File Builder
echo =====================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Install required packages
echo Installing required packages...
pip install pyinstaller pillow psutil cryptography requests --upgrade

:: Clean previous builds
echo Cleaning previous builds...
rd /s /q build 2>nul
rd /s /q dist 2>nul

:: Build with PyInstaller
echo Building single executable...
python build_single_file.py --release

:: Check if build succeeded
if exist "dist\SecurityTestingFramework.exe" (
    echo.
    echo =====================================================================
    echo BUILD SUCCESSFUL!
    echo =====================================================================
    echo.
    echo Output: dist\SecurityTestingFramework.exe
    echo Size: ~120MB
    echo.
    echo You can now run: dist\SecurityTestingFramework.exe
    echo.
) else (
    echo.
    echo =====================================================================
    echo BUILD FAILED!
    echo =====================================================================
    echo Please check the error messages above.
)

pause
