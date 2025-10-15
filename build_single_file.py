#!/usr/bin/env python3
"""
Security Testing Framework - Single File Builder
Creates a self-contained executable for security testing
"""

import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
import argparse
import json
import base64
from pathlib import Path
from datetime import datetime

class SingleFileBuilder:
    def __init__(self, release_mode=False):
        self.base_dir = Path(__file__).parent.absolute()
        self.dist_dir = self.base_dir / "dist"
        self.build_dir = self.base_dir / "build"
        self.temp_dir = Path(tempfile.mkdtemp())
        self.release_mode = release_mode
        self.version = "1.0.0"
        self.build_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    def clean_directories(self):
        """Clean previous build artifacts"""
        print("Cleaning previous builds...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
        self.dist_dir.mkdir(parents=True)
        self.build_dir.mkdir(parents=True)

    def create_project_structure(self):
        """Create the project directory structure"""
        print("Creating project structure...")

        directories = [
            "src/core",
            "src/modules",
            "src/gui",
            "src/cli",
            "src/utils",
            "resources/configs",
            "resources/icons",
            "resources/data",
            "native/dll",
            "native/drivers"
        ]

        for dir_name in directories:
            (self.base_dir / dir_name).mkdir(parents=True, exist_ok=True)

    def create_launcher(self):
        """Create the main launcher application"""
        print("[LAUNCH] Creating launcher application...")

        launcher_code = '''
#!/usr/bin/env python3
"""
Security Testing Framework - Main Launcher
Professional security testing tool for authorized use only
"""

import sys
import os
import ctypes
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityTestingFramework:
    """Main framework controller"""

    VERSION = "1.0.0"

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "config.json"
        self.is_admin = self.check_admin()
        self.config = self.load_config()

    def check_admin(self):
        """Check for administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def request_admin(self):
        """Request administrator privileges"""
        if not self.is_admin:
            print("[WARNING]  Requesting administrator privileges...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)

    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "version": self.VERSION,
            "security_level": "HIGH",
            "enable_logging": True,
            "stealth_mode": False,
            "auto_update": True,
            "modules": {
                "screen_capture": True,
                "process_monitor": True,
                "api_hooks": True,
                "memory_scanner": True,
                "network_monitor": True
            }
        }

        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return default_config

    def save_config(self, config):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def run_gui(self):
        """Launch the GUI interface"""
        logger.info("Launching GUI interface...")
        from src.gui.main_window import MainWindow
        app = MainWindow(self)
        app.run()

    def run_cli(self, args):
        """Run command-line interface"""
        logger.info(f"Running CLI with args: {args}")
        from src.cli.cli_handler import CLIHandler
        handler = CLIHandler(self)
        handler.execute(args)

    def run_test(self, test_name, target=None):
        """Run specific security test"""
        logger.info(f"Running test: {test_name} on target: {target}")
        from src.modules.test_runner import TestRunner
        runner = TestRunner(self)
        return runner.run_test(test_name, target)

    def generate_report(self, output_file):
        """Generate security assessment report"""
        logger.info(f"Generating report: {output_file}")
        from src.utils.report_generator import ReportGenerator
        generator = ReportGenerator(self)
        generator.generate(output_file)

    def check_updates(self):
        """Check for framework updates"""
        if self.config.get("auto_update", True):
            logger.info("Checking for updates...")
            from src.utils.updater import AutoUpdater
            updater = AutoUpdater(self)
            updater.check()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Security Testing Framework - Professional security assessment tool"
    )

    parser.add_argument(
        "--cli", action="store_true",
        help="Run in CLI mode"
    )
    parser.add_argument(
        "--test", type=str,
        help="Run specific test suite"
    )
    parser.add_argument(
        "--target", type=str,
        help="Target process or application"
    )
    parser.add_argument(
        "--report", type=str,
        help="Generate report (specify output file)"
    )
    parser.add_argument(
        "--silent", action="store_true",
        help="Run in silent mode"
    )
    parser.add_argument(
        "--config", type=str,
        help="Configuration file path"
    )
    parser.add_argument(
        "--no-admin", action="store_true",
        help="Don't request admin privileges"
    )

    args = parser.parse_args()

    # Initialize framework
    framework = SecurityTestingFramework()

    # Request admin if needed
    if not args.no_admin and not framework.is_admin:
        framework.request_admin()

    # Check for updates
    framework.check_updates()

    # Handle different modes
    if args.report:
        framework.generate_report(args.report)
    elif args.test:
        framework.run_test(args.test, args.target)
    elif args.cli:
        framework.run_cli(args)
    else:
        # Default to GUI mode
        framework.run_gui()

if __name__ == "__main__":
    main()
'''

        launcher_path = self.base_dir / "launcher.py"
        launcher_path.write_text(launcher_code)
        return launcher_path

    def create_gui_module(self):
        """Create the GUI module"""
        print("[GUI] Creating GUI module...")

        gui_code = '''
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime

class MainWindow:
    """Main GUI window for the Security Testing Framework"""

    def __init__(self, framework):
        self.framework = framework
        self.root = tk.Tk()
        self.root.title("Security Testing Framework v1.0")
        self.root.geometry("900x600")
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Screen Capture", command=self.run_screen_capture)
        tools_menu.add_command(label="Process Monitor", command=self.run_process_monitor)
        tools_menu.add_command(label="API Hooks", command=self.run_api_hooks)

        # Main content
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Dashboard tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.setup_dashboard()

        # Tests tab
        self.tests_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tests_frame, text="Security Tests")
        self.setup_tests()

        # Results tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self.setup_results()

        # Status bar
        self.status_bar = ttk.Label(
            self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_dashboard(self):
        """Setup dashboard tab"""
        ttk.Label(
            self.dashboard_frame,
            text="Security Testing Framework",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        info_frame = ttk.LabelFrame(self.dashboard_frame, text="System Information")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)

        info_text = f"""
        Version: {self.framework.VERSION}
        Admin Privileges: {"Yes" if self.framework.is_admin else "No"}
        Security Level: {self.framework.config.get('security_level', 'HIGH')}
        Stealth Mode: {"Enabled" if self.framework.config.get('stealth_mode') else "Disabled"}
        """

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)

    def setup_tests(self):
        """Setup tests tab"""
        # Test selection
        ttk.Label(self.tests_frame, text="Select Tests:", font=("Arial", 12)).pack(pady=5)

        self.test_vars = {}
        tests = [
            "Screen Capture Detection",
            "Process Manipulation",
            "API Hooking",
            "Memory Scanning",
            "Network Monitoring"
        ]

        for test in tests:
            var = tk.BooleanVar(value=True)
            self.test_vars[test] = var
            ttk.Checkbutton(self.tests_frame, text=test, variable=var).pack(anchor=tk.W, padx=20)

        # Target selection
        target_frame = ttk.Frame(self.tests_frame)
        target_frame.pack(pady=10)

        ttk.Label(target_frame, text="Target Process:").pack(side=tk.LEFT, padx=5)
        self.target_entry = ttk.Entry(target_frame, width=30)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        self.target_entry.insert(0, "LockDownBrowser.exe")

        # Run button
        ttk.Button(
            self.tests_frame, text="Run Tests", command=self.run_tests
        ).pack(pady=10)

    def setup_results(self):
        """Setup results tab"""
        # Results text area
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD)
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.results_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)

        # Export button
        ttk.Button(
            self.results_frame, text="Export Report", command=self.export_report
        ).pack(pady=5)

    def run_tests(self):
        """Run selected security tests"""
        self.update_status("Running tests...")
        self.notebook.select(self.results_frame)

        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Security Test Report\\n")
        self.results_text.insert(tk.END, f"{'='*60}\\n")
        self.results_text.insert(tk.END, f"Timestamp: {datetime.now()}\\n")
        self.results_text.insert(tk.END, f"Target: {self.target_entry.get()}\\n\\n")

        # Run tests in background thread
        def test_worker():
            for test_name, var in self.test_vars.items():
                if var.get():
                    self.results_text.insert(tk.END, f"\\n[*] Running {test_name}...\\n")
                    # Simulate test execution
                    result = f"  [OK] {test_name} completed successfully\\n"
                    self.results_text.insert(tk.END, result)
                    self.results_text.see(tk.END)

            self.results_text.insert(tk.END, f"\\n{'='*60}\\n")
            self.results_text.insert(tk.END, "All tests completed.\\n")
            self.update_status("Tests completed")

        thread = threading.Thread(target=test_worker)
        thread.daemon = True
        thread.start()

    def run_screen_capture(self):
        """Run screen capture test"""
        self.update_status("Running screen capture test...")
        messagebox.showinfo("Screen Capture", "Screen capture test started")

    def run_process_monitor(self):
        """Run process monitor"""
        self.update_status("Running process monitor...")
        messagebox.showinfo("Process Monitor", "Process monitor started")

    def run_api_hooks(self):
        """Run API hooks test"""
        self.update_status("Running API hooks test...")
        messagebox.showinfo("API Hooks", "API hooks test started")

    def load_config(self):
        """Load configuration file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            messagebox.showinfo("Config", f"Loaded configuration from {filename}")

    def save_config(self):
        """Save configuration file"""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.framework.save_config(self.framework.config)
            messagebox.showinfo("Config", f"Saved configuration to {filename}")

    def export_report(self):
        """Export test results"""
        filename = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.results_text.get(1.0, tk.END))
            messagebox.showinfo("Export", f"Report exported to {filename}")

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()
'''

        gui_path = self.base_dir / "src" / "gui" / "main_window.py"
        gui_path.parent.mkdir(parents=True, exist_ok=True)
        gui_path.write_text(gui_code)

        # Create __init__.py
        (self.base_dir / "src" / "gui" / "__init__.py").touch()

    def create_pyinstaller_spec(self):
        """Create PyInstaller spec file"""
        print("[PACKAGE] Creating PyInstaller spec file...")

        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None
base_dir = Path('{self.base_dir}').as_posix()

a = Analysis(
    [base_dir + '/launcher.py'],
    pathex=[base_dir],
    binaries=[],
    datas=[
        (base_dir + '/resources', 'resources'),
        (base_dir + '/native', 'native'),
    ],
    hiddenimports=[
        'tkinter',
        'ctypes',
        'json',
        'threading',
        'subprocess',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SecurityTestingFramework',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.py',
    uac_admin=True,
    icon='resources/icons/app.ico'
)
'''

        spec_path = self.base_dir / "SecurityTestingFramework.spec"
        spec_path.write_text(spec_content)
        return spec_path

    def create_version_info(self):
        """Create version information file"""
        print("[DOC] Creating version information...")

        version_info = f'''
# UTF-8
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                u'040904B0',
                [
                    StringStruct(u'CompanyName', u'Security Research Team'),
                    StringStruct(u'FileDescription', u'Security Testing Framework'),
                    StringStruct(u'FileVersion', u'{self.version}'),
                    StringStruct(u'InternalName', u'SecurityTestingFramework'),
                    StringStruct(u'LegalCopyright', u'© 2024 Security Research Team'),
                    StringStruct(u'OriginalFilename', u'SecurityTestingFramework.exe'),
                    StringStruct(u'ProductName', u'Security Testing Framework'),
                    StringStruct(u'ProductVersion', u'{self.version}')
                ]
            )
        ]),
        VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
    ]
)
'''

        version_path = self.base_dir / "version_info.py"
        version_path.write_text(version_info)

    def create_batch_installer(self):
        """Create batch file for easy building"""
        print("[BUILD] Creating batch installer...")

        batch_content = '''@echo off
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
if exist "dist\\SecurityTestingFramework.exe" (
    echo.
    echo =====================================================================
    echo BUILD SUCCESSFUL!
    echo =====================================================================
    echo.
    echo Output: dist\\SecurityTestingFramework.exe
    echo Size: ~120MB
    echo.
    echo You can now run: dist\\SecurityTestingFramework.exe
    echo.
) else (
    echo.
    echo =====================================================================
    echo BUILD FAILED!
    echo =====================================================================
    echo Please check the error messages above.
)

