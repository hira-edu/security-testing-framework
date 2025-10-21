# Windows Installation Guide

## 🚀 Quick Start (Recommended)

### One-Click Installation
For the easiest installation experience, simply:

1. **Download the framework** from GitHub
2. **Extract the ZIP file** to a folder (e.g., `C:\bypass-methods`)
3. **Double-click** `scripts\install_windows.bat`
4. **Follow the prompts** and wait for installation to complete
5. **Launch the framework** when prompted

That's it! The installer will handle everything automatically.

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10 (version 1903) or Windows 11
- **Architecture**: x64 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Graphics**: DirectX 11 or 12 compatible graphics card
- **Internet**: Required for downloading dependencies

### Recommended Requirements
- **OS**: Windows 11 (latest version)
- **RAM**: 16GB or more
- **Storage**: 5GB free space (SSD recommended)
- **Graphics**: DirectX 12 compatible graphics card
- **Administrator privileges**: For full functionality

## 🔧 Installation Methods

### Method 1: One-Click Installer (Easiest)
```bash
# Simply double-click this file:
scripts\install_windows.bat
```

**Features:**
- ✅ Automatic prerequisite detection and installation
- ✅ Automatic build process
- ✅ Desktop shortcuts and start menu entries
- ✅ Comprehensive error handling and logging
- ✅ User-friendly interface

### Method 2: PowerShell Script (Advanced)
```powershell
# Run as administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\build_windows.ps1

# Or with options:
.\scripts\build_windows.ps1 -SkipTests -Verbose
```

**Options:**
- `-SkipPrerequisites`: Skip prerequisite checking
- `-SkipTests`: Skip running tests
- `-Verbose`: Enable verbose output
- `-LogFile`: Specify custom log file

### Method 3: Batch Script (Legacy)
```cmd
# Run as administrator
scripts\build_windows.bat
```

### Method 4: Manual Installation (Expert)
```bash
# 1. Install prerequisites manually
# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

# 3. Install Python dependencies
pip install -r python\requirements\requirements.txt
pip install -r python\requirements\requirements_security.txt
pip install pywin32==306 PyWinCtl==0.3

# 4. Build C++ components
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release

# 5. Run tests
ctest --test-dir . -C Release
python -m pytest python\tests\
```

## 📦 Prerequisites Installation

The installer will automatically install these prerequisites, but you can also install them manually:

### Python 3.11+
```bash
# Download from python.org or use installer
# Ensure "Add Python to PATH" is checked
```

### Visual Studio Build Tools 2022
```bash
# Download from Microsoft or use installer
# Required components:
# - MSVC v143 - VS 2022 C++ x64/x86 build tools
# - Windows 10/11 SDK
```

### CMake 3.16+
```bash
# Download from cmake.org or use installer
# Add to PATH during installation
```

### Git
```bash
# Download from git-scm.com or use installer
# Add to PATH during installation
```

## 🚀 Running the Framework

### After Installation
1. **Desktop Shortcut**: Double-click "Bypass Methods Framework"
2. **Start Menu**: Search for "Bypass Methods Framework"
3. **Launch Script**: Double-click `launch_framework.bat`
4. **Manual**: `python python\tools\gui_controller.py`

### Command Line Options
```bash
# Basic launch
python python\tools\gui_controller.py

# With options
python python\tools\gui_controller.py --config custom_config.json
python python\tools\gui_controller.py --debug
python python\tools\gui_controller.py --test
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "Python not found" Error
**Solution:**
```bash
# Install Python manually
# Download from python.org
# Ensure "Add Python to PATH" is checked
# Restart command prompt after installation
```

#### 2. "Visual Studio not found" Error
**Solution:**
```bash
# Install Visual Studio Build Tools
# Download from Microsoft
# Install C++ build tools and Windows SDK
```

#### 3. "CMake not found" Error
**Solution:**
```bash
# Install CMake manually
# Download from cmake.org
# Add to PATH during installation
```

#### 4. "Permission denied" Error
**Solution:**
```bash
# Run as administrator
# Right-click installer → "Run as administrator"
```

#### 5. "Windows Defender blocking" Error
**Solution:**
```bash
# Add exception to Windows Defender
# Settings → Update & Security → Windows Security → Virus & threat protection
# Add folder to exclusions
```

#### 6. "Build failed" Error
**Solution:**
```bash
# Check log files: build_log_*.txt
# Ensure all prerequisites are installed
# Try running as administrator
# Check available disk space
```

### Advanced Troubleshooting

#### Check Installation Status
```bash
# Check Python
python --version
pip --version

# Check Visual Studio
cl 2>&1 | findstr "Version"

# Check CMake
cmake --version

# Check Git
git --version
```

#### Verify Framework Installation
```bash
# Check virtual environment
venv\Scripts\activate.bat
python --version

# Check Python packages
pip list

# Check C++ components
dir build\Release\*.dll

# Run tests
python -m pytest python\tests\ -v
```

#### Clean Installation
```bash
# Remove existing installation
rmdir /s /q venv
rmdir /s /q build
del launch_framework.bat
del build_log_*.txt

# Reinstall
scripts\install_windows.bat
```

## 📊 Installation Verification

### Success Indicators
- ✅ Python virtual environment created
- ✅ All Python dependencies installed
- ✅ C++ components built successfully
- ✅ Tests passing
- ✅ Desktop shortcut created
- ✅ Start menu entry created
- ✅ Launch script created

### Log Files
- `build_log_YYYYMMDD_HHMMSS.txt`: Detailed build log
- `CMakeCache.txt`: CMake configuration cache
- `CMakeFiles/`: CMake build files

## 🆘 Getting Help

### Documentation
- **User Guide**: `docs\USER_GUIDE.md`
- **API Reference**: `docs\API_REFERENCE.md`
- **Architecture**: `docs\ARCHITECTURE.md`
- **Troubleshooting**: `docs\TROUBLESHOOTING.md`

### Support Channels
- **GitHub Issues**: Report bugs and problems
- **GitHub Discussions**: Ask questions and get help
- **Security Issues**: Follow SECURITY.md guidelines

### Common Commands
```bash
# Check framework status
python python\tools\gui_controller.py --status

# Run security tests
python python\tools\security_tester.py

# Run performance tests
python python\tools\performance_tester.py

# Update framework
git pull origin main
scripts\install_windows.bat
```

## 🎯 Next Steps

After successful installation:

1. **Launch the GUI Controller** to explore the framework
2. **Read the User Guide** for detailed usage instructions
3. **Check the API Reference** for development information
4. **Run the Security Tests** to verify functionality
5. **Explore the Examples** in the `python\examples\` directory

## 🔒 Security Notes

- The framework includes advanced security features
- Some antivirus software may flag components (false positive)
- Add the framework directory to antivirus exclusions if needed
- Run security tests to verify integrity
- Follow security best practices in production use

---

**🎉 Congratulations! You've successfully installed the Bypass Methods Framework on Windows!**

For questions or issues, please refer to the documentation or create a GitHub issue. 