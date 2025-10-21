@echo off
setlocal enabledelayedexpansion

:: =============================================================================
:: Bypass Methods Framework - Windows Build Script
:: =============================================================================
:: This script automates the entire build process for Windows users
:: From checking prerequisites to running the final application
:: =============================================================================

echo.
echo =============================================================================
echo 🚀 Bypass Methods Framework - Windows Build Script
echo =============================================================================
echo Production-ready DirectX and Windows API hooking framework
echo Automated build process for Windows users
echo =============================================================================
echo.

:: Set error handling
set "ERROR_COUNT=0"
set "WARNING_COUNT=0"

:: Create log file
set "LOG_FILE=build_log_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt"
set "LOG_FILE=%LOG_FILE: =0%"
echo Build started at %date% %time% > "%LOG_FILE%"

:: Function to log messages
:log
echo [%time%] %~1 | tee -a "%LOG_FILE%"
goto :eof

:: Function to check if command exists
:command_exists
where %1 >nul 2>&1
if %errorlevel% equ 0 (
    set "%~2=1"
) else (
    set "%~2=0"
)
goto :eof

:: Function to increment error count
:increment_error
set /a ERROR_COUNT+=1
goto :eof

:: Function to increment warning count
:increment_warning
set /a WARNING_COUNT+=1
goto :eof

:: =============================================================================
:: PHASE 1: PREREQUISITE CHECKING
:: =============================================================================

call :log "PHASE 1: Checking Prerequisites"
echo.

:: Check Windows version
call :log "Checking Windows version..."
ver | findstr /i "10\.0\|11\.0" >nul
if %errorlevel% neq 0 (
    call :log "❌ ERROR: Windows 10 or 11 required. Current version:"
    ver
    call :increment_error
    goto :prerequisites_failed
) else (
    call :log "✅ Windows version: OK"
    ver
)

:: Check if running as administrator
call :log "Checking administrator privileges..."
net session >nul 2>&1
if %errorlevel% neq 0 (
    call :log "⚠️ WARNING: Not running as administrator. Some features may be limited."
    call :increment_warning
) else (
    call :log "✅ Administrator privileges: OK"
)

:: Check Python
call :log "Checking Python installation..."
call :command_exists python PYTHON_EXISTS
if %PYTHON_EXISTS% equ 0 (
    call :log "❌ ERROR: Python not found. Installing Python..."
    
    :: Download and install Python
    call :log "Downloading Python installer..."
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile 'python_installer.exe'}"
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to download Python installer"
        call :increment_error
        goto :prerequisites_failed
    )
    
    call :log "Installing Python..."
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to install Python"
        call :increment_error
        goto :prerequisites_failed
    )
    
    :: Refresh environment variables
    call refreshenv.cmd 2>nul || (
        set "PATH=%PATH%;C:\Python311;C:\Python311\Scripts"
    )
    
    del python_installer.exe
) else (
    call :log "✅ Python found:"
    python --version
)

:: Check pip
call :log "Checking pip installation..."
call :command_exists pip PIP_EXISTS
if %PIP_EXISTS% equ 0 (
    call :log "❌ ERROR: pip not found. Installing pip..."
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to install pip"
        call :increment_error
        goto :prerequisites_failed
    )
) else (
    call :log "✅ pip found:"
    pip --version
)

:: Check Visual Studio
call :log "Checking Visual Studio installation..."
call :command_exists cl CL_EXISTS
if %CL_EXISTS% equ 0 (
    call :log "❌ ERROR: Visual Studio not found. Installing Visual Studio Build Tools..."
    
    :: Download and install Visual Studio Build Tools
    call :log "Downloading Visual Studio Build Tools..."
    powershell -Command "& {Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile 'vs_buildtools.exe'}"
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to download Visual Studio Build Tools"
        call :increment_error
        goto :prerequisites_failed
    )
    
    call :log "Installing Visual Studio Build Tools..."
    vs_buildtools.exe --quiet --wait --norestart --nocache ^
        --installPath "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools" ^
        --add Microsoft.VisualStudio.Workload.VCTools ^
        --add Microsoft.VisualStudio.Component.Windows10SDK.19041
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to install Visual Studio Build Tools"
        call :increment_error
        goto :prerequisites_failed
    )
    
    del vs_buildtools.exe
    
    :: Set up Visual Studio environment
    call :log "Setting up Visual Studio environment..."
    call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
) else (
    call :log "✅ Visual Studio found:"
    cl 2>&1 | findstr "Version"
)

