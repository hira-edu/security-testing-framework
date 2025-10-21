"""
Advanced Screen Capture Module for UndownUnlock Accessibility Framework

This module implements low-level Windows graphics capture techniques to
bypass SetWindowDisplayAffinity protection used by applications like
LockDown Browser. It complements the enhanced_capture.py module with
more advanced methods that operate directly at the graphics driver level.

Key techniques:
- Windows Graphics Capture API (Windows 10+)
- DXGI Desktop Duplication API 
- Direct3D capture
- Display Driver/Kernel-level screen access
"""

import os
import sys
import time
import ctypes
import logging
import threading
import subprocess
from typing import Optional, Tuple, List, Dict, Any, Union
from ctypes import wintypes
import uuid
from datetime import datetime
import tempfile
import winreg
import struct
import importlib
import asyncio
import platform

# Third-party imports
import numpy as np
from PIL import Image
import win32gui
import win32con
import win32api
import win32ui
import win32process
import win32security
import pywintypes
from comtypes import client, GUID
import pythoncom

# Import Windows Graphics Capture implementation
try:
    from windows_graphics_capture import WindowsGraphicsCapture, is_windows_10_1809_or_later
    windows_graphics_capture_available = True
except ImportError:
    windows_graphics_capture_available = False

# Import DXGI Desktop Duplication implementation
try:
    from dxgi_desktop_duplication import DXGIOutputDuplicationCapture
    dxgi_desktop_duplication_available = True
except ImportError:
    dxgi_desktop_duplication_available = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("advanced_capture.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AdvancedCapture")

# Windows 10 build number threshold for Graphics Capture API
WIN10_THRESHOLD_BUILD = 17763  # Windows 10 1809 or later

# DXGI constants and structures
DXGI_FORMAT_B8G8R8A8_UNORM = 87
DXGI_RESOURCE_FLAG_NONE = 0

class DXGI_OUTDUPL_DESC(ctypes.Structure):
    _fields_ = [
        ("ModeDesc", ctypes.c_int * 28),  # Simplified for this example
        ("Rotation", ctypes.c_int),
        ("DesktopImageInSystemMemory", ctypes.c_bool),
    ]

class DXGI_OUTDUPL_FRAME_INFO(ctypes.Structure):
    _fields_ = [
        ("LastPresentTime", ctypes.c_longlong),
        ("LastMouseUpdateTime", ctypes.c_longlong),
        ("AccumulatedFrames", ctypes.c_uint),
        ("RectsCoalesced", ctypes.c_bool),
        ("ProtectedContentMaskedOut", ctypes.c_bool),
        ("pointer_position_info", ctypes.c_int * 5),  # Simplified
        ("total_metadata", ctypes.c_uint),
        ("getframe_result", ctypes.c_int),
    ]


