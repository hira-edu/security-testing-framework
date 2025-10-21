#!/usr/bin/env python3
"""
Configuration Manager for UndownUnlock System
Handles configuration file management, validation, and real-time updates
"""

import json
import os
import sys
import time
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class ConfigurationManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.default_config: Dict[str, Any] = {}
        self.watchers: List[callable] = []
        self.file_watcher_thread = None
        self.watching = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize with default configuration
        self.setup_default_config()
        self.load_config()
    
    def setup_default_config(self):
        """Setup default configuration"""
        self.default_config = {
            "capture": {
                "method": "windows_graphics_capture",
                "frame_rate": 60,
                "quality": "high",
                "compression": True,
                "compression_level": 6,
                "hardware_acceleration": True,
                "buffer_size": 10485760,  # 10MB
                "fallback_chain": [
                    "windows_graphics_capture",
                    "dxgi_desktop_duplication",
                    "direct3d_capture",
                    "gdi_capture"
                ]
            },
            "hooks": {
                "directx": {
                    "enabled": True,
                    "versions": ["11", "12"],
                    "interfaces": ["IDXGISwapChain", "ID3D11Device", "ID3D12Device"]
                },
                "windows_api": {
                    "enabled": True,
                    "functions": [
                        "SetForegroundWindow",
                        "GetForegroundWindow",
                        "CreateProcess",
                        "TerminateProcess"
                    ]
                },
                "keyboard": {
                    "enabled": False,
                    "blocked_keys": ["F12", "VK_SNAPSHOT"],
                    "hotkeys": {
                        "ctrl+alt+s": "screenshot",
                        "ctrl+alt+q": "quit"
                    }
                },
                "process": {
                    "enabled": False,
                    "blocked_processes": []
                }
            },
            "performance": {
                "monitoring": True,
                "sampling_interval": 1000,
                "memory_tracking": True,
                "leak_threshold": 1048576,  # 1MB
                "optimization": {
                    "memory_pool": True,
                    "thread_pool": True,
                    "hardware_acceleration": True
                },
                "limits": {
                    "max_cpu_usage": 80.0,
                    "max_memory_usage": 1073741824,  # 1GB
                    "max_frame_rate": 60
                }
            },
            "security": {
                "anti_detection": {
                    "enabled": True,
                    "hook_concealment": True,
                    "timing_normalization": True,
                    "call_stack_spoofing": True
                },
                "obfuscation": {
                    "enabled": False,
                    "string_encryption": True,
                    "function_obfuscation": True,
                    "import_obfuscation": True
                },
                "integrity": {
                    "enabled": True,
                    "code_verification": True,
                    "memory_protection": True,
                    "tamper_detection": True
                }
            },
            "logging": {
                "level": "INFO",
                "file": "undownunlock.log",
                "console_output": True,
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5
            },
            "shared_memory": {
                "name": "UndownUnlock_FrameBuffer",
                "size": 10485760,  # 10MB
                "timeout": 5000,
                "compression": True,
                "encryption": False
            },
            "ui": {
                "theme": "default",
                "window_size": "800x600",
                "auto_start": False,
                "minimize_to_tray": True
            }
        }
    
    def load_config(self, file_path: Optional[str] = None) -> bool:
        """Load configuration from file"""
        try:
            config_path = Path(file_path) if file_path else self.config_file
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with default config
                self.config = self.merge_configs(self.default_config, loaded_config)
                self.logger.info(f"Configuration loaded from {config_path}")
            else:
                # Use default configuration
                self.config = self.default_config.copy()
                self.logger.info("Using default configuration")
            
            # Validate configuration
            if self.validate_config():
                self.notify_watchers()
                return True
            else:
                self.logger.error("Configuration validation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Fallback to default configuration
            self.config = self.default_config.copy()
            return False
    
    def save_config(self, file_path: Optional[str] = None) -> bool:
        """Save configuration to file"""
        try:
            config_path = Path(file_path) if file_path else self.config_file
            
            # Create directory if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user configuration with default configuration"""
        result = default.copy()
        
        def merge_dict(base: Dict[str, Any], override: Dict[str, Any]):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(result, user)
        return result
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        try:
            # Validate capture settings
            capture = self.config.get("capture", {})
            if not isinstance(capture.get("frame_rate"), (int, float)) or capture["frame_rate"] <= 0:
                self.logger.error("Invalid frame rate")
                return False
            
            if capture.get("frame_rate", 0) > 120:
                self.logger.warning("Frame rate exceeds recommended maximum")
            
            # Validate performance settings
            performance = self.config.get("performance", {})
            if not isinstance(performance.get("sampling_interval"), int) or performance["sampling_interval"] <= 0:
                self.logger.error("Invalid sampling interval")
                return False
            
            # Validate logging settings
            logging_config = self.config.get("logging", {})
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
            if logging_config.get("level") not in valid_levels:
                self.logger.error("Invalid log level")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                value = value[k]
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value by key (supports dot notation)"""
        try:
            keys = key.split('.')
            config = self.config
            
            # Navigate to parent of target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            # Validate and notify watchers
            if self.validate_config():
                self.notify_watchers()
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set configuration {key}: {e}")
            return False
    
    def get_capture_config(self) -> Dict[str, Any]:
        """Get capture configuration"""
        return self.config.get("capture", {})
    
    def get_hooks_config(self) -> Dict[str, Any]:
        """Get hooks configuration"""
        return self.config.get("hooks", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.config.get("performance", {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.config.get("security", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get("logging", {})
    
    def update_capture_config(self, updates: Dict[str, Any]) -> bool:
        """Update capture configuration"""
        try:
            capture_config = self.config.get("capture", {})
            capture_config.update(updates)
            self.config["capture"] = capture_config
            
            if self.validate_config():
                self.notify_watchers()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update capture config: {e}")
            return False
    
    def update_hooks_config(self, updates: Dict[str, Any]) -> bool:
        """Update hooks configuration"""
        try:
            hooks_config = self.config.get("hooks", {})
            hooks_config.update(updates)
            self.config["hooks"] = hooks_config
            
            if self.validate_config():
                self.notify_watchers()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update hooks config: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """Reset configuration to default values"""
        try:
            self.config = self.default_config.copy()
            self.notify_watchers()
            self.logger.info("Configuration reset to default")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def add_watcher(self, callback: callable):
        """Add configuration change watcher"""
        if callback not in self.watchers:
            self.watchers.append(callback)
    
    def remove_watcher(self, callback: callable):
        """Remove configuration change watcher"""
        if callback in self.watchers:
            self.watchers.remove(callback)
    
    def notify_watchers(self):
        """Notify all watchers of configuration changes"""
        for watcher in self.watchers:
            try:
                watcher(self.config)
            except Exception as e:
                self.logger.error(f"Watcher notification error: {e}")
    
    def start_file_watching(self):
        """Start watching configuration file for changes"""
        if self.watching:
            return
        
        self.watching = True
        self.file_watcher_thread = threading.Thread(target=self._file_watcher, daemon=True)
        self.file_watcher_thread.start()
        self.logger.info("Configuration file watching started")
    
    def stop_file_watching(self):
        """Stop watching configuration file"""
        self.watching = False
        if self.file_watcher_thread:
            self.file_watcher_thread.join(timeout=1)
        self.logger.info("Configuration file watching stopped")
    
    def _file_watcher(self):
        """File watcher thread"""
        last_modified = 0
        
        while self.watching:
            try:
                if self.config_file.exists():
                    current_modified = self.config_file.stat().st_mtime
                    
                    if current_modified > last_modified:
                        self.logger.info("Configuration file changed, reloading...")
                        self.load_config()
                        last_modified = current_modified
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"File watcher error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuration exported to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from file"""
        try:
            with open(file_path, 'r') as f:
                imported_config = json.load(f)
            
            # Merge with current config
            self.config = self.merge_configs(self.config, imported_config)
            
            if self.validate_config():
                self.notify_watchers()
                self.logger.info(f"Configuration imported from {file_path}")
                return True
            else:
                self.logger.error("Imported configuration validation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "capture_method": self.get_config("capture.method", "unknown"),
            "frame_rate": self.get_config("capture.frame_rate", 0),
            "quality": self.get_config("capture.quality", "unknown"),
            "directx_hooks": self.get_config("hooks.directx.enabled", False),
            "windows_api_hooks": self.get_config("hooks.windows_api.enabled", False),
            "keyboard_hooks": self.get_config("hooks.keyboard.enabled", False),
            "performance_monitoring": self.get_config("performance.monitoring", False),
            "anti_detection": self.get_config("security.anti_detection.enabled", False),
            "obfuscation": self.get_config("security.obfuscation.enabled", False),
            "log_level": self.get_config("logging.level", "INFO")
        }
    
    def validate_section(self, section: str) -> List[str]:
        """Validate specific configuration section and return errors"""
        errors = []
        
        try:
            if section == "capture":
                capture = self.config.get("capture", {})
                if capture.get("frame_rate", 0) <= 0:
                    errors.append("Frame rate must be positive")
                if capture.get("frame_rate", 0) > 120:
                    errors.append("Frame rate exceeds recommended maximum")
                if capture.get("compression_level", 0) < 0 or capture.get("compression_level", 0) > 9:
                    errors.append("Compression level must be between 0 and 9")
            
            elif section == "performance":
                performance = self.config.get("performance", {})
                if performance.get("sampling_interval", 0) <= 0:
                    errors.append("Sampling interval must be positive")
                if performance.get("leak_threshold", 0) <= 0:
                    errors.append("Leak threshold must be positive")
            
            elif section == "logging":
                logging_config = self.config.get("logging", {})
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
                if logging_config.get("level") not in valid_levels:
                    errors.append(f"Log level must be one of: {', '.join(valid_levels)}")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    def get_recommended_config(self, use_case: str) -> Dict[str, Any]:
        """Get recommended configuration for specific use case"""
        recommendations = {
            "gaming": {
                "capture": {
                    "method": "windows_graphics_capture",
                    "frame_rate": 60,
                    "quality": "high",
                    "compression": True,
                    "compression_level": 6
                },
                "performance": {
                    "monitoring": True,
                    "sampling_interval": 1000
                },
                "security": {
                    "anti_detection": {
                        "enabled": True,
                        "hook_concealment": True
                    }
                }
            },
            "monitoring": {
                "capture": {
                    "method": "enhanced_capture",
                    "frame_rate": 30,
                    "quality": "medium",
                    "compression": True,
                    "compression_level": 8
                },
                "performance": {
                    "monitoring": True,
                    "sampling_interval": 500
                },
                "hooks": {
                    "windows_api": {
                        "enabled": True
                    },
                    "process": {
                        "enabled": True
                    }
                }
            },
            "development": {
                "capture": {
                    "method": "windows_graphics_capture",
                    "frame_rate": 30,
                    "quality": "low",
                    "compression": False
                },
                "logging": {
                    "level": "DEBUG",
                    "console_output": True
                },
                "performance": {
                    "monitoring": True,
                    "memory_tracking": True
                }
            }
        }
        
        return recommendations.get(use_case, {})

def main():
    """Test configuration manager"""
    config_manager = ConfigurationManager("test_config.json")
    
    # Test basic operations
    print("Default configuration loaded")
    print(f"Frame rate: {config_manager.get_config('capture.frame_rate')}")
    print(f"Log level: {config_manager.get_config('logging.level')}")
    
    # Test setting configuration
    config_manager.set_config("capture.frame_rate", 30)
    print(f"Updated frame rate: {config_manager.get_config('capture.frame_rate')}")
    
    # Test configuration summary
    summary = config_manager.get_config_summary()
    print("Configuration summary:", summary)
    
    # Test validation
    errors = config_manager.validate_section("capture")
    if errors:
        print("Validation errors:", errors)
    else:
        print("Configuration is valid")
    
    # Save configuration
    config_manager.save_config()
    print("Configuration saved")

if __name__ == "__main__":
    main() 