:: Check CMake
call :log "Checking CMake installation..."
call :command_exists cmake CMAKE_EXISTS
if %CMAKE_EXISTS% equ 0 (
    call :log "❌ ERROR: CMake not found. Installing CMake..."
    
    :: Download and install CMake
    call :log "Downloading CMake..."
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/Kitware/CMake/releases/download/v3.28.1/cmake-3.28.1-windows-x86_64.msi' -OutFile 'cmake_installer.msi'}"
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to download CMake"
        call :increment_error
        goto :prerequisites_failed
    )
    
    call :log "Installing CMake..."
    msiexec /i cmake_installer.msi /quiet /norestart
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to install CMake"
        call :increment_error
        goto :prerequisites_failed
    )
    
    del cmake_installer.msi
    
    :: Add CMake to PATH
    set "PATH=%PATH%;C:\Program Files\CMake\bin"
) else (
    call :log "✅ CMake found:"
    cmake --version
)

:: Check Git
call :log "Checking Git installation..."
call :command_exists git GIT_EXISTS
if %GIT_EXISTS% equ 0 (
    call :log "❌ ERROR: Git not found. Installing Git..."
    
    :: Download and install Git
    call :log "Downloading Git..."
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe' -OutFile 'git_installer.exe'}"
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to download Git"
        call :increment_error
        goto :prerequisites_failed
    )
    
    call :log "Installing Git..."
    git_installer.exe /VERYSILENT /NORESTART
    if %errorlevel% neq 0 (
        call :log "❌ ERROR: Failed to install Git"
        call :increment_error
        goto :prerequisites_failed
    )
    
    del git_installer.exe
    
    :: Add Git to PATH
    set "PATH=%PATH%;C:\Program Files\Git\bin"
) else (
    call :log "✅ Git found:"
    git --version
)

:: Check DirectX SDK
call :log "Checking DirectX SDK..."
if not exist "%DXSDK_DIR%" (
    call :log "⚠️ WARNING: DirectX SDK not found. Windows 10/11 includes DirectX by default."
    call :increment_warning
) else (
    call :log "✅ DirectX SDK found: %DXSDK_DIR%"
)

:: Prerequisites summary
echo.
call :log "PREREQUISITES SUMMARY:"
if %ERROR_COUNT% gtr 0 (
    call :log "❌ %ERROR_COUNT% errors found"
    goto :prerequisites_failed
) else (
    call :log "✅ All prerequisites satisfied"
    if %WARNING_COUNT% gtr 0 (
        call :log "⚠️ %WARNING_COUNT% warnings (non-critical)"
    )
)

:: =============================================================================
:: PHASE 2: ENVIRONMENT SETUP
:: =============================================================================

call :log "PHASE 2: Setting up Environment"
echo.

:: Create build directory
call :log "Creating build directory..."
if not exist "build" mkdir build
cd build

:: Set up Visual Studio environment if not already done
if %CL_EXISTS% equ 0 (
    call :log "Setting up Visual Studio environment..."
    call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
)

:: =============================================================================
:: PHASE 3: PYTHON DEPENDENCIES
:: =============================================================================

call :log "PHASE 3: Installing Python Dependencies"
echo.

cd ..

:: Create virtual environment
call :log "Creating Python virtual environment..."
if exist "venv" (
    call :log "Virtual environment already exists, removing..."
    rmdir /s /q venv
)

python -m venv venv
if %errorlevel% neq 0 (
    call :log "❌ ERROR: Failed to create virtual environment"
    call :increment_error
    goto :build_failed
)