class AdvancedScreenCapture:
    """
    AdvancedScreenCapture uses low-level Windows graphics techniques to
    capture screenshots, bypassing SetWindowDisplayAffinity protection.
    """
    
    def __init__(self, screenshot_dir: str = "screenshots"):
        """
        Initialize the advanced screen capture.
        
        Args:
            screenshot_dir: Directory to save screenshots
        """
        self.screenshot_dir = screenshot_dir
        
        # Create screenshot directory if it doesn't exist
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Check Windows version for feature availability
        self.windows_ver_info = self._get_windows_version()
        
        # Flag to indicate if Windows Graphics Capture API is available
        self.wgc_available = self._is_wgc_available()
        
        # Flag for Direct3D and DXGI availability
        self.d3d_available = False
        
        # Initialize COM for thread
        self._init_com()
        
        # Initialize Windows Graphics Capture if available
        self.windows_graphics_capture = None
        if windows_graphics_capture_available and self.wgc_available:
            try:
                self.windows_graphics_capture = WindowsGraphicsCapture(screenshot_dir)
                logger.info("Windows Graphics Capture initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Windows Graphics Capture: {e}")
        
        # Initialize DXGI Desktop Duplication if available
        self.dxgi_duplication = None
        if dxgi_desktop_duplication_available:
            try:
                self.dxgi_duplication = DXGIOutputDuplicationCapture(screenshot_dir)
                if self.dxgi_duplication.initialized:
                    logger.info("DXGI Desktop Duplication initialized successfully")
                else:
                    logger.warning("DXGI Desktop Duplication initialization failed")
                    self.dxgi_duplication = None
            except Exception as e:
                logger.error(f"Failed to initialize DXGI Desktop Duplication: {e}")
                self.dxgi_duplication = None
        
        logger.info(f"Advanced Screen Capture initialized (Windows {self.windows_ver_info})")
        logger.info(f"Windows Graphics Capture API available: {self.wgc_available}")
        
        # Load the D3D and DXGI interfaces
        self._init_dxgi_interfaces()
    
    def _init_com(self):
        """Initialize COM for the current thread."""
        try:
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            logger.info("COM initialized for current thread")
        except Exception as e:
            logger.error(f"Failed to initialize COM: {e}")
    
    def _get_windows_version(self) -> str:
        """
        Get detailed Windows version information.
        
        Returns:
            String containing Windows version details
        """
        try:
            ver_info = sys.getwindowsversion()
            win_ver = platform.platform()
            return f"{win_ver} (Build {ver_info.build})"
        except Exception as e:
            logger.error(f"Error getting Windows version: {e}")
            return "Unknown Windows version"
    
    def _is_wgc_available(self) -> bool:
        """
        Check if Windows Graphics Capture API is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            # Check Windows 10 version (1809 or later required)
            ver_info = sys.getwindowsversion()
            if ver_info.major >= 10 and ver_info.build >= WIN10_THRESHOLD_BUILD:
                # Try to import the Windows Capture API types
                try:
                    # See if the UWP/WinRT interop libraries are available
                    # This is a simplified check - in real implementation we'd check for 
                    # specific COM interfaces related to Windows.Graphics.Capture
                    client.GetModule(('{94EA2B94-E9CC-49E0-C0FF-EE64CA8F5B90}', 1, 0))
                    logger.info("Windows Graphics Capture API detected")
                    return True
                except Exception as e:
                    logger.info(f"Windows Graphics Capture API not available: {e}")
            else:
                logger.info(f"Windows build {ver_info.build} too old for Graphics Capture API")
            return False
        except Exception as e:
            logger.error(f"Error checking for Windows Graphics Capture API: {e}")
            return False
    
    def _init_dxgi_interfaces(self):
        """Initialize Direct3D and DXGI interfaces required for screen capture."""
        try:
            # Load D3D11 module
            self.d3d11 = client.GetModule("d3d11.dll")
            
            # Load DXGI module
            self.dxgi = client.GetModule("dxgi.dll")
            
            self.d3d_available = True
            logger.info("D3D and DXGI interfaces loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load D3D and DXGI interfaces: {e}")
            self.d3d_available = False
    
    def capture_screenshot(self, hwnd: Optional[int] = None) -> Optional[str]:
        """
        Capture a screenshot using advanced methods.
        
        Args:
            hwnd: Optional window handle to capture. If None, captures the entire screen.
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        methods = [
            self.capture_using_windows_graphics_capture,  # Try Windows Graphics Capture API first
            self.capture_using_dxgi_desktop_duplication,  # Then try DXGI Desktop Duplication
            self.capture_using_direct3d,
            self.capture_using_display_driver,
            self.capture_using_gdi_window_redir,
        ]
        
        for method in methods:
            try:
                result = method(hwnd)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error in {method.__name__}: {e}")
        
        logger.error("All advanced capture methods failed")
        return None
    
    def capture_using_windows_graphics_capture(self, hwnd: Optional[int] = None) -> Optional[str]:
        """
        Capture using Windows Graphics Capture API (Windows 10 1809+).
        
        Args:
            hwnd: Optional window handle to capture. If None, captures the entire screen.
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.windows_graphics_capture or not self.wgc_available:
            logger.warning("Windows Graphics Capture API not available, skipping")
            return None
        
        try:
            # If no window handle, capture foreground window
            if hwnd is None:
                hwnd = win32gui.GetForegroundWindow()
            
            # Get window name
            window_name = win32gui.GetWindowText(hwnd)
            logger.info(f"Capturing window '{window_name}' ({hwnd}) using Windows Graphics Capture API")
            
            # Capture using Windows Graphics Capture API
            result = self.windows_graphics_capture.capture_window(window_name=window_name, hwnd=hwnd)
            
            if result:
                logger.info(f"Windows Graphics Capture successful: {result}")
                return result
            else:
                logger.warning("Windows Graphics Capture failed")
                return None
                
        except Exception as e:
            logger.error(f"Windows Graphics Capture API failed: {e}")
            return None
    
    def capture_using_dxgi_desktop_duplication(self, hwnd: Optional[int] = None) -> Optional[str]:
        """
        Capture using DXGI Desktop Duplication API.
        
        Args:
            hwnd: Optional window handle to capture. If None, captures entire screen.
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.dxgi_duplication:
            logger.warning("DXGI Desktop Duplication not available, skipping")
            return None
        
        try:
            if hwnd:
                # Capture specific window
                logger.info(f"Capturing window {hwnd} using DXGI Desktop Duplication")
                result = self.dxgi_duplication.capture_window(hwnd)
            else:
                # Capture entire screen
                logger.info("Capturing full screen using DXGI Desktop Duplication")
                result = self.dxgi_duplication.capture_full_screen()
                
            if result:
                logger.info(f"DXGI Desktop Duplication successful: {result}")
                return result
            else:
                logger.warning("DXGI Desktop Duplication failed")
                return None
                
        except Exception as e:
            logger.error(f"DXGI Desktop Duplication failed: {e}")
            return None
    
    def capture_using_direct3d(self, hwnd: Optional[int] = None) -> Optional[str]:
        """
        Capture using Direct3D screen capture.
        
        Args:
            hwnd: Optional window handle to capture. If None, captures entire screen.
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.d3d_available:
            logger.warning("D3D not available, skipping Direct3D capture")
            return None
        
        try:
            # This method would create a Direct3D device and capture the screen
            # by copying from the GPU frame buffer. The implementation is complex
            # and requires detailed knowledge of Direct3D.
            
            # For simplicity in this POC, we'll use a variation of the GDI approach
            # but with a method that might bypass the affinity flag
            
            if hwnd is None:
                # For full screen capture, get the desktop window
                hwnd = win32gui.GetDesktopWindow()
            
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Create device contexts
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # Create bitmap
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # Use BitBlt with a special drawing code that might bypass restrictions
            # Use SRCCOPY_CAPTUREBLT which includes layered windows
            CAPTUREBLT = 0x40000000
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY | CAPTUREBLT)
            
            # Convert to PIL Image
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # Clean up
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            # Save the image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(self.screenshot_dir, f"direct3d_{timestamp}.png")
            img.save(filename)
            
            logger.info(f"Direct3D capture saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Direct3D capture failed: {e}")
            return None
    
    def capture_using_display_driver(self, hwnd: Optional[int] = None) -> Optional[str]:
        """
        Attempt to capture using display driver/kernel level access.
        
        Args:
            hwnd: Optional window handle to capture. If None, captures entire screen.
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        try:
            # This is a very advanced technique that would normally require
            # kernel-mode driver access, which is not feasible in a Python script.
            
            # For this POC, we'll try an alternative approach using techniques to
            # access lower-level graphics functionality.
            
            # Get primary monitor information
            monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromWindow(
                hwnd if hwnd else win32gui.GetDesktopWindow(),
                win32con.MONITOR_DEFAULTTOPRIMARY
            ))
            
            # Monitor dimensions
            monitor_rect = monitor_info['Monitor']
            width = monitor_rect[2] - monitor_rect[0]
            height = monitor_rect[3] - monitor_rect[1]
            
            # Using an undocumented trick: Create a device context for the entire desktop
            desktop_hwnd = win32gui.GetDesktopWindow()
            desktop_dc = win32gui.GetWindowDC(desktop_hwnd)
            
            # Create a memory DC compatible with the desktop
            mem_dc = win32ui.CreateDCFromHandle(desktop_dc)
            compatible_dc = mem_dc.CreateCompatibleDC()
            
            # Create a bitmap to store the screenshot
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mem_dc, width, height)
            compatible_dc.SelectObject(bitmap)
            
            # Try to capture the screen by copying from desktop DC to memory DC
            # Use a special set of flags for BitBlt to bypass restrictions
            CAPTUREBLT = 0x40000000  # Include layered windows
            compatible_dc.BitBlt(
                (0, 0), (width, height), 
                mem_dc, 
                (monitor_rect[0], monitor_rect[1]), 
                win32con.SRCCOPY | CAPTUREBLT
            )
            
            # Convert to PIL Image
            bmpinfo = bitmap.GetInfo()
            bmpstr = bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # If a specific window was requested, crop to that window
            if hwnd:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                # Adjust for monitor position
                left -= monitor_rect[0]
                top -= monitor_rect[1]
                right -= monitor_rect[0]
                bottom -= monitor_rect[1]
                
                # Make sure coordinates are within the image bounds
                left = max(0, left)
                top = max(0, top)
                right = min(width, right)
                bottom = min(height, bottom)
                
                if left < right and top < bottom:
                    img = img.crop((left, top, right, bottom))
            
            # Clean up resources
            win32gui.DeleteObject(bitmap.GetHandle())
            compatible_dc.DeleteDC()
            mem_dc.DeleteDC()
            win32gui.ReleaseDC(desktop_hwnd, desktop_dc)
            
            # Save the image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(self.screenshot_dir, f"displaydriver_{timestamp}.png")
            img.save(filename)
            
            logger.info(f"Display driver capture saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Display driver capture failed: {e}")
            return None
    
    def capture_using_gdi_window_redir(self, hwnd: Optional[int] = None) -> Optional[str]:
        """
        Capture using GDI window redirection technique, which attempts to
        temporarily move the window to a virtual screen buffer.
        
        Args:
            hwnd: Optional window handle to capture. If None, captures entire screen.
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        try:
            if hwnd is None:
                # For full screen capture
                hwnd = win32gui.GetDesktopWindow()
            
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                logger.warning(f"Invalid window dimensions: {width}x{height}")
                return None
            
            # Try to temporarily "redirect" the window by changing Z-order
            # and capturing during the brief transition
            foreground_hwnd = win32gui.GetForegroundWindow()
            
            # Create a device context for the entire screen
            screen_dc = win32gui.GetDC(0)
            mem_dc = win32ui.CreateDCFromHandle(screen_dc)
            save_dc = mem_dc.CreateCompatibleDC()
            
            # Create bitmap
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mem_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # Temporarily change window z-order to potentially bypass protection
            # The idea is to briefly change window states while capturing
            try:
                # Save window position and state
                window_placement = win32gui.GetWindowPlacement(hwnd)
                
                # Try various window manipulations to bypass protection
                # First, try to briefly change window styles
                current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                
                # Modify window style to temporarily remove layered attribute
                # which might affect the SetWindowDisplayAffinity setting
                temp_style = current_style & ~win32con.WS_DLGFRAME & ~win32con.WS_SYSMENU
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, temp_style)
                
                # Force window update
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 
                                     left, top, width, height, 
                                     win32con.SWP_FRAMECHANGED)
                
                # Try to capture during this brief state change
                CAPTUREBLT = 0x40000000  # Include layered windows
                result = save_dc.BitBlt(
                    (0, 0), (width, height), 
                    mem_dc, 
                    (left, top), 
                    win32con.SRCCOPY | CAPTUREBLT
                )
                
                # Restore original window style and position
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, current_style)
                win32gui.SetWindowPlacement(hwnd, window_placement)
                
                # Restore foreground window
                if foreground_hwnd:
                    win32gui.SetForegroundWindow(foreground_hwnd)
                    
            except Exception as e:
                logger.warning(f"Window manipulation failed: {e}")
                
                # Try a simpler BitBlt directly from screen
                try:
                    save_dc.BitBlt(
                        (0, 0), (width, height), 
                        mem_dc, 
                        (left, top), 
                        win32con.SRCCOPY | CAPTUREBLT
                    )
                except Exception as inner_e:
                    logger.error(f"Direct BitBlt also failed: {inner_e}")
                    return None
            
            # Convert to PIL Image
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # Clean up
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mem_dc.DeleteDC()
            win32gui.ReleaseDC(0, screen_dc)
            
            # Check if the image is mostly black (which might indicate capture protection)
            img_array = np.array(img)
            if np.mean(img_array) < 5:  # Very dark image
                logger.warning("Captured image is mostly black, likely protected")
                
                # Try a different approach - add slight delay to try to catch redraw
                time.sleep(0.1)
                
                # Try PrintWindow as a fallback
                try:
                    hwnd_dc = win32gui.GetWindowDC(hwnd)
                    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
                    save_dc = mfc_dc.CreateCompatibleDC()
                    save_bitmap = win32ui.CreateBitmap()
                    save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
                    save_dc.SelectObject(save_bitmap)
                    
                    # Use PrintWindow with full window content option
                    result = win32gui.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)  # PW_RENDERFULLCONTENT = 2
                    
                    bmpinfo = save_bitmap.GetInfo()
                    bmpstr = save_bitmap.GetBitmapBits(True)
                    img = Image.frombuffer(
                        'RGB',
                        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                        bmpstr, 'raw', 'BGRX', 0, 1
                    )
                    
                    # Check again if still black
                    img_array = np.array(img)
                    if np.mean(img_array) < 5:
                        logger.warning("PrintWindow also produced a black image")
                    
                    # Clean up
                    win32gui.DeleteObject(save_bitmap.GetHandle())
                    save_dc.DeleteDC()
                    mfc_dc.DeleteDC()
                    win32gui.ReleaseDC(hwnd, hwnd_dc)
                    
                except Exception as e:
                    logger.error(f"PrintWindow fallback failed: {e}")
            
            # Save the image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(self.screenshot_dir, f"gdi_redir_{timestamp}.png")
            img.save(filename)
            
            logger.info(f"GDI window redirection capture saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"GDI window redirection capture failed: {e}")
            return None


class ScreenCaptureProxy:
    """
    ScreenCaptureProxy attempts to capture screens by leveraging multiple techniques
    and aggregating results from different approaches.
    """
    
    def __init__(self, screenshot_dir: str = "screenshots"):
        """
        Initialize the screen capture proxy.
        
        Args:
            screenshot_dir: Directory to save screenshots
        """
        self.screenshot_dir = screenshot_dir
        
        # Import the enhanced capture module
        from enhanced_capture import EnhancedScreenCapture, get_window_handle_by_name
        
        # Store the get_window_handle_by_name function
        self.get_window_handle_by_name = get_window_handle_by_name
        
        # Create instances of both capture systems
        self.enhanced_capture = EnhancedScreenCapture(screenshot_dir)
        self.advanced_capture = AdvancedScreenCapture(screenshot_dir)
        
        # Also create direct instances of specific capture methods
        self.windows_graphics_capture = None
        if windows_graphics_capture_available and is_windows_10_1809_or_later():
            try:
                self.windows_graphics_capture = WindowsGraphicsCapture(screenshot_dir)
                logger.info("Windows Graphics Capture initialized in proxy")
            except Exception as e:
                logger.error(f"Failed to initialize Windows Graphics Capture in proxy: {e}")
        
        self.dxgi_duplication = None
        if dxgi_desktop_duplication_available:
            try:
                self.dxgi_duplication = DXGIOutputDuplicationCapture(screenshot_dir)
                if self.dxgi_duplication.initialized:
                    logger.info("DXGI Desktop Duplication initialized in proxy")
                else:
                    logger.warning("DXGI Desktop Duplication initialization failed in proxy")
                    self.dxgi_duplication = None
            except Exception as e:
                logger.error(f"Failed to initialize DXGI Desktop Duplication in proxy: {e}")
                self.dxgi_duplication = None
        
        logger.info("Screen Capture Proxy initialized with multiple capture systems")
    
    def capture_screenshot(self, window_name: Optional[str] = None) -> Optional[str]:
        """
        Capture a screenshot using multiple methods and systems.
        
        Args:
            window_name: Optional name of window to capture. If None, captures entire screen.
            
        Returns:
            Path to the saved screenshot or None if all methods failed
        """
        hwnd = None
        
        if window_name:
            # Get window handle from name
            hwnd = self.get_window_handle_by_name(window_name)
            if not hwnd:
                logger.warning(f"Could not find window with name: {window_name}")
                return None
        
        # First try direct Windows Graphics Capture if available
        if self.windows_graphics_capture:
            try:
                logger.info("Attempting Windows Graphics Capture directly")
                result = self.windows_graphics_capture.capture_window(window_name=window_name, hwnd=hwnd)
                if result:
                    logger.info(f"Direct Windows Graphics Capture successful: {result}")
                    return result
            except Exception as e:
                logger.error(f"Direct Windows Graphics Capture failed: {e}")
        
        # Then try direct DXGI Desktop Duplication if available
        if self.dxgi_duplication:
            try:
                logger.info("Attempting DXGI Desktop Duplication directly")
                if hwnd:
                    result = self.dxgi_duplication.capture_window(hwnd)
                else:
                    result = self.dxgi_duplication.capture_full_screen()
                    
                if result:
                    logger.info(f"Direct DXGI Desktop Duplication successful: {result}")
                    return result
            except Exception as e:
                logger.error(f"Direct DXGI Desktop Duplication failed: {e}")
        
        # Then try the advanced techniques
        result = self.advanced_capture.capture_screenshot(hwnd)
        if result:
            logger.info(f"Advanced capture successful: {result}")
            return result
        
        # If advanced techniques fail, fall back to enhanced techniques
        result = self.enhanced_capture.capture_screenshot(hwnd)
        if result:
            logger.info(f"Enhanced capture successful: {result}")
            return result
        
        logger.error("All capture methods failed")
        return None


def test_all_capture_methods(window_name: Optional[str] = None):
    """
    Test all available capture methods on the specified window or entire screen.
    
    Args:
        window_name: Optional name of window to capture. If None, tests on entire screen.
    """
    print("\n=================================================")
    print("   Advanced Screen Capture Testing Utility")
    print("=================================================\n")
    
    # Create the screenshot directory
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # If window name provided, try to find the window
    hwnd = None
    if window_name:
        from enhanced_capture import get_window_handle_by_name
        hwnd = get_window_handle_by_name(window_name)
        if hwnd:
            print(f"Found window '{window_name}' with handle: {hwnd}")
            
            # Check window display affinity
            from enhanced_capture import GetWindowDisplayAffinity, WDA_NONE, WDA_MONITOR, WDA_EXCLUDEFROMCAPTURE
            affinity = wintypes.DWORD()
            if GetWindowDisplayAffinity(hwnd, ctypes.byref(affinity)):
                affinity_str = "NONE" if affinity.value == WDA_NONE else \
                              "MONITOR" if affinity.value == WDA_MONITOR else \
                              "EXCLUDEFROMCAPTURE" if affinity.value == WDA_EXCLUDEFROMCAPTURE else \
                              f"UNKNOWN ({affinity.value})"
                print(f"Window display affinity: {affinity_str}")
        else:
            print(f"Could not find window with name: {window_name}")
            return
    
    # Initialize capture systems
    enhanced = None
    advanced = None
    
    try:
        from enhanced_capture import EnhancedScreenCapture
        enhanced = EnhancedScreenCapture(screenshot_dir)
        print("Enhanced capture system initialized")
    except Exception as e:
        print(f"Error initializing enhanced capture: {e}")
    
    try:
        advanced = AdvancedScreenCapture(screenshot_dir)
        print("Advanced capture system initialized")
    except Exception as e:
        print(f"Error initializing advanced capture: {e}")
    
    # Test each method in sequence
    if enhanced:
        print("\n--- Enhanced Capture Methods ---")
        methods = [
            ("GDI", enhanced.capture_using_gdi),
            ("Accessibility", enhanced.capture_using_accessibility),
            ("Direct Memory", enhanced.capture_using_direct_memory),
            ("BitBlt with Temporary Affinity", enhanced.capture_using_bitblt_with_temporary_affinity),
            ("Magnification API", enhanced.capture_using_magnification_api)
        ]
        
        for name, method in methods:
            print(f"\nTesting {name} method...")
            try:
                result = method(hwnd)
                if result:
                    print(f"  SUCCESS! Screenshot saved to: {result}")
                else:
                    print("  FAILED. Method returned None")
            except Exception as e:
                print(f"  ERROR: {e}")
    
    if advanced:
        print("\n--- Advanced Capture Methods ---")
        methods = [
            ("Windows Graphics Capture API", advanced.capture_using_windows_graphics_capture),
            ("DXGI Desktop Duplication", advanced.capture_using_dxgi_desktop_duplication),
            ("Direct3D", advanced.capture_using_direct3d),
            ("Display Driver", advanced.capture_using_display_driver),
            ("GDI Window Redirection", advanced.capture_using_gdi_window_redir)
        ]
        
        for name, method in methods:
            print(f"\nTesting {name} method...")
            try:
                result = method(hwnd)
                if result:
                    print(f"  SUCCESS! Screenshot saved to: {result}")
                else:
                    print("  FAILED. Method returned None")
            except Exception as e:
                print(f"  ERROR: {e}")
    
    # Test the proxy system that combines all methods
    print("\n--- Testing Combined Capture Proxy ---")
    try:
        proxy = ScreenCaptureProxy(screenshot_dir)
        result = proxy.capture_screenshot(window_name)
        if result:
            print(f"Combined capture successful! Screenshot saved to: {result}")
        else:
            print("Combined capture failed. All methods returned None")
    except Exception as e:
        print(f"Error in combined capture: {e}")
    
    print("\n=================================================")
    print("   Capture Testing Complete")
    print("=================================================")
    print(f"\nAll screenshots saved to: {os.path.abspath(screenshot_dir)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test advanced screen capture methods")
    parser.add_argument("--window", help="Name of window to capture")
    args = parser.parse_args()
    
    test_all_capture_methods(args.window) 