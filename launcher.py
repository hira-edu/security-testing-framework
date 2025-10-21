#!/usr/bin/env python3
"""
Security Testing Framework - Advanced Launcher
Includes stealth engine, monitoring, and comprehensive tests.
"""

import sys
import os
import ctypes
import json
import copy
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.cli.constants import CLICommand
from src.cli.default_profiles import build_default_profiles
from src.cli.profile_store import ProfileStore

if TYPE_CHECKING:
    from src.cli.profile_store import CLIProfile
from src.core.stealth_engine import StealthEngine, StealthConfig, StealthLevel
from src.core.advanced_config import AdvancedConfiguration, ConfigPresets
from src.modules.comprehensive_test_runner import ComprehensiveTestRunner
from src.modules.process_inventory import ProcessInventory

try:
    from src.modules.api_hooks import HookManager
except Exception:  # pragma: no cover - optional dependency handling
    HookManager = None  # type: ignore

try:
    from src.modules.screen_capture_bypass import ScreenCaptureBypass
except Exception:  # pragma: no cover - optional dependency handling
    ScreenCaptureBypass = None  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SecurityTestingFramework:
    VERSION = "1.0.0"

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.vendor_root: Optional[Path] = None
        self._configure_vendor_environment()
        self.data_dir = self._determine_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.data_dir / "config.json"
        self.profile_store = ProfileStore(self.data_dir / "profiles")
        self.profile_store.seed_defaults(build_default_profiles())
        self.is_admin = self._check_admin()
        self.config = self._load_config()
        self.version = self.config.get("version", self.VERSION)
        self.VERSION = self.version
        self.build_time = self.config.get("build_time")
        template_defaults = self._default_config()
        for section in ("capture", "hooks", "performance", "security", "logging"):
            if section not in self.config:
                self.config[section] = copy.deepcopy(template_defaults[section])
        self.bypass_methods_config = self.config.get("bypass_methods", {})
        self.module_flags = self._resolve_module_flags(self.config)
        self.targets = self._ensure_targets(self.config)
        self.primary_target = self.targets[0] if self.targets else "LockDownBrowser.exe"
        self.capture_config = self.config.get("capture", {})
        self.hook_config = self.config.get("hooks", {})
        self.performance_config = self.config.get("performance", {})
        self.security_config = self.config.get("security", {})
        self.logging_config = self.config.get("logging", {})

        self.config["version"] = self.VERSION
        if self.build_time:
            self.config["build_time"] = self.build_time
        self.config["modules"] = dict(self.module_flags)
        self.config["targets"] = list(self.targets)
        self.advanced_config = None
        self.stealth_engine = None
        self.hook_manager = HookManager() if HookManager and self.module_flags.get("api_hooks", True) else None
        self.capture_bypass = ScreenCaptureBypass() if ScreenCaptureBypass and self.module_flags.get("screen_capture", True) else None
        self.process_inventory = ProcessInventory() if self.module_flags.get("process_monitor", True) else None

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

    def _default_config(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "build_time": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "security_level": "HIGH",
            "enable_logging": True,
            "stealth_mode": True,
            "auto_update": True,
            "modules": {
                "screen_capture": True,
                "process_monitor": True,
                "api_hooks": True,
                "memory_scanner": True,
                "network_monitor": True,
                "gui": False,
            },
            "capture": {
                "method": "enhanced_capture",
                "fallback_chain": [
                    "windows_graphics_capture",
                    "dxgi_desktop_duplication",
                    "direct3d_capture",
                    "gdi_capture",
                ],
                "frame_rate": 60,
                "quality": "high",
                "compression": True,
                "compression_level": 6,
                "hardware_acceleration": True,
                "buffer_size": 10_485_760,
            },
            "hooks": {
                "directx": {
                    "enabled": True,
                    "versions": ["11", "12"],
                    "interfaces": ["IDXGISwapChain", "ID3D11Device", "ID3D12Device"],
                },
                "windows_api": {
                    "enabled": True,
                    "functions": [
                        "SetForegroundWindow",
                        "GetForegroundWindow",
                        "CreateProcess",
                        "TerminateProcess",
                    ],
                },
                "keyboard": {
                    "enabled": True,
                    "blocked_keys": ["F12", "VK_SNAPSHOT"],
                    "hotkeys": {
                        "ctrl+alt+s": "screenshot",
                        "ctrl+alt+q": "quit",
                    },
                },
                "process": {
                    "enabled": False,
                },
            },
            "performance": {
                "monitoring": True,
                "sampling_interval": 1000,
                "memory_tracking": True,
                "leak_threshold": 1_048_576,
                "optimization": {
                    "memory_pool": True,
                    "thread_pool": True,
                    "hardware_acceleration": True,
                },
                "limits": {
                    "max_cpu_usage": 80.0,
                    "max_memory_usage": 1_073_741_824,
                    "max_frame_rate": 60,
                },
            },
            "security": {
                "anti_detection": True,
                "obfuscation": False,
                "integrity_checking": True,
            },
            "logging": {
                "level": "medium",
                "file": "undownunlock.log",
                "console_output": True,
            },
            "bypass_methods": {
                "enabled": True,
                "package_root": "src.external.bypass_methods",
                "native": {
                    "dll": "native/bypass_methods/dll/UndownUnlockDXHook.dll",
                    "auto_stage": True,
                },
                "features": {
                    "capture": True,
                    "api_hooks": True,
                    "security": True,
                    "gui": False,
                },
            },
            "targets": [
                "LockDownBrowser.exe",
                "LockDownBrowserOEM.exe",
                "Lockdown.exe",
                "SafeExamBrowser.exe",
                "Respondus.exe",
                "OnVUE.exe",
                "ProProctor.exe",
                "ETSBrowser.exe",
                "Prometric.exe",
                "ProctorTrack.exe",
                "ExamitySecureBrowser.exe",
                "Examplify.exe",
                "RPNow.exe",
                "GuardianBrowser.exe",
                "HonorlockBrowser.exe",
            ],
        }

    def _configure_vendor_environment(self) -> None:
        vendor_root = self.base_dir / "src" / "external" / "bypass_methods"
        if vendor_root.exists():
            self.vendor_root = vendor_root
            vendor_path = str(vendor_root)
            if vendor_path not in sys.path:
                sys.path.insert(0, vendor_path)
        else:
            self.vendor_root = None
        try:
            from src.utils import native_paths
        except Exception as exc:  # pragma: no cover - optional helper
            logger.debug("native_paths helper unavailable: %s", exc)
            return

        native_paths.ensure_native_dirs()
        dll_path = native_paths.get_bypass_methods_dll()
        if not dll_path.exists():
            logger.debug("Bypass-methods DLL not staged at %s", dll_path)
        if os.name == "nt" and hasattr(os, "add_dll_directory"):
            for directory in native_paths.runtime_dll_search_paths():
                if os.path.isdir(directory):
                    try:
                        os.add_dll_directory(directory)
                    except OSError as err:  # pragma: no cover - defensive
                        logger.debug("Failed to register DLL directory %s: %s", directory, err)

    def _deep_merge(self, base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        result = copy.deepcopy(base)
        for key, value in overrides.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _merge_config(self, defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(overrides, dict):
            return copy.deepcopy(defaults)
        return self._deep_merge(defaults, overrides)

    def _resolve_module_flags(self, config: Dict[str, Any]) -> Dict[str, bool]:
        defaults = {
            "screen_capture": True,
            "process_monitor": True,
            "api_hooks": True,
            "memory_scanner": True,
            "network_monitor": True,
            "gui": False,
        }
        modules = config.get("modules") or {}
        features = (config.get("bypass_methods") or {}).get("features", {})
        feature_overrides = {
            "screen_capture": bool(features.get("capture", True)),
            "api_hooks": bool(features.get("api_hooks", True)),
            "gui": bool(features.get("gui", modules.get("gui", False))),
        }
        resolved = {}
        for name, default in defaults.items():
            base_enabled = bool(modules.get(name, default))
            feature_enabled = feature_overrides.get(name, True)
            resolved[name] = base_enabled and feature_enabled
        return resolved

    def _ensure_targets(self, config: Dict[str, Any]) -> List[str]:
        targets = config.get("targets")
        if isinstance(targets, list) and targets:
            return targets
        return ["LockDownBrowser.exe", "SafeExamBrowser.exe", "Respondus.exe"]

    def _load_config(self):
        defaults = self._default_config()
        for candidate in (self.config_file, self.base_dir / "config.json"):
            if candidate.exists():
                try:
                    with candidate.open("r", encoding="utf-8") as handle:
                        loaded = json.load(handle)
                    return self._merge_config(defaults, loaded)
                except Exception as exc:
                    logger.warning("Failed to load config from %s: %s", candidate, exc)
        return defaults

    def save_config(self):
        try:
            with self.config_file.open("w", encoding="utf-8") as handle:
                json.dump(self.config, handle, indent=4)
        except Exception as exc:
            logger.warning("Failed to save configuration to %s: %s", self.config_file, exc)

    def _require_hook_manager(self):
        if not self.module_flags.get("api_hooks", True):
            raise RuntimeError("API hook functionality is disabled in the current configuration.")
        if not self.hook_manager:
            raise RuntimeError("API hook manager is unavailable on this platform or missing dependencies.")
        return self.hook_manager

    def _require_capture_bypass(self):
        if not self.module_flags.get("screen_capture", True):
            raise RuntimeError("Screen capture module is disabled in the current configuration.")
        if not self.capture_bypass:
            raise RuntimeError("Screen capture bypass module is unavailable on this platform or missing dependencies.")
        return self.capture_bypass

    def _require_process_inventory(self):
        if not self.module_flags.get("process_monitor", True):
            raise RuntimeError("Process monitoring is disabled in the current configuration.")
        if not self.process_inventory:
            raise RuntimeError("Process inventory module is unavailable on this platform or missing dependencies.")
        return self.process_inventory

    def _resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.data_dir / candidate
        return candidate

    def _write_json(self, destination: str, data: Dict[str, Any]) -> str:
        output_path = self._resolve_path(destination)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')
        return str(output_path)

    def load_inventory_snapshot(self, path: str) -> Dict[str, Any]:
        snapshot_path = self._resolve_path(path)
        return json.loads(snapshot_path.read_text(encoding='utf-8'))

    def remember_inventory_selection(
        self,
        selection: Dict[str, Any],
        snapshot: Dict[str, Any],
        *,
        label: str = "auto",
    ) -> str:
        timestamp = int(time.time())
        relative_path = f"inventory/selection/{label}_{timestamp}.json"
        payload = {
            "collected_at": snapshot.get("collected_at"),
            "filters": snapshot.get("filters"),
            "processes": snapshot.get("processes"),
            "selection": selection,
        }
        return self._write_json(relative_path, payload)

    def resolve_inventory_process(
        self,
        snapshot: Dict[str, Any],
        *,
        pid: Optional[int],
        name: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        processes = snapshot.get("processes") or []
        for proc in processes:
            if pid is not None and proc.get("pid") == pid:
                return proc
        if name:
            query = name.lower()
            for proc in processes:
                candidate = str(proc.get("name", "")).lower()
                exe = str(proc.get("exe", "")).lower()
                if query in candidate or query in exe:
                    return proc
        return processes[0] if processes else None

    def inventory(
        self,
        filters: Optional[Dict[str, Any]] = None,
        output: Optional[str] = None,
        baseline: Optional[str] = None,
    ) -> Dict[str, Any]:
        inventory_module = self._require_process_inventory()
        snapshot = inventory_module.collect(filters or {})
        snapshot["command"] = CLICommand.INVENTORY.value
        if baseline:
            try:
                baseline_path = self._resolve_path(baseline)
                baseline_data = self.load_inventory_snapshot(str(baseline_path))
                snapshot["diff"] = inventory_module.diff_snapshots(baseline_data, snapshot)
                snapshot["baseline_path"] = str(baseline_path)
            except Exception as exc:  # pragma: no cover - defensive
                snapshot["baseline_error"] = str(exc)
        if output:
            snapshot["output_path"] = self._write_json(output, snapshot)
        return snapshot

    def list_profiles(self) -> List[Dict[str, Any]]:
        return self.profile_store.list_profiles()

    def load_profile(self, name: str) -> "CLIProfile":
        return self.profile_store.load(name)

    def save_profile(self, profile: "CLIProfile", overwrite: bool = False) -> "CLIProfile":
        return self.profile_store.save(profile, overwrite=overwrite)

    def delete_profile(self, name: str) -> None:
        self.profile_store.delete(name)

    def apply_profile(self, name: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.profile_store.apply(name, overrides=overrides)

    def enable_hooks(
        self,
        hooks: Optional[List[str]] = None,
        profile: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        manager = self._require_hook_manager()
        context_payload = context or {}
        if profile:
            return manager.enable_profile(profile, target_info=context_payload)
        return manager.enable_hooks(hooks, target_info=context_payload)

    def disable_hooks(self, hooks: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        manager = self._require_hook_manager()
        return manager.disable_hooks(hooks)

    def hooks_status(self) -> Dict[str, Any]:
        manager = self._require_hook_manager()
        return manager.get_status()

    def monitor(
        self,
        *,
        target: Optional[str],
        profile: Optional[str],
        duration: Optional[int],
        stealth: bool,
        comprehensive: bool,
        output: Optional[str],
    ) -> Dict[str, Any]:
        profile_name = profile or "lockdown-bypass"
        target_name = target or self.primary_target
        summary: Dict[str, Any] = {
            "target": target_name,
            "profile": profile_name,
            "duration": duration or 0,
            "stealth": stealth,
            "comprehensive": comprehensive,
            "timestamp": datetime.now().isoformat(),
        }

        if stealth:
            if self.config.get("stealth_mode", False):
                self.init_stealth(maximum=True)
                summary["stealth_status"] = "initialised"
            else:
                summary["stealth_status"] = "disabled_by_config"
        elif self.config.get("stealth_mode"):
            summary["stealth_status"] = "available"
        else:
            summary["stealth_status"] = "disabled"

        hook_context = {
            "source": "monitor",
            "target": summary["target"],
            "profile": profile_name,
        }

        hooks_enabled = (
            self.module_flags.get("api_hooks", True)
            and self.hook_config.get("windows_api", {}).get("enabled", True)
        )

        if hooks_enabled:
            try:
                hook_results = self.enable_hooks(profile=profile_name, context=hook_context)
                summary["hook_operations"] = hook_results
                summary["hook_context"] = hook_context
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to enable hooks: %s", exc)
                summary["hook_operations"] = [{"status": "error", "error": str(exc)}]
                summary["hook_context"] = hook_context

            try:
                summary["hook_status"] = self.hooks_status()
            except Exception as exc:  # pragma: no cover - defensive
                summary["hook_status"] = {"status": "unavailable", "error": str(exc)}
        else:
            reason = "api_hooks disabled in config"
            if not self.hook_config.get("windows_api", {}).get("enabled", True):
                reason = "windows_api hooks disabled in user config"
            summary["hook_operations"] = [{"status": "skipped", "reason": reason}]
            summary["hook_context"] = hook_context
            summary["hook_status"] = {"status": "disabled"}

        if comprehensive:
            results = self.run_comprehensive(target_name)
            summary["comprehensive_results"] = results

        if duration:
            summary["notes"] = "Duration parameter acknowledged; continuous monitoring loop not yet implemented."

        if output:
            summary["output_path"] = self._write_json(output, summary)

        return summary

    def capture(
        self,
        *,
        target: Optional[str],
        method: str = "auto",
        output_image: Optional[str] = None,
        output_json: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_name = target or self.primary_target
        bypass = self._require_capture_bypass()
        capture_cfg = self.capture_config or {}
        configured_method = capture_cfg.get("method", "auto")
        fallback_chain = capture_cfg.get("fallback_chain") or []

        methods_to_try: List[str] = []
        requested_method = method or configured_method
        if requested_method == "enhanced_capture":
            methods_to_try = [m for m in fallback_chain] or ["auto"]
        else:
            methods_to_try = [requested_method or "auto"]

        capture_result = None
        attempt_log: List[Dict[str, Any]] = []
        for candidate in methods_to_try:
            capture_result = bypass.capture_protected_window(method=candidate)
            attempt_log.append(
                {
                    "method": candidate,
                    "success": getattr(capture_result, "success", False),
                    "error": getattr(capture_result, "error", None),
                    "bypass": getattr(capture_result, "bypass_used", None),
                }
            )
            if capture_result.success:
                break

        if capture_result is None:
            raise RuntimeError("Capture module returned no result.")

        payload: Dict[str, Any] = {
            "target": target_name,
            "method": getattr(capture_result, "method", methods_to_try[-1]),
            "success": capture_result.success,
            "bypass_used": getattr(capture_result, "bypass_used", None),
            "error": capture_result.error,
            "attempts": attempt_log,
        }

        if capture_result.image and output_image:
            image_path = Path(output_image)
            if not image_path.is_absolute():
                image_path = self.data_dir / image_path
            image_path.parent.mkdir(parents=True, exist_ok=True)
            capture_result.image.save(image_path)
            payload["image_path"] = str(image_path)

        if output_json:
            payload["metadata_path"] = self._write_json(output_json, payload)

        return payload

    def init_stealth(self, maximum: bool = True):
        stealth_level = StealthLevel.MAXIMUM if maximum else StealthLevel.HIGH
        sconf = StealthConfig(stealth_level=stealth_level, hide_process=True, encrypt_memory=True,
                              obfuscate_api_calls=True, randomize_behavior=True,
                              detect_sandbox=True, detect_vm=True, detect_debugger=True)
        self.stealth_engine = StealthEngine(sconf)
        self.stealth_engine.activate()
        logger.info("Stealth engine activated: %s", stealth_level.name)

    def run_comprehensive(self, target: str = None):
        target_name = target or self.primary_target
        config = ConfigPresets.full_stealth()
        config.anti_detection.enabled = bool(self.config.get("stealth_mode", False))
        hook_directx_enabled = self.hook_config.get("directx", {}).get("enabled", True)
        config.directx.enabled = self.module_flags.get("screen_capture", True) and hook_directx_enabled
        config.screen_capture.enabled = self.module_flags.get("screen_capture", True)
        hook_windows_api_enabled = self.hook_config.get("windows_api", {}).get("enabled", True)
        config.windows_api.enabled = self.module_flags.get("api_hooks", True) and hook_windows_api_enabled
        config.memory.enabled = self.module_flags.get("memory_scanner", True)
        config.network.enabled = self.module_flags.get("network_monitor", True)
        config.persistence.enabled = self.module_flags.get("process_monitor", True)
        process_hooks_enabled = self.hook_config.get("process", {}).get("enabled", False)
        config.injection.enabled = self.module_flags.get("api_hooks", True) and (hook_windows_api_enabled or process_hooks_enabled)
        config.target_process = target_name
        config.target_window_title = target_name

        self.advanced_config = config
        runner = ComprehensiveTestRunner(config)
        results = runner.run_all_tests()
        return results

    def run_gui(self):
        if not self.module_flags.get("gui", False):
            logger.info("GUI module disabled; launching interactive shell instead.")
            from src.cli.shell import launch_shell

            launch_shell(self, _build_parser, show_banner=True)
            return

        try:
            from src.gui.main_window import MainWindow
        except Exception as exc:  # pragma: no cover - optional dependency handling
            logger.error("GUI dependencies unavailable: %s", exc)
            logger.info("Falling back to interactive shell.")
            from src.cli.shell import launch_shell

            launch_shell(self, _build_parser, show_banner=True)
            return

        app = MainWindow(self)
        app.run()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Security Testing Framework - Advanced")
    parser.add_argument("--stealth", action="store_true", help="Enable maximum stealth mode before running")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive tests (legacy flag)")
    parser.add_argument("--test", type=str, help="Run specific test suite")
    parser.add_argument("--target", type=str, help="Target process")
    parser.add_argument("--report", type=str, help="Generate report to file")
    parser.add_argument("--silent", action="store_true", help="Silent/headless mode")
    parser.add_argument("--config", type=str, help="Configuration file path")
    parser.add_argument("--no-admin", action="store_true", help="Do not request admin")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = False

    monitor_parser = subparsers.add_parser("monitor", help="Run monitoring workflow")
    monitor_parser.add_argument("--target", type=str, default="LockDownBrowser.exe", help="Target process")
    monitor_parser.add_argument("--profile", type=str, help="Profile name to apply")
    monitor_parser.add_argument("--duration", type=int, default=0, help="Monitoring duration in seconds (0=indefinite)")
    monitor_parser.add_argument("--stealth", action="store_true", help="Initialise stealth engine before monitoring")
    monitor_parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive test suite")
    monitor_parser.add_argument("--output", type=str, help="Optional path to persist results")

    inject_parser = subparsers.add_parser("inject", help="Queue injection workflow")
    inject_parser.add_argument("--target", type=str, help="Target process name or PID")
    inject_parser.add_argument("--method", type=str, required=True, help="Injection method (section-map, manual-map, etc.)")
    inject_parser.add_argument("--dll", type=str, help="DLL to inject when required")
    inject_parser.add_argument("--profile", type=str, help="Profile to use for injection options")
    inject_parser.add_argument("--layer", action="append", help="Preferred hook layer(s)")
    inject_parser.add_argument("--dry-run", action="store_true", help="Plan the injection without executing it.")
    inject_parser.add_argument(
        "--from-inventory",
        dest="from_inventory",
        type=str,
        help="Resolve target details from an inventory snapshot JSON.",
    )

    capture_parser = subparsers.add_parser("capture", help="Run capture workflow")
    capture_parser.add_argument("--target", type=str, help="Target window or process")
    capture_parser.add_argument("--method", type=str, help="Capture method override")
    capture_parser.add_argument("--output", type=str, help="Path to store capture metadata (JSON)")
    capture_parser.add_argument("--image", type=str, help="Path to store the captured image")
    capture_parser.add_argument("--metadata", type=str, help="Alternative metadata path (alias for --output)")

    hooks_parser = subparsers.add_parser("hooks", help="Manage hook layers")
    hooks_parser.add_argument("--action", type=str, required=True, choices=["status", "enable", "disable"], help="Hook action to perform")
    hooks_parser.add_argument("--profile", type=str, help="Hook profile to apply (e.g. lockdown-bypass)")
    hooks_parser.add_argument("--layer", action="append", help="Layer(s) to enable or disable")
    hooks_parser.add_argument("--target", type=str, help="Target process or executable context")
    hooks_parser.add_argument("--process", type=str, help="Process name context (alias for --target)")
    hooks_parser.add_argument("--pid", type=int, help="Process ID context")
    hooks_parser.add_argument("--file", type=str, help="Executable or DLL path context")
    hooks_parser.add_argument("--service", type=str, help="Service name context")

    report_parser = subparsers.add_parser("report", help="Generate framework report")
    report_parser.add_argument("--target", type=str, default="LockDownBrowser.exe", help="Target process for context")
    report_parser.add_argument("--output", type=str, required=True, help="Output path for report JSON")
    report_parser.add_argument(
        "--pid",
        type=int,
        help="Optional PID to reference when using --from-inventory.",
    )
    report_parser.add_argument(
        "--from-inventory",
        dest="from_inventory",
        type=str,
        help="Load context from an inventory snapshot JSON.",
    )
    report_parser.add_argument("--input", type=str, help="Existing results file to transform")

    inventory_parser = subparsers.add_parser("inventory", help="Inspect running processes and apply filters")
    inventory_parser.add_argument("--name", type=str, help="Filter by process name (substring match)")
    inventory_parser.add_argument("--pid", type=int, help="Filter by exact PID")
    inventory_parser.add_argument("--session", type=int, help="Filter by Windows session ID")
    inventory_parser.add_argument(
        "--integrity",
        type=str,
        choices=["low", "medium", "high", "system", "protected", "unknown"],
        help="Filter by integrity level.",
    )
    inventory_parser.add_argument("--user", type=str, help="Filter by username (substring match)")
    inventory_parser.add_argument("--window", type=str, help="Filter by window title substring")
    inventory_parser.add_argument("--limit", type=int, help="Limit number of results returned")
    inventory_parser.add_argument("--picker", action="store_true", help="Interactively choose a process after listing results.")
    inventory_parser.add_argument(
        "--baseline",
        type=str,
        help="Path to a previous inventory snapshot JSON for diffing results.",
    )
    inventory_parser.add_argument(
        "--sort-by",
        type=str,
        choices=["name", "pid", "session_id", "integrity", "username", "cpu_percent"],
        help="Sort results by the specified column.",
    )
    inventory_parser.add_argument(
        "--sort-desc",
        action="store_true",
        help="Sort in descending order when --sort-by is provided.",
    )
    inventory_parser.add_argument(
        "--no-windows",
        dest="include_windows",
        action="store_false",
        help="Skip window enumeration for faster collection.",
    )
    inventory_parser.add_argument("--output", type=str, help="Optional path to persist the snapshot JSON")
    inventory_parser.set_defaults(include_windows=True)

    profiles_parser = subparsers.add_parser("profiles", help="Manage CLI profiles")
    profiles_parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=["list", "show", "add", "remove", "apply"],
        help="Profile management action to perform.",
    )
    profiles_parser.add_argument("--name", type=str, help="Profile name.")
    profiles_parser.add_argument(
        "--base-command",
        type=str,
        choices=[
            cmd.value
            for cmd in CLICommand
            if cmd not in {CLICommand.PROFILES, CLICommand.SHELL}
        ],
        help="Underlying command the profile configures.",
    )
    profiles_parser.add_argument(
        "--description",
        type=str,
        help="Optional description for the profile.",
    )
    profiles_parser.add_argument(
        "--set",
        dest="kv_pairs",
        action="append",
        help="Define or override an option using key=value. Repeat for multiple entries.",
    )
    profiles_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing profile with the same name when adding.",
    )

    shell_parser = subparsers.add_parser("shell", help="Launch interactive shell session")
    shell_parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress the welcome banner when the shell starts.",
    )

    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()

    fw = SecurityTestingFramework()
    if not getattr(args, "no_admin", False) and not fw.is_admin:
        fw.request_admin()

    if args.command == CLICommand.SHELL.value:
        from src.cli.shell import launch_shell

        launch_shell(
            fw,
            _build_parser,
            show_banner=not getattr(args, "no_banner", False),
        )
        return

    if args.command:
        from src.cli.cli_handler import CLIHandler, CLIRequest

        handler = CLIHandler(fw)
        request = CLIRequest.from_namespace(args)
        try:
            response = handler.execute(request)
        except Exception as exc:  # noqa: BLE001
            logger.error("CLI command failed: %s", exc)
            if not args.silent:
                print(json.dumps({"error": str(exc)}, indent=2, default=str))
            sys.exit(1)
        if not args.silent:
            print(json.dumps(response, indent=2, default=str))
        return

    if args.stealth:
        if fw.config.get("stealth_mode", False):
            fw.init_stealth(maximum=True)
        else:
            logger.warning("Stealth flag requested but stealth_mode is disabled in config.")

    if args.comprehensive:
        res = fw.run_comprehensive(args.target or fw.primary_target)
        if args.report:
            with open(args.report, 'w') as f:
                json.dump(res, f, indent=2, default=str)
        if not args.silent and not args.report:
            print(json.dumps(res, indent=2, default=str))
        return

    if args.test:
        from src.modules.test_runner import TestRunner

        test_target = args.target or fw.primary_target
        result = TestRunner(fw).run_test(args.test, test_target)
        if not args.silent:
            print(json.dumps(result, indent=2, default=str))
        return

    fw.run_gui()


if __name__ == '__main__':
    main()
