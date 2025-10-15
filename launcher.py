
#!/usr/bin/env python3
"""
Security Testing Framework - Main Launcher v2.0
Advanced Professional Security Testing Tool
"""

import sys
import os
import ctypes
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Try to import advanced modules
try:
    from core.stealth_engine import StealthEngine, StealthConfig, StealthLevel
    from core.advanced_config import AdvancedConfiguration, ConfigPresets
    from modules.comprehensive_test_runner import ComprehensiveTestRunner
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False
    print("[WARNING] Advanced features not available. Basic mode enabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityTestingFramework:
    """Advanced framework controller with stealth capabilities"""

    VERSION = "2.0.0"

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "config.json"
        self.is_admin = self.check_admin()
        self.config = self.load_config()
        self.advanced_config = None
        self.stealth_engine = None
        self.test_runner = None

        # Initialize advanced features if available
        if ADVANCED_FEATURES:
            self._init_advanced_features()

    def _init_advanced_features(self):
        """Initialize advanced testing features"""
        try:
            # Load or create advanced configuration
            adv_config_file = self.base_dir / "advanced_config.json"
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

        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return default_config

    def save_config(self, config):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

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
