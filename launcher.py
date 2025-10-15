
#!/usr/bin/env python3
"""
Security Testing Framework - Advanced Launcher
Includes stealth engine, monitoring, and comprehensive tests.
"""

import sys
import os
import ctypes
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

from src.core.stealth_engine import StealthEngine, StealthConfig, StealthLevel
from src.core.advanced_config import AdvancedConfiguration, ConfigPresets
from src.modules.comprehensive_test_runner import ComprehensiveTestRunner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SecurityTestingFramework:
    VERSION = "3.0.0"

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = self._determine_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.data_dir / "config.json"
        self.is_admin = self._check_admin()
        self.config = self._load_config()
        self.advanced_config = None
        self.stealth_engine = None

    def _determine_data_dir(self) -> Path:
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
                (p / '.__w').write_text('ok')
                (p / '.__w').unlink(missing_ok=True)
                return p
            except Exception:
                continue
        return self.base_dir

    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def request_admin(self):
        if not self.is_admin:
            logger.warning("Requesting administrator privileges...")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)

    def _load_config(self):
        default_config = {
            "version": self.VERSION,
            "security_level": "MAXIMUM",
            "enable_logging": True,
            "stealth_mode": True,
            "auto_update": False,
        }
        if self.config_file.exists():
            try:
                return json.load(open(self.config_file, 'r'))
            except Exception:
                pass
        alt = self.base_dir / 'config.json'
        if alt.exists():
            try:
                return json.load(open(alt, 'r'))
            except Exception:
                pass
        return default_config

    def save_config(self):
        try:
            json.dump(self.config, open(self.config_file, 'w'), indent=4)
        except Exception:
            pass

    def init_stealth(self, maximum: bool = True):
        stealth_level = StealthLevel.MAXIMUM if maximum else StealthLevel.HIGH
        sconf = StealthConfig(stealth_level=stealth_level, hide_process=True, encrypt_memory=True,
                              obfuscate_api_calls=True, randomize_behavior=True,
                              detect_sandbox=True, detect_vm=True, detect_debugger=True)
        self.stealth_engine = StealthEngine(sconf)
        self.stealth_engine.activate()
        logger.info("Stealth engine activated: %s", stealth_level.name)

    def run_comprehensive(self, target: str = None):
        self.advanced_config = ConfigPresets.full_stealth()
        runner = ComprehensiveTestRunner(self.advanced_config)
        results = runner.run_all_tests()
        return results

    def run_gui(self):
        from src.gui.main_window import MainWindow
        app = MainWindow(self)
        app.run()


def main():
    p = argparse.ArgumentParser(description="Security Testing Framework - Advanced")
    p.add_argument("--monitor", action="store_true", help="Start monitoring mode")
    p.add_argument("--stealth", action="store_true", help="Enable maximum stealth mode")
    p.add_argument("--comprehensive", action="store_true", help="Run comprehensive tests")
    p.add_argument("--cli", action="store_true", help="Run in CLI mode")
    p.add_argument("--test", type=str, help="Run specific test suite")
    p.add_argument("--target", type=str, default="LockDownBrowser.exe", help="Target process")
    p.add_argument("--report", type=str, help="Generate report to file")
    p.add_argument("--silent", action="store_true", help="Silent/headless mode")
    p.add_argument("--config", type=str, help="Configuration file path")
    p.add_argument("--no-admin", action="store_true", help="Do not request admin")
    args = p.parse_args()

    fw = SecurityTestingFramework()
    if not args.no_admin and not fw.is_admin:
        fw.request_admin()

    if args.stealth:
        fw.init_stealth(maximum=True)

    if args.comprehensive:
        res = fw.run_comprehensive(args.target)
        if args.report:
            with open(args.report, 'w') as f:
                json.dump(res, f, indent=2, default=str)
        return

    if args.test:
        from src.modules.test_runner import TestRunner
        TestRunner(fw).run_test(args.test, args.target)
        return

    if args.cli:
        from src.cli.cli_handler import CLIHandler
        CLIHandler(fw).execute(args)
        return

    fw.run_gui()


if __name__ == '__main__':
    main()
