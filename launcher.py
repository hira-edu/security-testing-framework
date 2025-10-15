
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
            print("[WARNING] Requesting administrator privileges...")
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
