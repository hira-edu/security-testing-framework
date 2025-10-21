# Security Testing Framework

For changes and release notes, see: CHANGELOG.md

A professional-grade, single-file security testing framework for evaluating exam proctoring software integrity. This tool is designed exclusively for legitimate security research and vulnerability assessment by authorized security professionals.

## ðŸŽ¯ Purpose

This framework assists security teams in:
- Identifying potential vulnerabilities in exam proctoring software
- Testing defensive mechanisms
- Improving security posture of educational integrity tools
- Conducting authorized penetration testing

## âš¡ Quick Start

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

Notes:
- The installers auto-detect non-writable locations (e.g., `C:\Windows\System32\config\systemprofile`) and fall back to user-writable paths under `%LOCALAPPDATA%`, `%USERPROFILE%`, or `%TEMP%`.
- Batch installer supports `--portable` and `--no-shortcuts`.
- PowerShell installer supports `-Portable`, `-NoDesktopShortcut`, `-NoStartMenu`, and `-Silent`.

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

### New Commands and Shortcuts

- Launch from Start Menu: Security Testing Framework
- Launch from Desktop: Security Testing Framework.lnk (if created)
- Launch from shell (after install): `SecurityTestingFramework` or run the installed `.exe`
- Portable run: extract or install to a folder and run `SecurityTestingFramework.exe`

### Troubleshooting

- If running under restricted/service contexts, the installer will avoid system profile paths and install to a user-writable directory automatically.
- If `irm` is not recognized in CMD, use the provided PowerShell-on-CMD one-liner above.

### Uninstallation

#### Windows:
```powershell
# If installed via PowerShell
& "$env:LOCALAPPDATA\SecurityTestingFramework\uninstall.ps1"

# If installed via CMD
%LOCALAPPDATA%\SecurityTestingFramework\uninstall.bat
```

## ðŸ—ï¸ Architecture

The framework uses a modular architecture with:
- **Core Engine**: Python-based testing orchestration
- **Native Modules**: C++ components for low-level operations
- **GUI Interface**: User-friendly testing interface
- **CLI Tools**: Scriptable command-line interface
- **Report Generator**: Comprehensive security assessment reports

## ðŸ“¦ Components

- **Screen Capture Testing**: Multiple capture method validation
- **Process Monitoring**: Process manipulation detection
- **API Hooking Tests**: System API interception verification
- **Memory Analysis**: Runtime memory inspection tools
- **Network Monitoring**: Network communication analysis

## ðŸ”§ Building from Source

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

## ðŸš€ Usage

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

**Structured CLI examples**
- `SecurityTestingFramework.exe monitor --target "LockDownBrowser.exe" --comprehensive --output results.json`
- `SecurityTestingFramework.exe hooks --action status`
- `SecurityTestingFramework.exe inject --method section-map --target "LockDownBrowser.exe" --dll C:\SecurityTestFramework\AdvancedHookDLL.dll`
- `SecurityTestingFramework.exe hooks --action enable --profile lockdown-bypass --target "SafeExamBrowser.exe" --pid 4242 --service ExamMonitor`
- `SecurityTestingFramework.exe capture --method auto --image captures\latest.png --metadata captures\latest.json`
- `SecurityTestingFramework.exe hooks --action disable --layer all`
- `SecurityTestingFramework.exe profiles --action add --name stealth-monitor --base-command monitor --set target=LockDownBrowser.exe --set stealth=true --set comprehensive=true`
- `SecurityTestingFramework.exe inventory --name browser --sort-by cpu_percent --limit 10 --output snapshots\\browser.json`
- `SecurityTestingFramework.exe inventory --baseline snapshots\baseline.json --sort-by pid --no-windows`
- `SecurityTestingFramework.exe report --from-inventory snapshots\baseline.json --output reports\ld.json`
- `SecurityTestingFramework.exe shell --no-banner`

Use `--process`, `--pid`, `--file`, or `--service` with the `hooks` command to associate telemetry with specific executables, running processes, or services. These flags feed directly into the hook manager status so you can confirm exactly which context is active.

See `docs/CLI_Roadmap.md` for the active roadmap and planned CLI enhancements.

### Interactive Shell

Launch an interactive REPL with:
```bash
SecurityTestingFramework.exe shell
```

