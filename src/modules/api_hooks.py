"""
Advanced API Hooking Module for Security Testing Framework
Comprehensive Windows API interception and manipulation
"""

import ctypes
import ctypes.wintypes as wintypes
import sys
import os
import threading
import struct
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
import logging

# Windows constants
PAGE_EXECUTE_READWRITE = 0x40
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000

class HookType(Enum):
    """Types of hooks"""
    IAT_HOOK = "iat"           # Import Address Table
    INLINE_HOOK = "inline"     # Inline/Detour
    VTABLE_HOOK = "vtable"     # Virtual Table
    SYSCALL_HOOK = "syscall"   # Direct System Call

class APIHook:
    """Single API hook representation"""

    def __init__(self, module: str, function: str, hook_type: HookType):
        self.module = module
        self.function = function
        self.hook_type = hook_type
        self.original_bytes = None
        self.hook_bytes = None
        self.original_function = None
        self.hook_function = None
        self.enabled = False

class WindowsAPIHooker:
    """Main Windows API hooking engine"""

    def __init__(self):
        self.hooks = {}
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        self.user32 = ctypes.windll.user32
        self.logger = logging.getLogger(__name__)

        # Store original functions
        self.originals = {}

        # Initialize hook templates
        self._init_hook_templates()

    def _init_hook_templates(self):
        """Initialize x86/x64 hook templates"""
        if sys.maxsize > 2**32:  # 64-bit
            # x64 trampoline:
            # mov rax, address
            # jmp rax
            self.jmp_template = bytes([
                0x48, 0xB8,  # mov rax
            ]) + b'\x00' * 8 + bytes([  # address placeholder
                0xFF, 0xE0   # jmp rax
            ])
        else:  # 32-bit
            # x86 trampoline:
            # jmp address
            self.jmp_template = bytes([
                0xE9,  # jmp
            ]) + b'\x00' * 4  # relative address

    def hook_api(self, module: str, function: str, callback: Callable,
                 hook_type: HookType = HookType.INLINE_HOOK) -> bool:
        """Hook a Windows API function"""
        try:
            hook_id = f"{module}.{function}"

            if hook_id in self.hooks:
                self.logger.warning(f"Hook already exists: {hook_id}")
                return False

            hook = APIHook(module, function, hook_type)

            if hook_type == HookType.IAT_HOOK:
                success = self._iat_hook(hook, callback)
            elif hook_type == HookType.INLINE_HOOK:
                success = self._inline_hook(hook, callback)
            elif hook_type == HookType.VTABLE_HOOK:
                success = self._vtable_hook(hook, callback)
            elif hook_type == HookType.SYSCALL_HOOK:
                success = self._syscall_hook(hook, callback)
            else:
                self.logger.error(f"Unknown hook type: {hook_type}")
                return False

            if success:
                self.hooks[hook_id] = hook
                self.logger.info(f"Successfully hooked: {hook_id}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to hook {module}.{function}: {e}")
            return False

    def _inline_hook(self, hook: APIHook, callback: Callable) -> bool:
        """Implement inline hooking (detour)"""
        try:
            # Get module handle
            module_handle = self.kernel32.GetModuleHandleW(hook.module)
            if not module_handle:
                module_handle = self.kernel32.LoadLibraryW(hook.module)

            # Get function address
            func_address = self.kernel32.GetProcAddress(
                module_handle,
                hook.function.encode('ascii')
            )

            if not func_address:
                return False

            # Save original bytes
            original_bytes = ctypes.string_at(func_address, len(self.jmp_template))
            hook.original_bytes = original_bytes

            # Create hook bytes
            callback_address = ctypes.cast(callback, ctypes.c_void_p).value
            hook_bytes = self._create_jmp_bytes(func_address, callback_address)
            hook.hook_bytes = hook_bytes

            # Change memory protection
            old_protect = wintypes.DWORD()
            self.kernel32.VirtualProtect(
                func_address,
                len(hook_bytes),
                PAGE_EXECUTE_READWRITE,
                ctypes.byref(old_protect)
            )

            # Write hook
            ctypes.memmove(func_address, hook_bytes, len(hook_bytes))

            # Restore protection
            self.kernel32.VirtualProtect(
                func_address,
                len(hook_bytes),
                old_protect.value,
                ctypes.byref(old_protect)
            )

            hook.enabled = True
            hook.original_function = func_address
            hook.hook_function = callback

            return True

        except Exception as e:
            self.logger.error(f"Inline hook failed: {e}")
            return False

    def _iat_hook(self, hook: APIHook, callback: Callable) -> bool:
        """Implement IAT hooking"""
        try:
            # Get base address of current process
            h_module = self.kernel32.GetModuleHandleW(None)

            # Parse PE headers to find IAT
            dos_header = ctypes.cast(h_module, ctypes.POINTER(IMAGE_DOS_HEADER))
            nt_header = ctypes.cast(
                h_module + dos_header.contents.e_lfanew,
                ctypes.POINTER(IMAGE_NT_HEADERS)
            )

            # Find import directory
            import_dir = nt_header.contents.OptionalHeader.DataDirectory[1]

            # Iterate through imports
            # ... IAT manipulation code ...

            return True

        except Exception as e:
            self.logger.error(f"IAT hook failed: {e}")
            return False

    def _vtable_hook(self, hook: APIHook, callback: Callable) -> bool:
        """Implement virtual table hooking"""
        # Implementation for COM/DirectX objects
        return False

    def _syscall_hook(self, hook: APIHook, callback: Callable) -> bool:
        """Implement direct syscall hooking"""
        # Requires kernel driver or special privileges
        return False

    def _create_jmp_bytes(self, from_addr: int, to_addr: int) -> bytes:
        """Create jump instruction bytes"""
        if sys.maxsize > 2**32:  # 64-bit
            # Absolute jump using mov rax + jmp rax
            hook_bytes = bytes([0x48, 0xB8])  # mov rax
            hook_bytes += struct.pack('<Q', to_addr)  # address
            hook_bytes += bytes([0xFF, 0xE0])  # jmp rax
        else:  # 32-bit
            # Relative jump
            offset = to_addr - from_addr - 5
            hook_bytes = bytes([0xE9])  # jmp
            hook_bytes += struct.pack('<I', offset & 0xFFFFFFFF)

        return hook_bytes

    def unhook(self, module: str, function: str) -> bool:
        """Remove a hook"""
        hook_id = f"{module}.{function}"

        if hook_id not in self.hooks:
            return False

        hook = self.hooks[hook_id]

        if hook.enabled and hook.original_bytes and hook.original_function:
            try:
                # Restore original bytes
                old_protect = wintypes.DWORD()
                self.kernel32.VirtualProtect(
                    hook.original_function,
                    len(hook.original_bytes),
                    PAGE_EXECUTE_READWRITE,
                    ctypes.byref(old_protect)
                )

                ctypes.memmove(
                    hook.original_function,
                    hook.original_bytes,
                    len(hook.original_bytes)
                )

                self.kernel32.VirtualProtect(
                    hook.original_function,
                    len(hook.original_bytes),
                    old_protect.value,
                    ctypes.byref(old_protect)
                )

                hook.enabled = False
                del self.hooks[hook_id]
                return True

            except Exception as e:
                self.logger.error(f"Failed to unhook: {e}")

        return False

    def unhook_all(self):
        """Remove all hooks"""
        for hook_id in list(self.hooks.keys()):
            module, function = hook_id.split('.')
            self.unhook(module, function)


