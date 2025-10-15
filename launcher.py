
#!/usr/bin/env python3
"""
Security Testing Framework - Main Launcher v3.0
Comprehensive Vulnerability Testing Platform
"""

import sys
import os
import ctypes
import json
import logging
import argparse
import threading
import time
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Try to import advanced modules
try:
    from core.stealth_engine import StealthEngine, StealthConfig, StealthLevel
    from core.advanced_config import AdvancedConfiguration, ConfigPresets
    from modules.comprehensive_test_runner import ComprehensiveTestRunner
    from modules.input_monitor import InputMonitor
    from modules.system_monitor import ComprehensiveMonitor
    from modules.memory_scanner import MemoryScanner
    ADVANCED_FEATURES = True
    FULL_MONITORING = True
except ImportError as e:
    ADVANCED_FEATURES = False
    FULL_MONITORING = False
    print(f"[WARNING] Some features not available: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityTestingFramework:
    """Comprehensive vulnerability testing framework with full monitoring"""

    VERSION = "3.0.0"

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = self._determine_data_dir()
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Last resort to base_dir if data_dir cannot be created
            self.data_dir = self.base_dir

        self.config_file = self.data_dir / "config.json"
        self.is_admin = self.check_admin()
        self.config = self.load_config()
        self.advanced_config = None
        self.stealth_engine = None
        self.test_runner = None

        # Monitoring components
        self.input_monitor = None
        self.system_monitor = None
        self.memory_scanner = None
        self.monitoring_active = False
        self.monitoring_threads = []

        # Initialize advanced features if available
        if ADVANCED_FEATURES:
            self._init_advanced_features()

        # Initialize monitoring if available
        if FULL_MONITORING:
            self._init_monitoring_components()

    def _init_advanced_features(self):
        """Initialize advanced testing features"""
        try:
            # Load or create advanced configuration (store under data_dir)
            adv_config_file = self.data_dir / "advanced_config.json"
            if adv_config_file.exists():
                self.advanced_config = AdvancedConfiguration.from_file(str(adv_config_file))
            else:
                # Use default stealth configuration
                self.advanced_config = ConfigPresets.full_stealth()
                self.advanced_config.save(str(adv_config_file))

            # Initialize stealth engine
            if self.advanced_config.anti_detection.enabled:
                stealth_config = StealthConfig(
                    stealth_level=StealthLevel.HIGH,
                    hide_process=True,
                    encrypt_memory=True,
                    obfuscate_api_calls=True,
                    randomize_behavior=True,
                    detect_sandbox=True,
                    detect_vm=True,
                    detect_debugger=True
                )
                self.stealth_engine = StealthEngine(stealth_config)
                logger.info("Stealth engine initialized")

        except Exception as e:
            logger.error(f"Failed to initialize advanced features: {e}")
            self.advanced_config = None
            self.stealth_engine = None

    def _init_monitoring_components(self):
        """Initialize comprehensive monitoring components"""
        try:
            logger.info("Initializing comprehensive monitoring components...")

            # Initialize input monitor
            self.input_monitor = InputMonitor()
            logger.info("Input monitor initialized")

            # Initialize system monitor
            self.system_monitor = ComprehensiveMonitor()

            # Configure system monitoring paths
            monitor_config = {
                'filesystem_paths': [
                    os.environ.get('TEMP', 'C:\\Windows\\Temp'),
                    os.environ.get('APPDATA', ''),
                    os.environ.get('USERPROFILE', '') + '\\Downloads'
                ],
                'registry_keys': [
                    'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                    'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                    'HKEY_CURRENT_USER\\Software\\Classes'
                ]
            }
            self.system_monitor.configure_monitoring(monitor_config)
            logger.info("System monitor initialized")

            # Initialize memory scanner
            self.memory_scanner = MemoryScanner()
            logger.info("Memory scanner initialized")

        except Exception as e:
            logger.error(f"Failed to initialize monitoring components: {e}")

    def start_full_monitoring(self, target_process: str = None):
        """Start comprehensive monitoring of all system activities"""
        if not FULL_MONITORING:
            logger.error("Full monitoring capabilities not available")
            return False

        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return False

        logger.info("STARTING FULL COMPREHENSIVE MONITORING")
        logger.info("="*60)

        # Activate maximum stealth
        if self.stealth_engine:
            logger.info("Activating maximum stealth mode...")
            self.stealth_engine.config.stealth_level = StealthLevel.MAXIMUM
            self.stealth_engine.activate()

        # Start input monitoring
        if self.input_monitor:
            def input_callback(event):
                if event.process_name == target_process or not target_process:
                    logger.debug(f"Input: {event.event_type}/{event.action} in {event.process_name}")

            self.input_monitor.start_monitoring(input_callback)
            logger.info("Input monitoring active")

        # Start system monitoring
        if self.system_monitor:
            self.system_monitor.start_all_monitoring()
            logger.info("System monitoring active")

        # Start memory scanning for target process
        if self.memory_scanner and target_process:
            def memory_scan_thread():
                while self.monitoring_active:
                    try:
                        # Find target process
                        import psutil
                        for proc in psutil.process_iter(['name', 'pid']):
                            if proc.info['name'] == target_process:
                                pid = proc.info['pid']
                                logger.debug(f"Scanning memory of {target_process} (PID: {pid})")

                                h_process = self.memory_scanner.open_process(pid)
                                if h_process:
                                    # Scan for credentials
                                    creds = self.memory_scanner.find_credentials(h_process)
                                    if any(creds.values()):
                                        logger.info(f"Found potential credentials in {target_process}")

                                    ctypes.windll.kernel32.CloseHandle(h_process)
                                break
                    except Exception as e:
                        logger.error(f"Memory scan error: {e}")

                    time.sleep(5)

            scan_thread = threading.Thread(target=memory_scan_thread)
            scan_thread.daemon = True
            scan_thread.start()
            self.monitoring_threads.append(scan_thread)
            logger.info("Memory scanning active")

        self.monitoring_active = True
        logger.info("Full monitoring activated successfully")
        return True

    def stop_monitoring(self):
        """Stop all monitoring"""
        if not self.monitoring_active:
            return

        logger.info("Stopping all monitoring...")

        self.monitoring_active = False

        if self.input_monitor:
            self.input_monitor.stop_monitoring()

        if self.system_monitor:
            self.system_monitor.stop_all_monitoring()

        # Wait for threads to finish
        for thread in self.monitoring_threads:
            thread.join(timeout=2)

        logger.info("All monitoring stopped")

    def export_monitoring_data(self, output_dir: str = None):
        """Export all captured monitoring data"""
        if not output_dir:
            output_dir = self.data_dir / "monitoring_data" / datetime.now().strftime("%Y%m%d_%H%M%S")

        os.makedirs(output_dir, exist_ok=True)

        # Export system events
        if self.system_monitor:
            self.system_monitor.export_events(os.path.join(output_dir, "system_events.json"))

        # Export input events
        if self.input_monitor:
            input_events = self.input_monitor.get_events(10000)
            with open(os.path.join(output_dir, "input_events.json"), 'w') as f:
                for event in input_events:
                    f.write(json.dumps({
                        'timestamp': event.timestamp.isoformat(),
                        'type': event.event_type,
                        'action': event.action,
                        'process': event.process_name,
                        'window': event.window_title
                    }) + '\n')

        logger.info(f"Monitoring data exported to {output_dir}")

    def check_admin(self):
        """Check for administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def request_admin(self):
        """Request administrator privileges"""
        if not self.is_admin:
            print("[WARNING] Requesting administrator privileges...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)

    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "version": self.VERSION,
            "security_level": "MAXIMUM",
            "enable_logging": True,
            "stealth_mode": True,
            "auto_update": True,
            "modules": {
                "screen_capture": True,
                "process_monitor": True,
                "api_hooks": True,
                "memory_scanner": True,
                "network_monitor": True,
                "stealth_engine": True,
                "advanced_bypass": True
            }
        }

        # Prefer user data config file; fallback to a config shipped beside the executable
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        alt_config = self.base_dir / "config.json"
        if alt_config.exists():
            try:
                with open(alt_config, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return default_config

    def save_config(self, config):
        """Save configuration to file"""
        # Ensure parent exists and write to user data directory
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def _determine_data_dir(self) -> Path:
        """Choose a writable per-user data directory for runtime files.
        Priority: LOCALAPPDATA\SecurityTestingFramework -> USERPROFILE\AppData\Local\SecurityTestingFramework -> USERPROFILE\SecurityTestingFramework -> TEMP\SecurityTestingFramework -> base_dir
        """
        candidates = []
        localapp = os.environ.get('LOCALAPPDATA')
        userprof = os.environ.get('USERPROFILE')
        temp = os.environ.get('TEMP') or os.environ.get('TMP')

        if localapp:
            candidates.append(Path(localapp) / 'SecurityTestingFramework')
        if userprof:
            candidates.append(Path(userprof) / 'AppData' / 'Local' / 'SecurityTestingFramework')
            candidates.append(Path(userprof) / 'SecurityTestingFramework')
        if temp:
            candidates.append(Path(temp) / 'SecurityTestingFramework')
        candidates.append(self.base_dir)

        for p in candidates:
            try:
                p.mkdir(parents=True, exist_ok=True)
                test_file = p / '.__writetest'
                with open(test_file, 'w') as tf:
                    tf.write('ok')
                try:
                    test_file.unlink(missing_ok=True)
                except TypeError:
                    # Python <3.8 compatibility
                    if test_file.exists():
                        test_file.unlink()
                return p
            except Exception:
                continue
        return self.base_dir

    def run_gui(self):
        """Launch the advanced GUI interface"""
        logger.info("Launching Advanced GUI interface...")

        # Activate stealth mode if configured
        if self.stealth_engine and self.config.get("stealth_mode"):
            logger.info("Activating stealth mode for GUI...")
            self.stealth_engine.activate()

        from src.gui.main_window import MainWindow
        app = MainWindow(self)
        app.run()

    def run_cli(self, args):
        """Run advanced command-line interface"""
        logger.info(f"Running CLI with args: {args}")

        # Check for comprehensive test mode
        if hasattr(args, 'comprehensive') and args.comprehensive:
            return self.run_comprehensive_tests(args)

        from src.cli.cli_handler import CLIHandler
        handler = CLIHandler(self)
        handler.execute(args)

    def run_test(self, test_name, target=None):
        """Run specific security test with advanced capabilities"""
        logger.info(f"Running test: {test_name} on target: {target}")

        if ADVANCED_FEATURES and self.advanced_config:
            # Use advanced test runner
            if not self.test_runner:
                self.test_runner = ComprehensiveTestRunner(self.advanced_config)

            # Map test names to runner methods
            test_map = {
                'stealth': self.test_runner._test_stealth_capabilities,
                'api_hooks': self.test_runner._test_api_hooks,
                'screen_capture': self.test_runner._test_screen_capture,
                'memory': self.test_runner._test_memory_manipulation,
                'process': self.test_runner._test_process_manipulation,
                'network': self.test_runner._test_network_capabilities,
                'persistence': self.test_runner._test_persistence,
                'injection': self.test_runner._test_injection
            }

            if test_name in test_map:
                return test_map[test_name]()
            else:
                logger.warning(f"Unknown test: {test_name}")
        else:
            # Fallback to basic test runner
            from src.modules.test_runner import TestRunner
            runner = TestRunner(self)
            return runner.run_test(test_name, target)

    def run_comprehensive_tests(self, args=None):
        """Run comprehensive security tests"""
        logger.info("Starting COMPREHENSIVE SECURITY TESTS")

        if not ADVANCED_FEATURES:
            logger.error("Advanced features not available!")
            return None

        # Select configuration based on args or prompt
        if args and hasattr(args, 'config'):
            if args.config == 'stealth':
                config = ConfigPresets.full_stealth()
            elif args.config == 'aggressive':
                config = ConfigPresets.aggressive_testing()
            elif args.config == 'passive':
                config = ConfigPresets.passive_monitoring()
            elif args.config == 'lockdown':
                config = ConfigPresets.lockdown_browser_test()
            else:
                config = self.advanced_config
        else:
            config = self.advanced_config

        # Create and run test runner
        runner = ComprehensiveTestRunner(config)
        results = runner.run_all_tests()

        return results

    def generate_report(self, output_file):
        """Generate advanced security assessment report"""
        logger.info(f"Generating report: {output_file}")

        if ADVANCED_FEATURES and hasattr(self, 'test_runner') and self.test_runner:
            # Generate report from test runner results
            results = self.test_runner.results if hasattr(self.test_runner, 'results') else []

            with open(output_file, 'w') as f:
                f.write("="*60 + "\n")
                f.write("SECURITY TESTING FRAMEWORK - ASSESSMENT REPORT\n")
                f.write("="*60 + "\n\n")
                f.write(f"Generated: {datetime.now()}\n")
                f.write(f"Version: {self.VERSION}\n")
                f.write(f"Admin Privileges: {self.is_admin}\n")

                if self.stealth_engine:
                    status = self.stealth_engine.get_status()
                    f.write(f"\nStealth Status:\n")
                    f.write(f"  Active: {status['active']}\n")
                    f.write(f"  Level: {status['level']}\n")
                    f.write(f"  Detection Status: {status['detection_status']}\n")

                f.write(f"\nTest Results:\n")
                for result in results:
                    f.write(f"  - {result}\n")

            logger.info(f"Report saved to {output_file}")
        else:
            from src.utils.report_generator import ReportGenerator
            generator = ReportGenerator(self)
            generator.generate(output_file)

    def check_updates(self):
        """Check for framework updates"""
        if self.config.get("auto_update", True):
            logger.info("Checking for updates...")
            # Check GitHub for updates
            try:
                import requests
                response = requests.get(
                    "https://api.github.com/repos/hira-edu/security-testing-framework/releases/latest"
                )
                if response.status_code == 200:
                    latest = response.json()
                    latest_version = latest['tag_name'].lstrip('v')

                    if latest_version > self.VERSION:
                        logger.info(f"Update available: {latest_version}")
                        print(f"\n[UPDATE] New version {latest_version} available!")
                        print(f"Download: {latest['html_url']}\n")
                    else:
                        logger.info("Framework is up to date")
            except Exception as e:
                logger.error(f"Update check failed: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Security Testing Framework v3.0 - Comprehensive Vulnerability Testing Platform"
    )

    parser.add_argument(
        "--monitor", action="store_true",
        help="Start in full monitoring mode (MAXIMUM CAPABILITIES)"
    )
    parser.add_argument(
        "--stealth", action="store_true",
        help="Enable maximum stealth mode"
    )
    parser.add_argument(
        "--comprehensive", action="store_true",
        help="Run comprehensive vulnerability tests"
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
        default="LockDownBrowser.exe",
        help="Target process (default: LockDownBrowser.exe)"
    )
    parser.add_argument(
        "--duration", type=int,
        default=0,
        help="Monitoring duration in seconds (0=unlimited)"
    )
    parser.add_argument(
        "--export", type=str,
        help="Export monitoring data to directory"
    )
    parser.add_argument(
        "--report", type=str,
        help="Generate report (specify output file)"
    )
    parser.add_argument(
        "--silent", action="store_true",
        help="Run in silent/headless mode"
    )
    parser.add_argument(
        "--config", type=str,
        help="Configuration file path"
    )
    parser.add_argument(
        "--no-admin", action="store_true",
        help="Don't request admin privileges"
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Automatic mode - start monitoring with all features"
    )

    args = parser.parse_args()

    # Initialize framework
    framework = SecurityTestingFramework()

    # Request admin if needed (required for full capabilities)
    if not args.no_admin and not framework.is_admin:
        framework.request_admin()

    # Auto mode - start everything
    if args.auto or (not any([args.monitor, args.comprehensive, args.test, args.report, args.cli])):
        logger.info("="*70)
        logger.info("SECURITY TESTING FRAMEWORK v3.0 - AUTOMATIC MODE")
        logger.info("Starting comprehensive vulnerability testing...")
        logger.info("="*70)

        # Enable maximum stealth
        args.stealth = True
        args.monitor = True
        args.comprehensive = True

    # Enable stealth if requested
    if args.stealth and framework.stealth_engine:
        logger.info("Enabling MAXIMUM STEALTH mode...")
        framework.stealth_engine.config.stealth_level = StealthLevel.MAXIMUM
        framework.stealth_engine.activate()
        time.sleep(1)  # Let stealth initialize

    # Start full monitoring mode
    if args.monitor:
        logger.info("="*70)
        logger.info("FULL MONITORING MODE ACTIVATED")
        logger.info(f"Target Process: {args.target}")
        logger.info(f"Duration: {'Unlimited' if args.duration == 0 else f'{args.duration} seconds'}")
        logger.info("="*70)

        # Start monitoring
        framework.start_full_monitoring(args.target)

        try:
            # Run for specified duration
            if args.duration > 0:
                time.sleep(args.duration)
            else:
                # Run until interrupted
                logger.info("Monitoring active. Press Ctrl+C to stop...")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nMonitoring interrupted by user")
        finally:
            # Stop monitoring
            framework.stop_monitoring()

            # Export data if requested
            if args.export:
                framework.export_monitoring_data(args.export)
            else:
                # Auto-export to default location
                framework.export_monitoring_data()

    # Run comprehensive tests
    if args.comprehensive:
        logger.info("Running COMPREHENSIVE vulnerability tests...")

        # Use maximum testing configuration
        config = ConfigPresets.aggressive_testing()
        config.target_process = args.target

        # Override with full capabilities
        config.anti_detection.enabled = True
        config.screen_capture.enabled = True
        config.windows_api.enabled = True
        config.memory.enabled = True
        config.injection.enabled = True
        config.directx.enabled = True

        framework.advanced_config = config
        results = framework.run_comprehensive_tests(args)

        # Generate report
        if args.report:
            framework.generate_report(args.report)
        else:
            framework.generate_report(f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    # Handle other modes
    elif args.report and not args.comprehensive:
        framework.generate_report(args.report)
    elif args.test:
        framework.run_test(args.test, args.target)
    elif args.cli:
        framework.run_cli(args)

    logger.info("Framework execution completed")

if __name__ == "__main__":
    main()