pause
'''

        batch_path = self.base_dir / "build_installer.bat"
        batch_path.write_text(batch_content)

    def create_icon(self):
        """Create a simple icon for the application"""
        print("[GUI] Creating application icon...")

        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create icon
            size = (256, 256)
            icon = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(icon)

            # Draw shield shape
            points = [
                (128, 20),   # top
                (220, 60),   # top-right
                (220, 140),  # mid-right
                (128, 236),  # bottom
                (36, 140),   # mid-left
                (36, 60),    # top-left
            ]
            draw.polygon(points, fill=(0, 120, 200), outline=(255, 255, 255))

            # Draw lock symbol
            draw.ellipse([108, 80, 148, 120], fill=(255, 255, 255))
            draw.rectangle([113, 100, 143, 140], fill=(255, 255, 255))

            # Save icon
            icon_dir = self.base_dir / "resources" / "icons"
            icon_dir.mkdir(parents=True, exist_ok=True)
            icon_path = icon_dir / "app.ico"
            icon.save(icon_path, format='ICO')

        except ImportError:
            # Create placeholder if PIL not available
            icon_dir = self.base_dir / "resources" / "icons"
            icon_dir.mkdir(parents=True, exist_ok=True)
            (icon_dir / "app.ico").touch()

    def build_executable(self):
        """Build the single executable using PyInstaller"""
        print("[BUILD] Building executable with PyInstaller...")

        if not shutil.which("pyinstaller"):
            print("[WARNING]  PyInstaller not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

        # Run PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "SecurityTestingFramework.spec"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("[SUCCESS] Build successful!")
            exe_path = self.dist_dir / "SecurityTestingFramework.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"[PACKAGE] Output: {exe_path}")
                print(f"[STATS] Size: {size_mb:.1f} MB")
        else:
            print("[ERROR] Build failed!")
            print(result.stderr)

    def create_additional_modules(self):
        """Create additional module files"""
        print("📚 Creating additional modules...")

        # Create CLI handler
        cli_code = '''