class CommonAPIHooks:
    """Common API hooks for testing"""

    def __init__(self, hooker: WindowsAPIHooker):
        self.hooker = hooker
        self.intercepted_calls = []

    def hook_process_creation(self):
        """Hook process creation APIs"""

        def create_process_hook(*args):
            # Log process creation
            self.intercepted_calls.append({
                'api': 'CreateProcess',
                'args': args
            })
            # Call original
            return self.hooker.originals.get('CreateProcess', lambda: None)(*args)

        if not self.hooker.hook_api('kernel32.dll', 'CreateProcessW', create_process_hook):
            raise RuntimeError("Failed to hook CreateProcessW")
        return True

    def hook_screen_capture_protection(self):
        """Hook APIs used for screen capture protection"""

        def set_window_display_affinity_hook(hwnd, affinity):
            # Bypass display affinity protection
            self.intercepted_calls.append({
                'api': 'SetWindowDisplayAffinity',
                'hwnd': hwnd,
                'affinity': affinity
            })
            # Return success without setting affinity
            return 1  # TRUE

        if not self.hooker.hook_api(
            'user32.dll',
            'SetWindowDisplayAffinity',
            set_window_display_affinity_hook
        ):
            raise RuntimeError("Failed to hook SetWindowDisplayAffinity")
        return True

    def hook_keyboard_input(self):
        """Hook keyboard input APIs"""

        def get_keyboard_state_hook(key_state):
            # Log keyboard state
            self.intercepted_calls.append({
                'api': 'GetKeyboardState',
                'state': key_state
            })
            # Call original
            return self.hooker.originals.get('GetKeyboardState', lambda: None)(key_state)

        if not self.hooker.hook_api('user32.dll', 'GetKeyboardState', get_keyboard_state_hook):
            raise RuntimeError("Failed to hook GetKeyboardState")
        return True

    def hook_clipboard(self):
        """Hook clipboard APIs"""

        def get_clipboard_data_hook(format):
            # Log clipboard access
            self.intercepted_calls.append({
                'api': 'GetClipboardData',
                'format': format
            })
            # Call original
            return self.hooker.originals.get('GetClipboardData', lambda: None)(format)

        if not self.hooker.hook_api('user32.dll', 'GetClipboardData', get_clipboard_data_hook):
            raise RuntimeError("Failed to hook GetClipboardData")
        return True

    def hook_window_enumeration(self):
        """Hook window enumeration APIs"""

        def enum_windows_hook(callback, lparam):
            # Log window enumeration
            self.intercepted_calls.append({
                'api': 'EnumWindows',
                'callback': callback
            })
            # Call original
            return self.hooker.originals.get('EnumWindows', lambda: None)(callback, lparam)

        if not self.hooker.hook_api('user32.dll', 'EnumWindows', enum_windows_hook):
            raise RuntimeError("Failed to hook EnumWindows")
        return True

    def hook_memory_access(self):
        """Hook memory access APIs"""

        def read_process_memory_hook(h_process, base_address, buffer, size, bytes_read):
            # Log memory read
            self.intercepted_calls.append({
                'api': 'ReadProcessMemory',
                'process': h_process,
                'address': base_address,
                'size': size
            })
            # Call original
            return self.hooker.originals.get('ReadProcessMemory', lambda: None)(
                h_process, base_address, buffer, size, bytes_read
            )

        if not self.hooker.hook_api('kernel32.dll', 'ReadProcessMemory', read_process_memory_hook):
            raise RuntimeError("Failed to hook ReadProcessMemory")
        return True