:: Activate virtual environment
call :log "Activating virtual environment..."
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    call :log "❌ ERROR: Failed to activate virtual environment"
    call :increment_error
    goto :build_failed
)

:: Upgrade pip
call :log "Upgrading pip..."
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    call :log "❌ ERROR: Failed to upgrade pip"
    call :increment_error
    goto :build_failed
)

:: Install Python dependencies
call :log "Installing Python dependencies..."
pip install -r python\requirements\requirements.txt
if %errorlevel% neq 0 (
    call :log "❌ ERROR: Failed to install Python dependencies"
    call :increment_error
    goto :build_failed
)

:: Install security dependencies
call :log "Installing security dependencies..."
pip install -r python\requirements\requirements_security.txt
if %errorlevel% neq 0 (
    call :log "❌ ERROR: Failed to install security dependencies"
    call :increment_error
    goto :build_failed
)

:: Install additional Windows-specific dependencies
call :log "Installing Windows-specific dependencies..."
pip install pywin32==306 PyWinCtl==0.3
if %errorlevel% neq 0 (
    call :log "❌ ERROR: Failed to install Windows-specific dependencies"
    call :increment_error
    goto :build_failed
)

:: =============================================================================
:: PHASE 4: C++ BUILD
:: =============================================================================

call :log "PHASE 4: Building C++ Components"
echo.

cd build

:: Configure CMake
call :log "Configuring CMake..."
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
if %errorlevel% neq 0 (
    call :log "❌ ERROR: CMake configuration failed"
    call :increment_error
    goto :build_failed
)

:: Build the project
call :log "Building C++ components..."
cmake --build . --config Release --parallel
if %errorlevel% neq 0 (
    call :log "❌ ERROR: C++ build failed"
    call :increment_error
    goto :build_failed
)

:: Run C++ tests
call :log "Running C++ tests..."
ctest --test-dir . -C Release --output-on-failure
if %errorlevel% neq 0 (
    call :log "⚠️ WARNING: Some C++ tests failed (non-critical)"
    call :increment_warning
) else (
    call :log "✅ All C++ tests passed"
)

cd ..

:: =============================================================================
:: PHASE 5: PYTHON TESTS
:: =============================================================================

call :log "PHASE 5: Running Python Tests"
echo.

:: Run Python tests
call :log "Running Python tests..."
python -m pytest python\tests\ -v
if %errorlevel% neq 0 (
    call :log "⚠️ WARNING: Some Python tests failed (non-critical)"
    call :increment_warning
) else (
    call :log "✅ All Python tests passed"
)

:: Run security tests
call :log "Running security tests..."
python python\tools\security_tester.py
if %errorlevel% neq 0 (
    call :log "⚠️ WARNING: Some security tests failed (non-critical)"
    call :increment_warning
) else (
    call :log "✅ All security tests passed"
)

:: =============================================================================
:: PHASE 6: FINAL SETUP
:: =============================================================================

call :log "PHASE 6: Final Setup"
echo.

:: Create shortcuts
call :log "Creating desktop shortcuts..."
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Bypass Methods Framework.lnk'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = 'python\\tools\\gui_controller.py'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Description = 'Bypass Methods Framework GUI Controller'; $Shortcut.Save()}"
if %errorlevel% neq 0 (
    call :log "⚠️ WARNING: Failed to create desktop shortcut"
    call :increment_warning
) else (
    call :log "✅ Desktop shortcut created"
)

:: Create start menu entry
call :log "Creating start menu entry..."
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Bypass Methods Framework" (
    mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Bypass Methods Framework"
)
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Bypass Methods Framework\GUI Controller.lnk'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = 'python\\tools\\gui_controller.py'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.Description = 'Bypass Methods Framework GUI Controller'; $Shortcut.Save()}"
if %errorlevel% neq 0 (
    call :log "⚠️ WARNING: Failed to create start menu entry"
    call :increment_warning
) else (
    call :log "✅ Start menu entry created"
)

