"""
Advanced Configuration System for Security Testing Framework
Comprehensive configuration for all testing capabilities
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import yaml

class TestMode(Enum):
    """Testing operation modes"""
    PASSIVE = "passive"          # Monitoring only
    ACTIVE = "active"            # Active testing
    AGGRESSIVE = "aggressive"    # Full bypass attempts
    STEALTH = "stealth"          # Stealth mode testing
    CUSTOM = "custom"            # Custom configuration

class HookingMethod(Enum):
    """API hooking methods"""
    IAT_HOOK = "iat_hook"              # Import Address Table
    INLINE_HOOK = "inline_hook"        # Inline/Detour hooking
    VTABLE_HOOK = "vtable_hook"        # Virtual table hooking
    SYSCALL_HOOK = "syscall_hook"      # Direct syscall hooking
    KERNEL_HOOK = "kernel_hook"        # Kernel-level hooking

@dataclass
class DirectXConfig:
    """DirectX hooking configuration"""
    enabled: bool = True
    version: str = "auto"  # auto, dx11, dx12
    capture_method: str = "staging_texture"
    capture_interval_ms: int = 100

    # Hooking options
    hook_present: bool = True
    hook_resize_buffers: bool = True
    hook_create_device: bool = True

    # Frame extraction
    extract_frames: bool = True
    frame_format: str = "rgba"
    compression: bool = False

    # Performance
    use_gpu_acceleration: bool = True
    async_capture: bool = True
    buffer_count: int = 3

@dataclass
class WindowsAPIConfig:
    """Windows API hooking configuration"""
    enabled: bool = True

    # Process hooks
    hook_create_process: bool = True
    hook_terminate_process: bool = True
    hook_open_process: bool = True

    # Window hooks
    hook_create_window: bool = True
    hook_set_window_pos: bool = True
    hook_show_window: bool = True
    hook_get_foreground_window: bool = True

    # Input hooks
    hook_keyboard: bool = True
    hook_mouse: bool = True
    hook_clipboard: bool = False

    # File system hooks
    hook_file_operations: bool = False
    hook_registry: bool = False

    # Network hooks
    hook_network: bool = False

    # Advanced
    bypass_hooks: List[str] = field(default_factory=list)
    protected_processes: List[str] = field(default_factory=list)

@dataclass
class MemoryConfig:
    """Memory manipulation configuration"""
    enabled: bool = True

    # Memory protection
    encrypt_sensitive_data: bool = True
    obfuscate_strings: bool = True
    scramble_memory_layout: bool = False

    # Memory scanning
    pattern_scanning: bool = True
    signature_detection: bool = True

    # Memory manipulation
    allow_read_process_memory: bool = True
    allow_write_process_memory: bool = False
    allow_virtual_protect: bool = True

    # Advanced features
    use_memory_pools: bool = True
    implement_memory_traps: bool = False
    anti_dumping: bool = True

@dataclass
class NetworkConfig:
    """Network configuration"""
    enabled: bool = False

    # Communication
    use_encryption: bool = True
    encryption_algorithm: str = "AES-256-GCM"

    # Proxy settings
    use_proxy: bool = False
    proxy_type: str = "socks5"
    proxy_address: str = ""
    proxy_port: int = 0

    # C2 communication
    c2_enabled: bool = False
    c2_server: str = ""
    c2_port: int = 0
    c2_protocol: str = "https"

    # Stealth communication
    use_dns_tunneling: bool = False
    use_icmp_tunneling: bool = False
    domain_fronting: bool = False

@dataclass
class AntiDetectionConfig:
    """Anti-detection configuration"""
    enabled: bool = True

    # Detection evasion
    evade_antivirus: bool = True
    evade_sandbox: bool = True
    evade_vm: bool = True
    evade_debugger: bool = True
    evade_memory_scanners: bool = True

    # Obfuscation
    code_obfuscation: bool = True
    string_encryption: bool = True
    api_obfuscation: bool = True
    control_flow_obfuscation: bool = True

    # Polymorphism
    polymorphic_code: bool = False
    metamorphic_engine: bool = False

    # Behavioral evasion
    randomize_execution: bool = True
    mimic_legitimate_behavior: bool = True
    implement_sleep_bypass: bool = True

    # Advanced evasion
    use_process_hollowing: bool = False
    use_process_doppelganging: bool = False
    use_atom_bombing: bool = False

@dataclass
class ScreenCaptureConfig:
    """Screen capture configuration"""
    enabled: bool = True

    # Capture methods (priority order)
    methods: List[str] = field(default_factory=lambda: [
        "windows_graphics_capture",
        "dxgi_desktop_duplication",
        "directx_hook",
        "gdi_capture",
        "magnification_api"
    ])

    # Capture settings
    capture_rate_fps: int = 30
    capture_quality: int = 95
    capture_format: str = "png"

    # Target settings
    target_window: str = ""  # Empty for all
    exclude_windows: List[str] = field(default_factory=list)

    # Bypass techniques
    bypass_display_affinity: bool = True
    bypass_dwm_protection: bool = True
    capture_overlays: bool = True

    # Storage
    save_captures: bool = False
    capture_directory: str = "captures"
    max_captures: int = 1000

@dataclass
class InjectionConfig:
    """Code injection configuration"""
    enabled: bool = True

    # Injection methods
    methods: List[str] = field(default_factory=lambda: [
        "SetWindowsHookEx",
        "CreateRemoteThread",
        "NtCreateThreadEx",
        "QueueUserAPC",
        "SetThreadContext"
    ])

    # Injection options
    inject_into_new_processes: bool = True
    inject_into_existing_processes: bool = False

    # Target processes
    target_processes: List[str] = field(default_factory=list)
    exclude_processes: List[str] = field(default_factory=lambda: [
        "System", "csrss.exe", "wininit.exe", "services.exe"
    ])

    # Payload options
    payload_type: str = "dll"  # dll, shellcode, exe
    payload_path: str = ""

    # Advanced techniques
    use_manual_mapping: bool = True
    use_reflective_dll: bool = True
    bypass_process_mitigation: bool = True

@dataclass
class PersistenceConfig:
    """Persistence configuration"""
    enabled: bool = False

    # Persistence methods
    registry_persistence: bool = False
    scheduled_task: bool = False
    service_persistence: bool = False
    wmi_persistence: bool = False

    # Startup options
    startup_folder: bool = False
    run_key: bool = False

    # Advanced persistence
    dll_hijacking: bool = False
    com_hijacking: bool = False

    # Anti-removal
    watchdog_process: bool = False
    self_healing: bool = False

@dataclass
class AdvancedConfiguration:
    """Complete advanced configuration"""
    # Test mode
    mode: TestMode = TestMode.ACTIVE

    # Core components
    directx: DirectXConfig = field(default_factory=DirectXConfig)
    windows_api: WindowsAPIConfig = field(default_factory=WindowsAPIConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    anti_detection: AntiDetectionConfig = field(default_factory=AntiDetectionConfig)
    screen_capture: ScreenCaptureConfig = field(default_factory=ScreenCaptureConfig)
    injection: InjectionConfig = field(default_factory=InjectionConfig)
    persistence: PersistenceConfig = field(default_factory=PersistenceConfig)

    # Global settings
    debug_mode: bool = False
    log_level: str = "INFO"
    log_file: str = "security_test.log"

    # Performance settings
    thread_count: int = 8
    memory_limit_mb: int = 1024
    cpu_limit_percent: int = 50

    # Safety settings
    safe_mode: bool = True
    require_confirmation: bool = True
    auto_cleanup: bool = True

    # Target information
    target_process: str = "LockDownBrowser.exe"
    target_window_title: str = ""

    def to_json(self) -> str:
        """Convert configuration to JSON"""
        return json.dumps(asdict(self), indent=4)

    def to_yaml(self) -> str:
        """Convert configuration to YAML"""
        return yaml.dump(asdict(self), default_flow_style=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'AdvancedConfiguration':
        """Load configuration from JSON"""
        data = json.loads(json_str)
        return cls._from_dict(data)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'AdvancedConfiguration':
        """Load configuration from YAML"""
        data = yaml.safe_load(yaml_str)
        return cls._from_dict(data)

    @classmethod
    def from_file(cls, file_path: str) -> 'AdvancedConfiguration':
        """Load configuration from file"""
        with open(file_path, 'r') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                return cls.from_yaml(f.read())
            else:
                return cls.from_json(f.read())

    def save(self, file_path: str):
        """Save configuration to file"""
        with open(file_path, 'w') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                f.write(self.to_yaml())
            else:
                f.write(self.to_json())

    @classmethod
    def _from_dict(cls, data: Dict) -> 'AdvancedConfiguration':
        """Create configuration from dictionary"""
        config = cls()

        # Parse mode
        if 'mode' in data:
            config.mode = TestMode(data['mode'])

        # Parse components
        if 'directx' in data:
            config.directx = DirectXConfig(**data['directx'])
        if 'windows_api' in data:
            config.windows_api = WindowsAPIConfig(**data['windows_api'])
        if 'memory' in data:
            config.memory = MemoryConfig(**data['memory'])
        if 'network' in data:
            config.network = NetworkConfig(**data['network'])
        if 'anti_detection' in data:
            config.anti_detection = AntiDetectionConfig(**data['anti_detection'])
        if 'screen_capture' in data:
            config.screen_capture = ScreenCaptureConfig(**data['screen_capture'])
        if 'injection' in data:
            config.injection = InjectionConfig(**data['injection'])
        if 'persistence' in data:
            config.persistence = PersistenceConfig(**data['persistence'])

        # Parse global settings
        for key in ['debug_mode', 'log_level', 'log_file', 'thread_count',
                    'memory_limit_mb', 'cpu_limit_percent', 'safe_mode',
                    'require_confirmation', 'auto_cleanup', 'target_process',
                    'target_window_title']:
            if key in data:
                setattr(config, key, data[key])

        return config


# Preset configurations for common scenarios
class ConfigPresets:
    """Preset configurations for different testing scenarios"""

    @staticmethod
    def passive_monitoring() -> AdvancedConfiguration:
        """Configuration for passive monitoring only"""
        config = AdvancedConfiguration()
        config.mode = TestMode.PASSIVE
        config.injection.enabled = False
        config.memory.allow_write_process_memory = False
        config.persistence.enabled = False
        return config

    @staticmethod
    def full_stealth() -> AdvancedConfiguration:
        """Maximum stealth configuration"""
        config = AdvancedConfiguration()
        config.mode = TestMode.STEALTH

        # Enable all anti-detection
        config.anti_detection.enabled = True
        config.anti_detection.evade_antivirus = True
        config.anti_detection.evade_sandbox = True
        config.anti_detection.evade_vm = True
        config.anti_detection.evade_debugger = True
        config.anti_detection.code_obfuscation = True
        config.anti_detection.polymorphic_code = True
        config.anti_detection.randomize_execution = True

        # Use stealthy injection
        config.injection.use_manual_mapping = True
        config.injection.use_reflective_dll = True

        # Encrypt everything
        config.memory.encrypt_sensitive_data = True
        config.network.use_encryption = True

        return config

    @staticmethod
    def aggressive_testing() -> AdvancedConfiguration:
        """Aggressive testing configuration"""
        config = AdvancedConfiguration()
        config.mode = TestMode.AGGRESSIVE

        # Enable all features
        config.directx.enabled = True
        config.windows_api.enabled = True
        config.memory.enabled = True
        config.screen_capture.enabled = True
        config.injection.enabled = True

        # Use all capture methods
        config.screen_capture.bypass_display_affinity = True
        config.screen_capture.bypass_dwm_protection = True

        # Enable all hooks
        config.windows_api.hook_create_process = True
        config.windows_api.hook_keyboard = True
        config.windows_api.hook_mouse = True

        return config

    @staticmethod
    def lockdown_browser_test() -> AdvancedConfiguration:
        """Specific configuration for LockDown Browser testing"""
        config = ConfigPresets.full_stealth()

        # Target LockDown Browser
        config.target_process = "LockDownBrowser.exe"
        config.target_window_title = "LockDown Browser"

        # Enable screen capture bypass
        config.screen_capture.enabled = True
        config.screen_capture.bypass_display_affinity = True
        config.screen_capture.methods = [
            "windows_graphics_capture",
            "dxgi_desktop_duplication",
            "directx_hook"
        ]

        # Hook relevant APIs
        config.windows_api.hook_keyboard = True
        config.windows_api.hook_mouse = True
        config.windows_api.hook_clipboard = True
        config.windows_api.hook_create_window = True

        # Process protection bypass
        config.memory.anti_dumping = False
        config.injection.bypass_process_mitigation = True

        return config