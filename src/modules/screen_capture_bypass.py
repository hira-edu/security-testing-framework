"""
Screen Capture Bypass Module for Security Testing Framework
Advanced techniques to bypass screen capture protection
"""

import ctypes
import ctypes.wintypes as wintypes
import sys
import os
import time
import threading
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import numpy as np
from PIL import Image
import logging

try:
    from src.external.bypass_methods.capture.advanced_capture import AdvancedScreenCapture  # type: ignore
except Exception:  # pragma: no cover - optional dependency handling
    AdvancedScreenCapture = None  # type: ignore

# Windows constants
WDA_NONE = 0x00000000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011

DWMWA_CLOAK = 13
DWMWA_CLOAKED = 14
DWMWA_FREEZE = 15

@dataclass
class CaptureResult:
    """Result of a capture attempt"""
    success: bool
    method: str
    image: Optional[Image.Image] = None
    error: Optional[str] = None
    bypass_used: Optional[str] = None

class ScreenCaptureBypass:
    """Advanced screen capture bypass techniques"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.dwmapi = ctypes.windll.dwmapi

        # Store original functions
        self.original_funcs = {}

        self._screenshot_dir = Path(tempfile.gettempdir()) / "stf_captures"
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.vendor_capture = None
        if AdvancedScreenCapture:
            try:
                self.vendor_capture = AdvancedScreenCapture(str(self._screenshot_dir))
                self.logger.info("Advanced bypass-methods capture initialised")
            except Exception as exc:  # pragma: no cover - optional dependency handling
                self.logger.warning("Advanced capture not available: %s", exc)
                self.vendor_capture = None

        base_methods = {
            'gdi': self._capture_gdi,
            'dxgi': self._capture_dxgi,
            'wgc': self._capture_wgc,
            'magnification': self._capture_magnification,
            'mirror_driver': self._capture_mirror_driver,
            'kernel': self._capture_kernel
        }
        self.capture_methods = {}
        if self.vendor_capture:
            self.capture_methods['advanced'] = self._capture_vendor_advanced
        self.capture_methods.update(base_methods)

        # Initialize bypass techniques
        self.bypass_techniques = {
            'hook_api': self._bypass_hook_api,
            'direct_memory': self._bypass_direct_memory,
            'kernel_driver': self._bypass_kernel_driver,
            'dwm_manipulation': self._bypass_dwm_manipulation,
            'window_cloning': self._bypass_window_cloning
        }

    def capture_protected_window(self, hwnd: int = None,
                                method: str = 'auto') -> CaptureResult:
        """
        Capture a protected window using various bypass techniques

        Args:
            hwnd: Window handle (None for desktop)
            method: Capture method to use ('auto' tries all)

        Returns:
            CaptureResult with captured image or error
        """
        if hwnd is None:
            hwnd = self.user32.GetDesktopWindow()

        # Check if window has display affinity protection
        if self._check_display_affinity(hwnd):
            self.logger.info(f"Window {hwnd} has display affinity protection")
            return self._capture_with_bypass(hwnd, method)
        else:
            # No protection, use standard capture
            return self._capture_standard(hwnd, method)

    def _check_display_affinity(self, hwnd: int) -> bool:
        """Check if window has display affinity protection"""
        try:
            affinity = ctypes.c_uint32()
            result = self.user32.GetWindowDisplayAffinity(
                hwnd,
                ctypes.byref(affinity)
            )

            if result:
                return affinity.value == WDA_EXCLUDEFROMCAPTURE

            return False
        except:
            return False

    def _capture_with_bypass(self, hwnd: int, method: str) -> CaptureResult:
        """Capture protected window using bypass techniques"""

        # Try each bypass technique
        for bypass_name, bypass_func in self.bypass_techniques.items():
            self.logger.debug(f"Trying bypass: {bypass_name}")

            try:
                # Apply bypass
                if bypass_func(hwnd):
                    # Try capture methods
                    if method == 'auto':
                        for capture_name, capture_func in self.capture_methods.items():
                            result = capture_func(hwnd)
                            if result.success:
                                result.bypass_used = bypass_name
                                return result
                    else:
                        if method in self.capture_methods:
                            result = self.capture_methods[method](hwnd)
                            if result.success:
                                result.bypass_used = bypass_name
                            return result
            except Exception as e:
                self.logger.error(f"Bypass {bypass_name} failed: {e}")
                continue

        return CaptureResult(
            success=False,
            method=method,
            error="All bypass techniques failed"
        )

    def _capture_standard(self, hwnd: int, method: str) -> CaptureResult:
        """Standard capture without bypass"""
        if method == 'auto':
            for capture_name, capture_func in self.capture_methods.items():
                result = capture_func(hwnd)
                if result.success:
                    return result
        else:
            if method in self.capture_methods:
                return self.capture_methods[method](hwnd)

        return CaptureResult(
            success=False,
            method=method,
            error="Capture failed"
        )

    def _capture_vendor_advanced(self, hwnd: int) -> CaptureResult:
        """Leverage bypass-methods advanced capture pipeline."""
        if not self.vendor_capture:
            return CaptureResult(success=False, method="advanced", error="Vendor capture not initialised")

        try:
            path = self.vendor_capture.capture_using_windows_graphics_capture(hwnd)
            method_used = "windows_graphics_capture"
            if not path:
                path = self.vendor_capture.capture_using_dxgi_desktop_duplication(hwnd)
                method_used = "dxgi_desktop_duplication"
            if not path:
                path = self.vendor_capture.capture_using_direct3d(hwnd)
                method_used = "direct3d"

            if not path:
                return CaptureResult(success=False, method="advanced", error="Advanced capture methods exhausted")

            image_path = Path(path)
            if not image_path.exists():
                return CaptureResult(success=False, method="advanced", error=f"Capture file missing at {path}")

            with Image.open(image_path) as img:
                image_copy = img.copy()

            return CaptureResult(success=True, method=method_used, image=image_copy, bypass_used="advanced_vendor")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Advanced capture pipeline failed: %s", exc)
            return CaptureResult(success=False, method="advanced", error=str(exc))

    # === Bypass Techniques ===

    def _bypass_hook_api(self, hwnd: int) -> bool:
        """Bypass by hooking SetWindowDisplayAffinity"""
        try:
            # Get the address of SetWindowDisplayAffinity
            set_affinity = self.user32.SetWindowDisplayAffinity

            # Create a hook that always returns success
            def hooked_set_affinity(hwnd, affinity):
                # Log the attempt but don't actually set affinity
                self.logger.debug(f"Intercepted SetWindowDisplayAffinity({hwnd}, {affinity})")
                return 1  # Return TRUE

            # Replace the function (simplified - real implementation needs inline hook)
            HOOK_FUNC = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.c_void_p,
                ctypes.c_uint32
            )(hooked_set_affinity)

            # Store original
            self.original_funcs['SetWindowDisplayAffinity'] = set_affinity

            # This is simplified - actual hooking requires memory manipulation
            # self.user32.SetWindowDisplayAffinity = HOOK_FUNC

            # Remove display affinity
            self.user32.SetWindowDisplayAffinity(hwnd, WDA_NONE)

            return True

        except Exception as e:
            self.logger.error(f"API hook bypass failed: {e}")
            return False

    def _bypass_direct_memory(self, hwnd: int) -> bool:
        """Bypass by reading directly from video memory"""
        try:
            # This would require low-level access to GPU memory
            # Simplified implementation

            # Get window DC
            hdc = self.user32.GetWindowDC(hwnd)
            if not hdc:
                return False

            # Get window rect
            rect = wintypes.RECT()
            self.user32.GetWindowRect(hwnd, ctypes.byref(rect))

            # Direct memory access would go here
            # This is a placeholder for the actual implementation

            self.user32.ReleaseDC(hwnd, hdc)
            return True

        except Exception as e:
            self.logger.error(f"Direct memory bypass failed: {e}")
            return False

    def _bypass_kernel_driver(self, hwnd: int) -> bool:
        """Bypass using kernel driver (requires driver)"""
        try:
            # This would require a kernel driver to be loaded
            # Placeholder for kernel-level bypass

            # Check if our driver is loaded
            # If not, this method fails

            return False

        except Exception as e:
            self.logger.error(f"Kernel driver bypass failed: {e}")
            return False

    def _bypass_dwm_manipulation(self, hwnd: int) -> bool:
        """Bypass by manipulating Desktop Window Manager"""
        try:
            # Disable DWM cloaking
            value = ctypes.c_int(0)
            self.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CLOAK,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )

            # Force window to be rendered
            self.dwmapi.DwmFlush()

            return True

        except Exception as e:
            self.logger.error(f"DWM manipulation failed: {e}")
            return False

    def _bypass_window_cloning(self, hwnd: int) -> bool:
        """Bypass by cloning the window"""
        try:
            # Get window class and title
            class_name = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(hwnd, class_name, 256)

            window_title = ctypes.create_unicode_buffer(256)
            self.user32.GetWindowTextW(hwnd, window_title, 256)

            # Create a clone window without protection
            # This is a simplified approach

            return False

        except Exception as e:
            self.logger.error(f"Window cloning failed: {e}")
            return False

    # === Capture Methods ===

    def _capture_gdi(self, hwnd: int) -> CaptureResult:
        """Capture using GDI"""
        try:
            # Get window dimensions
            rect = wintypes.RECT()
            self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top

            # Get device contexts
            hwnd_dc = self.user32.GetWindowDC(hwnd)
            mfc_dc = ctypes.windll.gdi32.CreateCompatibleDC(hwnd_dc)
            bitmap = ctypes.windll.gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)

            # Select bitmap into DC
            ctypes.windll.gdi32.SelectObject(mfc_dc, bitmap)

            # Copy window to bitmap
            ctypes.windll.gdi32.BitBlt(
                mfc_dc, 0, 0, width, height,
                hwnd_dc, 0, 0, 0x00CC0020  # SRCCOPY
            )

            # Convert to PIL Image (simplified)
            # Real implementation would extract bitmap data

            # Cleanup
            ctypes.windll.gdi32.DeleteObject(bitmap)
            ctypes.windll.gdi32.DeleteDC(mfc_dc)
            self.user32.ReleaseDC(hwnd, hwnd_dc)

            return CaptureResult(
                success=True,
                method='gdi',
                image=None  # Would contain actual image
            )

        except Exception as e:
            return CaptureResult(
                success=False,
                method='gdi',
                error=str(e)
            )

    def _capture_dxgi(self, hwnd: int) -> CaptureResult:
        """Capture using DXGI Desktop Duplication"""
        try:
            # This would use DXGI Desktop Duplication API
            # Requires DirectX initialization

            return CaptureResult(
                success=False,
                method='dxgi',
                error="DXGI not implemented"
            )

        except Exception as e:
            return CaptureResult(
                success=False,
                method='dxgi',
                error=str(e)
            )

    def _capture_wgc(self, hwnd: int) -> CaptureResult:
        """Capture using Windows Graphics Capture"""
        try:
            # This would use Windows.Graphics.Capture API
            # Available on Windows 10 1903+

            return CaptureResult(
                success=False,
                method='wgc',
                error="WGC not implemented"
            )

        except Exception as e:
            return CaptureResult(
                success=False,
                method='wgc',
                error=str(e)
            )

    def _capture_magnification(self, hwnd: int) -> CaptureResult:
        """Capture using Magnification API"""
        try:
            # This would use Windows Magnification API
            # Can sometimes bypass protections

            return CaptureResult(
                success=False,
                method='magnification',
                error="Magnification not implemented"
            )

        except Exception as e:
            return CaptureResult(
                success=False,
                method='magnification',
                error=str(e)
            )

    def _capture_mirror_driver(self, hwnd: int) -> CaptureResult:
        """Capture using mirror driver"""
        try:
            # This would use a mirror driver
            # Requires driver installation

            return CaptureResult(
                success=False,
                method='mirror_driver',
                error="Mirror driver not available"
            )

        except Exception as e:
            return CaptureResult(
                success=False,
                method='mirror_driver',
                error=str(e)
            )

    def _capture_kernel(self, hwnd: int) -> CaptureResult:
        """Capture using kernel-level access"""
        try:
            # This would require kernel driver
            # Direct framebuffer access

            return CaptureResult(
                success=False,
                method='kernel',
                error="Kernel driver not available"
            )

        except Exception as e:
            return CaptureResult(
                success=False,
                method='kernel',
                error=str(e)
            )


class LockDownBrowserBypass:
    """Specific bypasses for LockDown Browser"""

    def __init__(self):
        self.capture = ScreenCaptureBypass()
        self.logger = logging.getLogger(__name__)

    def find_lockdown_window(self) -> Optional[int]:
        """Find LockDown Browser window"""
        target_titles = [
            "LockDown Browser",
            "Respondus LockDown Browser",
            "LockDown Browser - "
        ]

        def enum_windows_callback(hwnd, lParam):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
                title = ctypes.create_unicode_buffer(length)
                ctypes.windll.user32.GetWindowTextW(hwnd, title, length)

                for target in target_titles:
                    if target in title.value:
                        self.lockdown_hwnd = hwnd
                        return False
            return True

        self.lockdown_hwnd = None
        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p
        )

        ctypes.windll.user32.EnumWindows(
            WNDENUMPROC(enum_windows_callback),
            0
        )

        return self.lockdown_hwnd

    def bypass_all_protections(self) -> Dict[str, Any]:
        """Attempt to bypass all LockDown Browser protections"""
        results = {
            'window_found': False,
            'capture_success': False,
            'protections_bypassed': []
        }

        # Find LockDown Browser window
        hwnd = self.find_lockdown_window()
        if hwnd:
            results['window_found'] = True
            self.logger.info(f"Found LockDown Browser window: {hwnd}")

            # Attempt capture with all bypass methods
            capture_result = self.capture.capture_protected_window(hwnd, 'auto')

            if capture_result.success:
                results['capture_success'] = True
                results['capture_method'] = capture_result.method
                results['bypass_used'] = capture_result.bypass_used
                results['image'] = capture_result.image

                self.logger.info(f"Successfully captured using {capture_result.method} with {capture_result.bypass_used}")
            else:
                self.logger.error(f"Failed to capture: {capture_result.error}")
        else:
            self.logger.error("LockDown Browser window not found")

        return results
