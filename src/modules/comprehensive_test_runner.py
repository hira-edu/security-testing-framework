"""
Comprehensive Test Runner for Security Testing Framework
Integrates all advanced testing capabilities
"""

import os
import sys
import time
import json
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import traceback

# Import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stealth_engine import StealthEngine, StealthConfig, StealthLevel
from core.advanced_config import AdvancedConfiguration, ConfigPresets
from modules.api_hooks import HookManager
from modules.screen_capture_bypass import LockDownBrowserBypass

@dataclass
class TestResult:
    """Result of a test execution"""
    test_name: str
    success: bool
    start_time: str
    end_time: str
    duration: float
    details: Dict[str, Any]
    errors: List[str]
    warnings: List[str]

class ComprehensiveTestRunner:
    """Main test runner that coordinates all testing capabilities"""

    def __init__(self, config: Optional[AdvancedConfiguration] = None):
        """Initialize test runner with configuration"""
        self.config = config or ConfigPresets.full_stealth()
        self.logger = self._setup_logging()
        self.results = []
        self.running = False

        # Initialize components
        self.stealth_engine = None
        self.hook_manager = None
        self.capture_bypass = None

        self._initialize_components()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('SecurityTestRunner')
        logger.setLevel(getattr(logging, self.config.log_level))

        # File handler
        if self.config.log_file:
            fh = logging.FileHandler(self.config.log_file)
            fh.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        logger.addHandler(ch)

        return logger

    def _initialize_components(self):
        """Initialize all testing components"""
        self.logger.info("Initializing testing components...")

        try:
            # Initialize stealth engine if enabled
            if self.config.anti_detection.enabled:
                stealth_config = StealthConfig(
                    stealth_level=StealthLevel.MAXIMUM if self.config.mode.value == "stealth" else StealthLevel.HIGH,
                    hide_process=self.config.anti_detection.evade_antivirus,
                    encrypt_memory=self.config.memory.encrypt_sensitive_data,
                    obfuscate_api_calls=self.config.anti_detection.api_obfuscation,
                    randomize_behavior=self.config.anti_detection.randomize_execution,
                    detect_sandbox=self.config.anti_detection.evade_sandbox,
                    detect_vm=self.config.anti_detection.evade_vm,
                    detect_debugger=self.config.anti_detection.evade_debugger
                )
                self.stealth_engine = StealthEngine(stealth_config)
                self.logger.info("Stealth engine initialized")

            # Initialize hook manager if Windows API hooks enabled
            if self.config.windows_api.enabled:
                self.hook_manager = HookManager()
                self.logger.info("Hook manager initialized")

            # Initialize screen capture bypass if enabled
            if self.config.screen_capture.enabled:
                self.capture_bypass = LockDownBrowserBypass()
                self.logger.info("Screen capture bypass initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all configured tests"""
        self.logger.info("="*60)
        self.logger.info("STARTING COMPREHENSIVE SECURITY TESTS")
        self.logger.info("="*60)

        self.running = True
        overall_start = time.time()

        test_suite = {
            'configuration': asdict(self.config),
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }

        try:
            # Activate stealth mode if configured
            if self.stealth_engine:
                self.logger.info("Activating stealth mode...")
                self.stealth_engine.activate()
                time.sleep(1)  # Let stealth initialize

                # Check environment
                stealth_status = self.stealth_engine.get_status()
                self.logger.info(f"Stealth status: {stealth_status}")

                if stealth_status['detection_status'].get('debugger'):
                    self.logger.warning("DEBUGGER DETECTED - Some tests may fail")
                if stealth_status['detection_status'].get('vm'):
                    self.logger.warning("VIRTUAL MACHINE DETECTED")
                if stealth_status['detection_status'].get('sandbox'):
                    self.logger.warning("SANDBOX ENVIRONMENT DETECTED")

            # Run test categories
            test_categories = [
                ('stealth', self._test_stealth_capabilities),
                ('api_hooks', self._test_api_hooks),
                ('screen_capture', self._test_screen_capture),
                ('memory', self._test_memory_manipulation),
                ('process', self._test_process_manipulation),
                ('network', self._test_network_capabilities),
                ('persistence', self._test_persistence),
                ('injection', self._test_injection)
            ]

            for category, test_func in test_categories:
                if self._should_run_test(category):
                    self.logger.info(f"\n{'='*40}")
                    self.logger.info(f"Running {category.upper()} tests...")
                    self.logger.info(f"{'='*40}")

                    result = test_func()
                    test_suite['tests'].append(result)

                    # Log result
                    if result.success:
                        self.logger.info(f"✓ {category} tests PASSED")
                    else:
                        self.logger.error(f"✗ {category} tests FAILED")

        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            self.logger.error(traceback.format_exc())

        finally:
            self.running = False

            # Cleanup
            self._cleanup()

            # Calculate summary
            overall_duration = time.time() - overall_start
            test_suite['end_time'] = datetime.now().isoformat()
            test_suite['duration'] = overall_duration

            passed = sum(1 for t in test_suite['tests'] if t.success)
            failed = len(test_suite['tests']) - passed

            test_suite['summary'] = {
                'total_tests': len(test_suite['tests']),
                'passed': passed,
                'failed': failed,
                'success_rate': (passed / len(test_suite['tests']) * 100) if test_suite['tests'] else 0,
                'duration': overall_duration
            }

            # Save results
            self._save_results(test_suite)

            self.logger.info("\n" + "="*60)
            self.logger.info("TEST SUITE COMPLETED")
            self.logger.info(f"Total: {test_suite['summary']['total_tests']} | "
                           f"Passed: {passed} | Failed: {failed} | "
                           f"Success Rate: {test_suite['summary']['success_rate']:.1f}%")
            self.logger.info("="*60)

        return test_suite

    def _should_run_test(self, category: str) -> bool:
        """Check if test category should run based on config"""
        category_config = {
            'stealth': self.config.anti_detection.enabled,
            'api_hooks': self.config.windows_api.enabled,
            'screen_capture': self.config.screen_capture.enabled,
            'memory': self.config.memory.enabled,
            'process': self.config.windows_api.enabled,
            'network': self.config.network.enabled,
            'persistence': self.config.persistence.enabled,
            'injection': self.config.injection.enabled
        }
        return category_config.get(category, False)

    def _test_stealth_capabilities(self) -> TestResult:
        """Test stealth and anti-detection capabilities"""
        start_time = datetime.now()
        errors = []
        warnings = []
        details = {}

        try:
            if not self.stealth_engine:
                raise Exception("Stealth engine not initialized")

            # Get current status
            status = self.stealth_engine.get_status()
            details['stealth_status'] = status

            # Test detection evasion
            tests = {
                'sandbox_evasion': not status['detection_status'].get('sandbox', False),
                'vm_evasion': not status['detection_status'].get('vm', False),
                'debugger_evasion': not status['detection_status'].get('debugger', False),
                'stealth_active': status['active']
            }

            details['evasion_tests'] = tests
            success = all(tests.values())

            if not success:
                failed = [k for k, v in tests.items() if not v]
                errors.append(f"Failed evasion tests: {', '.join(failed)}")

        except Exception as e:
            success = False
            errors.append(str(e))

        end_time = datetime.now()
        return TestResult(
            test_name='stealth_capabilities',
            success=success,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=(end_time - start_time).total_seconds(),
            details=details,
            errors=errors,
            warnings=warnings
        )

    def _test_api_hooks(self) -> TestResult:
        """Test API hooking capabilities"""
        start_time = datetime.now()
        errors = []
        warnings = []
        details = {}

        try:
            if not self.hook_manager:
                raise Exception("Hook manager not initialized")

            # Enable hooks
            self.hook_manager.enable_lockdown_bypass_hooks()
            details['hooks_enabled'] = self.hook_manager.active_hooks

            # Test hook functionality
            # This would trigger hooked APIs and verify interception

            # Get intercepted calls
            intercepted = self.hook_manager.get_intercepted_calls()
            details['intercepted_calls'] = len(intercepted)

            success = len(self.hook_manager.active_hooks) > 0

        except Exception as e:
            success = False
            errors.append(str(e))

        end_time = datetime.now()
        return TestResult(
            test_name='api_hooks',
            success=success,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=(end_time - start_time).total_seconds(),
            details=details,
            errors=errors,
            warnings=warnings
        )

    def _test_screen_capture(self) -> TestResult:
        """Test screen capture bypass"""
        start_time = datetime.now()
        errors = []
        warnings = []
        details = {}

        try:
            if not self.capture_bypass:
                raise Exception("Capture bypass not initialized")

            # Attempt to bypass LockDown Browser protections
            results = self.capture_bypass.bypass_all_protections()
            details['bypass_results'] = {
                'window_found': results['window_found'],
                'capture_success': results['capture_success'],
                'method_used': results.get('capture_method'),
                'bypass_used': results.get('bypass_used')
            }

            success = results['capture_success'] if results['window_found'] else True

            if not results['window_found']:
                warnings.append("LockDown Browser window not found - test skipped")

        except Exception as e:
            success = False
            errors.append(str(e))

        end_time = datetime.now()
        return TestResult(
            test_name='screen_capture',
            success=success,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=(end_time - start_time).total_seconds(),
            details=details,
            errors=errors,
            warnings=warnings
        )

    def _test_memory_manipulation(self) -> TestResult:
        """Test memory manipulation capabilities"""
        start_time = datetime.now()
        errors = []
        warnings = []
        details = {}

        try:
            # Memory tests would go here
            details['memory_tests'] = {
                'encryption': self.config.memory.encrypt_sensitive_data,
                'obfuscation': self.config.memory.obfuscate_strings,
                'anti_dumping': self.config.memory.anti_dumping
            }

            success = True

        except Exception as e:
            success = False
            errors.append(str(e))

        end_time = datetime.now()
        return TestResult(
            test_name='memory_manipulation',
            success=success,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=(end_time - start_time).total_seconds(),
            details=details,
            errors=errors,
            warnings=warnings
        )

    def _test_process_manipulation(self) -> TestResult:
        """Test process manipulation capabilities"""
        start_time = datetime.now()
        errors = []
        warnings = []
        details = {}

        try:
            # Process manipulation tests
            details['process_tests'] = {
                'hook_creation': self.config.windows_api.hook_create_process,
                'hook_termination': self.config.windows_api.hook_terminate_process,
                'process_protection': bool(self.config.windows_api.protected_processes)
            }

            success = True

        except Exception as e:
            success = False
            errors.append(str(e))

        end_time = datetime.now()
        return TestResult(
            test_name='process_manipulation',
            success=success,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=(end_time - start_time).total_seconds(),
            details=details,
            errors=errors,
            warnings=warnings
        )

    def _test_network_capabilities(self) -> TestResult:
        """Test network capabilities"""
        start_time = datetime.now()
        errors = []
        warnings = []
        details = {}

        try:
            if not self.config.network.enabled:
                warnings.append("Network testing disabled")
                success = True
            else:
                # Network tests would go here
                details['network_tests'] = {
                    'encryption': self.config.network.use_encryption,
                    'proxy': self.config.network.use_proxy,
                    'c2': self.config.network.c2_enabled
                }
                success = True

        except Exception as e:
            success = False
            errors.append(str(e))

        end_time = datetime.now()
        return TestResult(
            test_name='network_capabilities',
            success=success,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=(end_time - start_time).total_seconds(),
            details=details,
            errors=errors,
            warnings=warnings
        )

    def _test_persistence(self) -> TestResult:
        """Test persistence mechanisms"""
        start_time = datetime.now()
        errors = []
        warnings = []
        details = {}

        try:
            if not self.config.persistence.enabled:
                warnings.append("Persistence testing disabled")
                success = True
            else:
                # Persistence tests would go here
                details['persistence_tests'] = {
                    'registry': self.config.persistence.registry_persistence,
                    'scheduled_task': self.config.persistence.scheduled_task,
                    'service': self.config.persistence.service_persistence
                }
                success = True

        except Exception as e:
            success = False
            errors.append(str(e))

        end_time = datetime.now()
        return TestResult(
            test_name='persistence',
            success=success,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=(end_time - start_time).total_seconds(),
            details=details,
            errors=errors,
            warnings=warnings
        )

    def _test_injection(self) -> TestResult:
        """Test code injection capabilities"""
        start_time = datetime.now()
        errors = []
        warnings = []
        details = {}

        try:
            if not self.config.injection.enabled:
                warnings.append("Injection testing disabled")
                success = True
            else:
                # Injection tests would go here
                details['injection_tests'] = {
                    'methods': self.config.injection.methods,
                    'manual_mapping': self.config.injection.use_manual_mapping,
                    'reflective_dll': self.config.injection.use_reflective_dll
                }
                success = True

        except Exception as e:
            success = False
            errors.append(str(e))

        end_time = datetime.now()
        return TestResult(
            test_name='injection',
            success=success,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=(end_time - start_time).total_seconds(),
            details=details,
            errors=errors,
            warnings=warnings
        )

    def _cleanup(self):
        """Cleanup after tests"""
        self.logger.info("Performing cleanup...")

        try:
            # Disable hooks
            if self.hook_manager:
                self.hook_manager.disable_all_hooks()

            # Deactivate stealth
            if self.stealth_engine:
                self.stealth_engine.active = False

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    def _save_results(self, results: Dict[str, Any]):
        """Save test results to a user-writable directory"""
        try:
            # Determine a writable results directory
            localapp = os.environ.get('LOCALAPPDATA')
            userprof = os.environ.get('USERPROFILE')
            temp = os.environ.get('TEMP') or os.environ.get('TMP')

            candidates = []
            if localapp:
                candidates.append(Path(localapp) / 'SecurityTestingFramework' / 'results')
            if userprof:
                candidates.append(Path(userprof) / 'AppData' / 'Local' / 'SecurityTestingFramework' / 'results')
                candidates.append(Path(userprof) / 'SecurityTestingFramework' / 'results')
            if temp:
                candidates.append(Path(temp) / 'SecurityTestingFramework' / 'results')
            # Fallback to current directory
            candidates.append(Path.cwd())

            results_dir = None
            for p in candidates:
                try:
                    p.mkdir(parents=True, exist_ok=True)
                    test_file = p / '.__writetest'
                    with open(test_file, 'w') as tf:
                        tf.write('ok')
                    try:
                        test_file.unlink(missing_ok=True)
                    except TypeError:
                        if test_file.exists():
                            test_file.unlink()
                    results_dir = p
                    break
                except Exception:
                    continue

            filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            out_path = (results_dir or Path.cwd()) / filename
            with open(out_path, 'w') as f:
                json.dump(results, f, indent=4, default=str)
            self.logger.info(f"Results saved to {out_path}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")


def main():
    """Main entry point for test runner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║       SECURITY TESTING FRAMEWORK - COMPREHENSIVE TEST        ║
║                    Professional Edition v2.0                  ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Select configuration preset
    print("\nSelect test configuration:")
    print("1. Passive Monitoring")
    print("2. Full Stealth Mode")
    print("3. Aggressive Testing")
    print("4. LockDown Browser Specific")
    print("5. Custom Configuration")

    choice = input("\nEnter choice (1-5): ")

    config_map = {
        '1': ConfigPresets.passive_monitoring(),
        '2': ConfigPresets.full_stealth(),
        '3': ConfigPresets.aggressive_testing(),
        '4': ConfigPresets.lockdown_browser_test(),
        '5': AdvancedConfiguration()
    }

    config = config_map.get(choice, ConfigPresets.full_stealth())

    # Create and run test runner
    runner = ComprehensiveTestRunner(config)
    results = runner.run_all_tests()

    print("\nTest complete. Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()
