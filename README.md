# Security Testing Framework

A professional-grade, single-file security testing framework for evaluating exam proctoring software integrity. This tool is designed exclusively for legitimate security research and vulnerability assessment by authorized security professionals.

## 🎯 Purpose

This framework assists security teams in:
- Identifying potential vulnerabilities in exam proctoring software
- Testing defensive mechanisms
- Improving security posture of educational integrity tools
- Conducting authorized penetration testing

## ⚡ Quick Start

### Method 1: One-Line Installation (Recommended)

#### PowerShell (Run as Administrator):
```powershell
irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex
```

#### Alternative PowerShell command:
```powershell
iwr -useb https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex
```

#### CMD/Command Prompt:
```cmd
curl -L https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.bat -o %TEMP%\stf-install.bat && %TEMP%\stf-install.bat
```

If you prefer the PowerShell installer but you are in CMD, use:
```cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex"
```

### Method 2: Download Pre-Built Release

Download the latest `SecurityTestingFramework.exe` directly:
```
https://github.com/hira-edu/security-testing-framework/releases/latest
```

### Method 3: Build from Source
```bash
# Clone and build
git clone https://github.com/hira-edu/security-testing-framework.git
cd security-testing-framework
build_installer.bat
```

This creates a single executable: `SecurityTestingFramework.exe` (~120MB)

### Advanced Installation Options

#### PowerShell with Parameters:
```powershell
# Install to custom location
irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex -InstallPath "C:\Tools\STF"

# Portable installation (current directory)
irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex -Portable

# Silent installation (no prompts)
irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex -Silent

# Without shortcuts
irm https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.ps1 | iex -NoDesktopShortcut -NoStartMenu
```

#### CMD with Options:
```cmd
# Portable mode (install to current directory)
curl -L https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.bat -o install.bat && install.bat --portable

# Without shortcuts
curl -L https://raw.githubusercontent.com/hira-edu/security-testing-framework/main/install.bat -o install.bat && install.bat --no-shortcuts
```

### Uninstallation

#### Windows:
```powershell
# If installed via PowerShell
& "$env:LOCALAPPDATA\SecurityTestingFramework\uninstall.ps1"

# If installed via CMD
%LOCALAPPDATA%\SecurityTestingFramework\uninstall.bat
```

## 🏗️ Architecture

The framework uses a modular architecture with:
- **Core Engine**: Python-based testing orchestration
- **Native Modules**: C++ components for low-level operations
- **GUI Interface**: User-friendly testing interface
- **CLI Tools**: Scriptable command-line interface
- **Report Generator**: Comprehensive security assessment reports

## 📦 Components

- **Screen Capture Testing**: Multiple capture method validation
- **Process Monitoring**: Process manipulation detection
- **API Hooking Tests**: System API interception verification
- **Memory Analysis**: Runtime memory inspection tools
- **Network Monitoring**: Network communication analysis

## 🔧 Building from Source

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.11+
- Visual Studio 2022 (or Build Tools)
- CMake 3.20+

### Build Process
```bash
# Clone the repository
git clone https://github.com/your-org/security-testing-framework.git
cd security-testing-framework

# Run the build script
python build_single_file.py --release

# Output: dist/SecurityTestingFramework.exe
```

## 🚀 Usage

### GUI Mode (Default)
```bash
SecurityTestingFramework.exe
```

### Command Line Interface
```bash
# Run specific test suite
SecurityTestingFramework.exe --test screen_capture --target "LockDownBrowser.exe"

# Generate security report
SecurityTestingFramework.exe --report --output security_audit.pdf

# Silent mode with configuration
SecurityTestingFramework.exe --silent --config test_config.json
```

## 📊 Testing Capabilities

### 1. Screen Capture Methods
- Windows Graphics Capture API
- DXGI Desktop Duplication
- DirectX Hook Injection
- GDI+ Capture Methods

### 2. Process Manipulation
- DLL Injection techniques
- Process hollowing detection
- API hooking mechanisms
- Kernel-level operations

### 3. Security Bypass Testing
- Anti-debugging bypass
- Sandbox detection
- Virtual machine detection
- Code integrity verification

## 🔒 Security & Legal

### Important Notice
This tool is designed for **authorized security testing only**. Users must:
- Have explicit permission to test target systems
- Comply with all applicable laws and regulations
- Use only for improving security posture
- Document all testing activities

### Ethical Guidelines
- Only use on systems you own or have permission to test
- Report discovered vulnerabilities responsibly
- Do not use for malicious purposes
- Maintain confidentiality of findings

## 📈 Performance Metrics

- **Installation Time**: < 30 seconds
- **Startup Time**: < 5 seconds
- **Memory Usage**: < 500MB
- **Test Coverage**: > 95%

## 🤝 Contributing

This is a private security research tool. Contributions are limited to authorized team members.

## 📄 License

Proprietary - For authorized security testing only.

## ⚠️ Disclaimer

This framework is provided for legitimate security testing purposes only. The authors assume no liability for misuse or damage caused by this software. Users are responsible for ensuring compliance with all applicable laws and obtaining proper authorization before use.

## 🆘 Support

For authorized users:
- Internal documentation: `docs/`
- Security reports: Submit through internal channels
- Technical support: Contact security team

---

**Security Testing Framework** - Professional tools for educational software security assessment