Within the shell you can run any CLI verb (`monitor`, `hooks`, `profiles`, etc.) without re-launching the executable. Use `help` to see available commands or `help <command>` for detailed usage. Type `exit` or `quit` to leave the session.
- Use `pick [inventory filters]` to launch an interactive selector backed by the inventory command; the chosen process is reused automatically by `inject`/`report` unless you run `clear selection`.

### Default Profiles

The framework seeds a few reusable CLI presets under `%LOCALAPPDATA%\SecurityTestingFramework\profiles` on first launch. List them with:
```bash
SecurityTestingFramework.exe profiles --action list
```

Included examples:
- `stealth-monitor`: runs stealth monitoring with the lockdown bypass profile.
- `baseline-capture`: captures a baseline screenshot plus metadata outputs.
- `hooks-lockdown`: enables the lockdown hook stack for the default target.
- `report-stealth`: generates a comprehensive report for LockDown Browser.

Customise or extend these with `profiles --action add` and the new settings will persist alongside the defaults.
### Process Inventory

Collect a filtered snapshot of running processes with:
```bash
SecurityTestingFramework.exe inventory --name browser --sort-by cpu_percent --limit 10
```

Supported filters include executable name, PID, Windows session, integrity level, username, and window title substring. Use `--sort-by` (`name`, `pid`, `session_id`, `integrity`, `username`, `cpu_percent`) with `--sort-desc` to control ordering, and `--no-windows` to speed up collections by skipping window enumeration. Provide `--output <path>` to persist results for later analysis or reporting. Use `--baseline <path>` to diff against a saved snapshot; the output includes `added`, `removed`, and `changed` sets. Snapshots also capture handle/thread counts, DirectX module hints, and SetWindowDisplayAffinity states when available.
Use `--from-inventory` with `inject` or `report` to reuse snapshot context without retyping targets.


## ðŸ“Š Testing Capabilities

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

## ðŸ”’ Security & Legal

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

## ðŸ“ˆ Performance Metrics

- **Installation Time**: < 30 seconds
- **Startup Time**: < 5 seconds
- **Memory Usage**: < 500MB
- **Test Coverage**: > 95%

## ðŸ¤ Contributing

This is a private security research tool. Contributions are limited to authorized team members.

## ðŸ“„ License

Proprietary - For authorized security testing only.

## âš ï¸ Disclaimer

This framework is provided for legitimate security testing purposes only. The authors assume no liability for misuse or damage caused by this software. Users are responsible for ensuring compliance with all applicable laws and obtaining proper authorization before use.

## ðŸ†˜ Support

For authorized users:
- Internal documentation: `docs/`
- Security reports: Submit through internal channels
- Technical support: Contact security team

## Tracking & TODO Checklist

- [ ] Phase 0: Baseline CLI inventory.
- [x] Phase 1.1: Parameter schema + profile storage (CLI profiles command with typed presets).
- [x] Phase 2: Process inventory engine & filtering (process inventory CLI with filters, 2025-10-19).
- [ ] Phase 3.1: Enhanced injection command.
- [ ] Phase 3.2: Layer enable/disable/status commands.
- [ ] Phase 3.3: DirectX hook management CLI.
- [ ] Phase 3.4: SetWindowDisplayAffinity monitoring & bypass.
- [ ] Phase 4.1: Structured logging implementation.
- [ ] Phase 4.2: Telemetry aggregation commands.
- [ ] Phase 4.3: Debug switches and diagnostics bundle.
- [ ] Phase 4.4: Error handling standardization.
- [ ] Phase 5.1: Pester coverage.
- [ ] Phase 5.2: Integration harness.
- [ ] Phase 5.3: CLI validation script integration.
- [ ] Phase 6.1: README updates.
- [ ] Phase 6.2: Help system.
- [ ] Phase 6.3: Troubleshooting docs.
- [ ] Phase 6.4: Demo artifacts.

---

**Security Testing Framework** - Professional tools for educational software security assessment

## Pending Tasks
- Build `native/bypass_methods/dll/UndownUnlockDXHook.dll` on Windows via CMake or drop in the prebuilt DLL/PDB (see native/bypass_methods/README.md).
- Update CI workflow to stage that DLL before running `build_single_file.py` so PyInstaller bundles remain functional.
- Smoke-test Windows PowerShell deployment scripts (`deploy_test_environment.ps1`, `HOT_DEPLOY.ps1`, `quick_deploy.ps1`) end-to-end.
- Run PyInstaller build on Windows and verify the frozen EXE captures/injects using the new bypass-methods integrations.