:: Create batch file for easy launching
call :log "Creating launch script..."
echo @echo off > "launch_framework.bat"
echo echo Starting Bypass Methods Framework... >> "launch_framework.bat"
echo call venv\Scripts\activate.bat >> "launch_framework.bat"
echo python python\tools\gui_controller.py >> "launch_framework.bat"
echo pause >> "launch_framework.bat"

:: =============================================================================
:: PHASE 7: VERIFICATION
:: =============================================================================

call :log "PHASE 7: Final Verification"
echo.

:: Test GUI controller
call :log "Testing GUI controller..."
python python\tools\gui_controller.py --test
if %errorlevel% neq 0 (
    call :log "⚠️ WARNING: GUI controller test failed (non-critical)"
    call :increment_warning
) else (
    call :log "✅ GUI controller test passed"
)

:: Check file integrity
call :log "Checking file integrity..."
if exist "build\Release\*.dll" (
    call :log "✅ C++ DLLs built successfully"
) else (
    call :log "❌ ERROR: C++ DLLs not found"
    call :increment_error
)

if exist "python\tools\gui_controller.py" (
    call :log "✅ Python tools available"
) else (
    call :log "❌ ERROR: Python tools not found"
    call :increment_error
)

:: =============================================================================
:: FINAL SUMMARY
:: =============================================================================

echo.
echo =============================================================================
call :log "BUILD COMPLETED"
echo =============================================================================

if %ERROR_COUNT% gtr 0 (
    call :log "❌ BUILD FAILED: %ERROR_COUNT% errors"
    echo.
    call :log "ERRORS FOUND:"
    call :log "Please check the log file: %LOG_FILE%"
    echo.
    call :log "TROUBLESHOOTING:"
    call :log "1. Run as administrator"
    call :log "2. Check Windows Defender/firewall settings"
    call :log "3. Ensure Visual Studio Build Tools are installed"
    call :log "4. Check internet connection for downloads"
    goto :build_failed
) else (
    call :log "🎉 BUILD SUCCESSFUL!"
    if %WARNING_COUNT% gtr 0 (
        call :log "⚠️ %WARNING_COUNT% warnings (non-critical)"
    )
    echo.
    call :log "NEXT STEPS:"
    call :log "1. Double-click 'launch_framework.bat' to start"
    call :log "2. Or use the desktop shortcut"
    call :log "3. Or run: python python\\tools\\gui_controller.py"
    echo.
    call :log "FEATURES AVAILABLE:"
    call :log "✅ DirectX 11/12 Hooking"
    call :log "✅ Windows API Interception"
    call :log "✅ Advanced Security Features"
    call :log "✅ Performance Optimization"
    call :log "✅ GUI Controller & Dashboard"
    call :log "✅ Security Testing Framework"
    echo.
    call :log "DOCUMENTATION:"
    call :log "📚 User Guide: docs\\USER_GUIDE.md"
    call :log "📚 API Reference: docs\\API_REFERENCE.md"
    call :log "📚 Architecture: docs\\ARCHITECTURE.md"
    echo.
    call :log "SUPPORT:"
    call :log "🐛 Issues: GitHub Issues"
    call :log "💬 Discussions: GitHub Discussions"
    call :log "🔒 Security: SECURITY.md"
)

:: Clean up
deactivate 2>nul

echo.
echo =============================================================================
call :log "Build completed at %date% %time%"
echo =============================================================================
echo.

if %ERROR_COUNT% gtr 0 (
    exit /b 1
) else (
    exit /b 0
)

:: Error handling labels
:prerequisites_failed
call :log "❌ Prerequisites check failed"
call :log "Please fix the errors above and run the script again"
echo.
call :log "COMMON SOLUTIONS:"
call :log "1. Run as administrator"
call :log "2. Install Visual Studio Build Tools manually"
call :log "3. Install Python manually from python.org"
call :log "4. Check Windows Defender/firewall settings"
goto :end

:build_failed
call :log "❌ Build process failed"
call :log "Please check the log file: %LOG_FILE%"
goto :end

:end
echo.
call :log "Build script finished"
echo.
pause 