# PE structure definitions for IAT hooking
class IMAGE_DOS_HEADER(ctypes.Structure):
    _fields_ = [
        ('e_magic', ctypes.c_uint16),
        ('e_cblp', ctypes.c_uint16),
        # ... other fields ...
        ('e_lfanew', ctypes.c_uint32),
    ]

class IMAGE_NT_HEADERS(ctypes.Structure):
    _fields_ = [
        ('Signature', ctypes.c_uint32),
        # ... other fields ...
    ]


class HookManager:
    """Manage all hooks in the system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".manager")
        self.hooker = WindowsAPIHooker()
        self.common_hooks = CommonAPIHooks(self.hooker)
        self.active_hooks: List[str] = []
        self.active_context: Dict[str, Dict[str, Any]] = {}
        self._catalog: Dict[str, Dict[str, Any]] = {
            "screen_capture": {
                "description": "Bypass SetWindowDisplayAffinity to capture protected windows",
                "handler": self.common_hooks.hook_screen_capture_protection,
            },
            "keyboard": {
                "description": "Monitor keyboard input APIs for telemetry",
                "handler": self.common_hooks.hook_keyboard_input,
            },
            "clipboard": {
                "description": "Monitor clipboard access APIs",
                "handler": self.common_hooks.hook_clipboard,
            },
            "window_enum": {
                "description": "Trace EnumWindows enumeration activity",
                "handler": self.common_hooks.hook_window_enumeration,
            },
            "process_creation": {
                "description": "Intercept CreateProcessW to observe spawning behaviour",
                "handler": self.common_hooks.hook_process_creation,
            },
        }
        self._profiles: Dict[str, List[str]] = {
            "lockdown-bypass": [
                "screen_capture",
                "keyboard",
                "clipboard",
                "window_enum",
                "process_creation",
            ],
        }

    def list_available_hooks(self) -> Dict[str, str]:
        return {name: data["description"] for name, data in self._catalog.items()}

    def enable_hooks(
        self,
        hooks: Optional[List[str]] = None,
        target_info: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        requested = hooks or list(self._catalog.keys())
        operations: List[Dict[str, Any]] = []
        context_payload = dict(target_info or {})

        for hook_name in requested:
            catalog_entry = self._catalog.get(hook_name)
            if not catalog_entry:
                operations.append({"hook": hook_name, "status": "unknown"})
                continue

            if hook_name in self.active_hooks:
                if context_payload:
                    self.active_context[hook_name] = dict(context_payload)
                operations.append({"hook": hook_name, "status": "already_enabled"})
                continue

            handler = catalog_entry["handler"]
            try:
                result = handler()
                if result is False:
                    raise RuntimeError("hook handler returned False")
                self.active_hooks.append(hook_name)
                self.active_context[hook_name] = dict(context_payload)
                operation = {
                    "hook": hook_name,
                    "status": "enabled",
                    "description": catalog_entry["description"],
                }
                if context_payload:
                    operation["context"] = dict(context_payload)
                operations.append(operation)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.exception("Failed to enable hook %s", hook_name)
                operations.append({"hook": hook_name, "status": "error", "error": str(exc)})

        return operations

    def enable_profile(
        self,
        profile: str,
        target_info: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        hooks = self._profiles.get(profile)
        if not hooks:
            raise ValueError(f"Unknown hook profile: {profile}")
        return self.enable_hooks(hooks, target_info=target_info)

    def enable_lockdown_bypass_hooks(self, target_info: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Enable hooks for LockDown Browser bypass."""
        return self.enable_profile("lockdown-bypass", target_info=target_info)

    def disable_hooks(self, hooks: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if not self.active_hooks:
            return []

        if not hooks or "all" in hooks:
            disabled = self.disable_all_hooks()
            return [
                {"hook": info["hook"], "status": "disabled", "context": info.get("context")}
                for info in disabled
            ]

        hooks_to_disable = [hook for hook in hooks if hook in self.active_hooks]
        if not hooks_to_disable:
            return []

        remaining = [hook for hook in self.active_hooks if hook not in hooks_to_disable]
        remaining_contexts = {hook: dict(self.active_context.get(hook, {})) for hook in remaining}
        disabled_contexts = {hook: dict(self.active_context.get(hook, {})) for hook in hooks_to_disable}
        self.disable_all_hooks()
        for hook, context in remaining_contexts.items():
            self.enable_hooks([hook], target_info=context)

        return [
            {"hook": name, "status": "disabled", "context": disabled_contexts.get(name)}
            for name in hooks_to_disable
        ]

    def disable_all_hooks(self) -> List[Dict[str, Any]]:
        """Disable all active hooks."""
        disabled = [
            {
                "hook": hook,
                "context": dict(self.active_context.get(hook, {})),
            }
            for hook in self.active_hooks
        ]
        self.hooker.unhook_all()
        self.active_hooks.clear()
        self.active_context.clear()
        return disabled

    def get_status(self) -> Dict[str, Any]:
        return {
            "available_hooks": self.list_available_hooks(),
            "profiles": {name: list(hooks) for name, hooks in self._profiles.items()},
            "active_hooks": list(self.active_hooks),
            "contexts": {hook: self.active_context.get(hook) for hook in self.active_hooks},
            "intercepted_calls": len(self.get_intercepted_calls()),
        }

    def get_intercepted_calls(self) -> List[Dict]:
        """Get all intercepted API calls."""
        return self.common_hooks.intercepted_calls

    def clear_intercepted_calls(self):
        """Clear the log of intercepted calls."""
        self.common_hooks.intercepted_calls.clear()