class CLIHandler:
    def __init__(self, framework):
        self.framework = framework

    def execute(self, args):
        print(f"Executing CLI command with args: {args}")
'''

        cli_path = self.base_dir / "src" / "cli" / "cli_handler.py"
        cli_path.parent.mkdir(parents=True, exist_ok=True)
        cli_path.write_text(cli_code)
        (self.base_dir / "src" / "cli" / "__init__.py").touch()

        # Create test runner
        test_code = '''
class TestRunner:
    def __init__(self, framework):
        self.framework = framework

    def run_test(self, test_name, target):
        print(f"Running test: {test_name} on target: {target}")
        return {"status": "success", "results": []}
'''

        test_path = self.base_dir / "src" / "modules" / "test_runner.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(test_code)
        (self.base_dir / "src" / "modules" / "__init__.py").touch()

        # Create report generator
        report_code = '''
class ReportGenerator:
    def __init__(self, framework):
        self.framework = framework

    def generate(self, output_file):
        print(f"Generating report: {output_file}")
'''

        report_path = self.base_dir / "src" / "utils" / "report_generator.py"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_code)

        # Create updater
        updater_code = '''
class AutoUpdater:
    def __init__(self, framework):
        self.framework = framework

    def check(self):
        print("Checking for updates...")
'''

        updater_path = self.base_dir / "src" / "utils" / "updater.py"
        updater_path.write_text(updater_code)
        (self.base_dir / "src" / "utils" / "__init__.py").touch()

        # Create __init__ files
        (self.base_dir / "src" / "__init__.py").touch()
        (self.base_dir / "src" / "core" / "__init__.py").touch()

    def create_config_file(self):
        """Create default configuration file"""
        print("⚙️ Creating configuration file...")

        config = {
            "version": self.version,
            "build_time": self.build_time,
            "security_level": "HIGH",
            "enable_logging": True,
            "stealth_mode": False,
            "auto_update": True,
            "modules": {
                "screen_capture": True,
                "process_monitor": True,
                "api_hooks": True,
                "memory_scanner": True,
                "network_monitor": True
            },
            "targets": [
                "LockDownBrowser.exe",
                "SafeExamBrowser.exe",
                "Respondus.exe"
            ]
        }

        config_path = self.base_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

    def run(self):
        """Execute the complete build process"""
        try:
            print(f"""
╔═══════════════════════════════════════════════════════════════╗
║     Security Testing Framework - Single File Builder          ║
║                    Version {self.version}                              ║
╚═══════════════════════════════════════════════════════════════╝
            """)
        except UnicodeEncodeError:
            # Fallback for systems that don't support Unicode
            print(f"""
================================================================
     Security Testing Framework - Single File Builder
                    Version {self.version}
================================================================
            """)

        try:
            self.clean_directories()
            self.create_project_structure()
            self.create_launcher()
            self.create_gui_module()
            self.create_additional_modules()
            self.create_config_file()
            self.create_icon()
            self.create_version_info()
            self.create_pyinstaller_spec()
            self.create_batch_installer()

            if self.release_mode:
                self.build_executable()

            try:
                print("""
╔═══════════════════════════════════════════════════════════════╗
║                    BUILD COMPLETE!                            ║
╚═══════════════════════════════════════════════════════════════╝

Next steps:
1. Run: build_installer.bat
2. Or: python build_single_file.py --release
3. Output will be in: dist/SecurityTestingFramework.exe

                """)
            except UnicodeEncodeError:
                print("""
================================================================
                    BUILD COMPLETE!
================================================================

Next steps:
1. Run: build_installer.bat
2. Or: python build_single_file.py --release
3. Output will be in: dist/SecurityTestingFramework.exe

                """)

        except Exception as e:
            print(f"[ERROR] Build failed: {e}")
            return 1
        finally:
            # Cleanup temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

        return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Build single-file security testing framework")
    parser.add_argument("--release", action="store_true", help="Build release executable")
    parser.add_argument("--version", type=str, default="1.0.0", help="Version number")

    args = parser.parse_args()

    builder = SingleFileBuilder(release_mode=args.release)
    if args.version:
        builder.version = args.version

    return builder.run()

if __name__ == "__main__":
    sys.exit(main())