"""
DXGI Desktop Duplication Module for UndownUnlock

This module provides a complete implementation of the DXGI Desktop Duplication API
for capturing screenshots, even from windows protected with SetWindowDisplayAffinity.
This approach works directly with the GPU to obtain screen content at a lower level.
"""

import os
import sys
import time
import logging
import threading
import ctypes
from ctypes import wintypes, windll, POINTER, Structure, c_void_p, c_int, c_uint, c_bool, c_char, c_float, c_long, c_longlong, c_ulonglong, c_ushort
import tempfile
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any, Union, NamedTuple
import uuid
import numpy as np
from PIL import Image

# Third-party imports
import win32gui
import win32con
import win32api
import win32ui
import win32process
import pywintypes
from comtypes import GUID, COMMETHOD, IUnknown, COMObject, helpstring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dxgi_desktop_duplication.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DXGIDesktopDuplication")

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

# Direct3D constants
D3D11_SDK_VERSION = 7
D3D_DRIVER_TYPE_HARDWARE = 1
D3D_DRIVER_TYPE_WARP = 2
D3D_DRIVER_TYPE_REFERENCE = 3
D3D_DRIVER_TYPE_UNKNOWN = 0

# DXGI constants
DXGI_FORMAT_B8G8R8A8_UNORM = 87
DXGI_FORMAT_R8G8B8A8_UNORM = 28
DXGI_USAGE_RENDER_TARGET_OUTPUT = 0x00000020
DXGI_ALPHA_MODE_PREMULTIPLIED = 1
DXGI_SCALING_STRETCH = 0
DXGI_SWAP_EFFECT_DISCARD = 0
DXGI_CPU_ACCESS_READ = 1

# Memory access
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_FLAG_SEQUENTIAL_SCAN = 0x08000000
INVALID_HANDLE_VALUE = -1

# Feature levels
D3D_FEATURE_LEVEL_11_1 = 0xb100
D3D_FEATURE_LEVEL_11_0 = 0xb000
D3D_FEATURE_LEVEL_10_1 = 0xa100
D3D_FEATURE_LEVEL_10_0 = 0xa000
D3D_FEATURE_LEVEL_9_3 = 0x9300
D3D_FEATURE_LEVEL_9_2 = 0x9200
D3D_FEATURE_LEVEL_9_1 = 0x9100

# Creation flags
D3D11_CREATE_DEVICE_DEBUG = 0x00000002
D3D11_CREATE_DEVICE_BGRA_SUPPORT = 0x00000020
D3D11_CREATE_DEVICE_SINGLETHREADED = 0x00000001

# Texture creation flags
D3D11_USAGE_STAGING = 3
D3D11_USAGE_DEFAULT = 0
D3D11_CPU_ACCESS_READ = 0x20000
D3D11_CPU_ACCESS_WRITE = 0x10000
D3D11_RESOURCE_MISC_SHARED = 2
D3D11_RESOURCE_MISC_SHARED_KEYEDMUTEX = 0x10

# Error constants
E_ACCESSDENIED = 0x80070005
E_INVALIDARG = 0x80070057
E_OUTOFMEMORY = 0x8007000E
E_FAIL = 0x80004005
DXGI_ERROR_NOT_FOUND = 0x887A0002
DXGI_ERROR_ACCESS_LOST = 0x887A0026
DXGI_ERROR_WAIT_TIMEOUT = 0x887A0027
DXGI_ERROR_DEVICE_REMOVED = 0x887A0005
DXGI_ERROR_UNSUPPORTED = 0x887A0004

# Map flags
D3D11_MAP_READ = 1
D3D11_MAP_WRITE = 2
D3D11_MAP_READ_WRITE = 3

# Capture flags
DXGI_OUTDUPL_POINTER_SHAPE_TYPE_MONOCHROME = 0x00000001
DXGI_OUTDUPL_POINTER_SHAPE_TYPE_COLOR = 0x00000002
DXGI_OUTDUPL_POINTER_SHAPE_TYPE_MASKED_COLOR = 0x00000004
DXGI_OUTDUPL_POINTER_VISIBLE = 0x00000001
DXGI_OUTDUPL_POINTER_SHAPE_UPDATED = 0x00000002

#-----------------------------------------------------------------------------
# Helper Functions
#-----------------------------------------------------------------------------

def check_hresult(hresult, message="DXGI operation failed"):
    """Check HRESULT and raise exception if operation failed."""
    if hresult < 0:
        error_msg = f"{message} (HRESULT: 0x{hresult & 0xFFFFFFFF:08X})"
        if hresult == E_ACCESSDENIED:
            error_msg += " - Access denied"
        elif hresult == DXGI_ERROR_ACCESS_LOST:
            error_msg += " - Access lost, desktop switch or mode change may have occurred"
        elif hresult == DXGI_ERROR_WAIT_TIMEOUT:
            error_msg += " - Timeout waiting for frame"
        elif hresult == DXGI_ERROR_DEVICE_REMOVED:
            error_msg += " - Graphics device was removed"
        elif hresult == DXGI_ERROR_UNSUPPORTED:
            error_msg += " - Operation not supported"
        logger.error(error_msg)
        raise WindowsError(hresult, error_msg)

#-----------------------------------------------------------------------------
# COM Interfaces and Structures
#-----------------------------------------------------------------------------

# Define necessary COM interface GUIDs for DXGI and D3D11
class DXGI_IIDs:
    IDXGIFactory1 = GUID("{770AAE78-F26F-4DBA-A829-253C83D1B387}")
    IDXGIAdapter1 = GUID("{29038F61-3839-4626-91FD-086879011A05}")
    IDXGIOutput1 = GUID("{00CDDEA8-939B-4B83-A340-A685226666CC}")
    IDXGIOutput5 = GUID("{80A07424-AB52-42EB-833C-0C42FD282D98}")
    IDXGIOutputDuplication = GUID("{191CFAC3-A341-470D-B26E-A864F428319C}")
    IDXGISurface1 = GUID("{4AE63092-6327-4C1B-80AE-BFE12EA32B86}")
    IDXGIResource = GUID("{035F3AB4-482E-4E50-B41F-8A7F8BD8960B}")

class D3D11_IIDs:
    ID3D11Device = GUID("{DB6F6DDB-AC77-4E88-8253-819DF9BBF140}")
    ID3D11DeviceContext = GUID("{C0BFA96C-E089-44FB-8EAF-26F8796190DA}")
    ID3D11Texture2D = GUID("{6F15AAF2-D208-4E89-9AB4-489535D34F9C}")

# DXGI Structures
class DXGI_RATIONAL(Structure):
    _fields_ = [
        ("Numerator", c_uint),
        ("Denominator", c_uint)
    ]

class DXGI_MODE_DESC(Structure):
    _fields_ = [
        ("Width", c_uint),
        ("Height", c_uint),
        ("RefreshRate", DXGI_RATIONAL),
        ("Format", c_uint),
        ("ScanlineOrdering", c_uint),
        ("Scaling", c_uint)
    ]

class DXGI_SAMPLE_DESC(Structure):
    _fields_ = [
        ("Count", c_uint),
        ("Quality", c_uint)
    ]

class DXGI_OUTDUPL_DESC(Structure):
    _fields_ = [
        ("ModeDesc", DXGI_MODE_DESC),
        ("Rotation", c_uint),
        ("DesktopImageInSystemMemory", c_bool)
    ]

class DXGI_OUTDUPL_POINTER_POSITION(Structure):
    _fields_ = [
        ("Position", POINT),
        ("Visible", c_bool)
    ]

class DXGI_OUTDUPL_FRAME_INFO(Structure):
    _fields_ = [
        ("LastPresentTime", c_longlong),
        ("LastMouseUpdateTime", c_longlong),
        ("AccumulatedFrames", c_uint),
        ("RectsCoalesced", c_bool),
        ("ProtectedContentMaskedOut", c_bool),
        ("PointerPosition", DXGI_OUTDUPL_POINTER_POSITION),
        ("TotalMetadataBufferSize", c_uint),
        ("PointerShapeBufferSize", c_uint)
    ]

class DXGI_MAPPED_RECT(Structure):
    _fields_ = [
        ("Pitch", c_int),
        ("pBits", POINTER(c_char))
    ]

class RECT(Structure):
    _fields_ = [
        ("left", c_long),
        ("top", c_long),
        ("right", c_long),
        ("bottom", c_long)
    ]

class POINT(Structure):
    _fields_ = [
        ("x", c_long),
        ("y", c_long)
    ]

class D3D11_BOX(Structure):
    _fields_ = [
        ("left", c_uint),
        ("top", c_uint),
        ("front", c_uint),
        ("right", c_uint),
        ("bottom", c_uint),
        ("back", c_uint)
    ]

class D3D11_TEXTURE2D_DESC(Structure):
    _fields_ = [
        ("Width", c_uint),
        ("Height", c_uint),
        ("MipLevels", c_uint),
        ("ArraySize", c_uint),
        ("Format", c_uint),
        ("SampleDesc", DXGI_SAMPLE_DESC),
        ("Usage", c_uint),
        ("BindFlags", c_uint),
        ("CPUAccessFlags", c_uint),
        ("MiscFlags", c_uint)
    ]

class D3D11_MAPPED_SUBRESOURCE(Structure):
    _fields_ = [
        ("pData", c_void_p),
        ("RowPitch", c_uint),
        ("DepthPitch", c_uint)
    ]

# Define function types for d3d11.dll
D3D11CreateDevice = windll.d3d11.D3D11CreateDevice
D3D11CreateDevice.argtypes = [
    c_void_p,  # pAdapter
    c_uint,    # DriverType
    c_void_p,  # Software
    c_uint,    # Flags
    POINTER(c_uint),  # pFeatureLevels
    c_uint,    # FeatureLevels
    c_uint,    # SDKVersion
    POINTER(c_void_p),  # ppDevice
    POINTER(c_uint),    # pFeatureLevel
    POINTER(c_void_p)   # ppImmediateContext
]
D3D11CreateDevice.restype = c_long  # HRESULT

#-----------------------------------------------------------------------------
# DXGI Desktop Duplication Implementation
#-----------------------------------------------------------------------------

class DXGIOutputDuplication:
    """
    Implements the DXGI Desktop Duplication API for capturing the screen content
    directly from the GPU, bypassing SetWindowDisplayAffinity restrictions.
    """
    
    def __init__(self, output_index: int = 0, screenshot_dir: str = "screenshots"):
        """
        Initialize the DXGI Desktop Duplication system.
        
        Args:
            output_index: Index of the output/monitor to capture (0 is primary)
            screenshot_dir: Directory to save screenshots
        """
        self.screenshot_dir = screenshot_dir
        self.output_index = output_index
        
        # Create screenshot directory if it doesn't exist
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Initialize required COM objects
        self.device = None
        self.device_context = None
        self.dxgi_output = None
        self.dxgi_output_duplication = None
        self.acquired_frame = None
        self.staging_texture = None
        
        # Initialize capture state
        self.desc = None
        self.width = 0
        self.height = 0
        self.initialized = False
        
        # Initialize and check for DXGI availability
        self._initialize_dxgi()
    
    def _initialize_dxgi(self):
        """Initialize the DXGI components and create the duplication object."""
        try:
            # Create D3D11 device
            pDevice = c_void_p()
            pContext = c_void_p()
            
            # Try hardware acceleration first
            feature_levels = (c_uint * 3)(
                D3D_FEATURE_LEVEL_11_0,
                D3D_FEATURE_LEVEL_10_1,
                D3D_FEATURE_LEVEL_10_0
            )
            feature_level = c_uint()
            
            # Create D3D device with hardware acceleration
            logger.info("Creating D3D11 device with hardware acceleration")
            hr = D3D11CreateDevice(
                None,  # No adapter specified, use default
                D3D_DRIVER_TYPE_HARDWARE,
                None,  # No software renderer
                D3D11_CREATE_DEVICE_BGRA_SUPPORT,  # Flags
                feature_levels,  # Feature levels
                3,  # Number of feature levels
                D3D11_SDK_VERSION,
                ctypes.byref(pDevice),
                ctypes.byref(feature_level),
                ctypes.byref(pContext)
            )
            
            # If hardware acceleration fails, try WARP
            if hr < 0:
                logger.warning("Hardware acceleration failed, trying WARP")
                hr = D3D11CreateDevice(
                    None,
                    D3D_DRIVER_TYPE_WARP,
                    None,
                    D3D11_CREATE_DEVICE_BGRA_SUPPORT,
                    feature_levels,
                    3,
                    D3D11_SDK_VERSION,
                    ctypes.byref(pDevice),
                    ctypes.byref(feature_level),
                    ctypes.byref(pContext)
                )
                
                if hr < 0:
                    logger.error(f"Failed to create D3D11 device (HRESULT: 0x{hr & 0xFFFFFFFF:08X})")
                    return False
            
            # Store the device and context
            self.device = pDevice
            self.device_context = pContext
            
            # Get the DXGI device
            dxgi_device = c_void_p()
            hr = self.device.QueryInterface(DXGI_IIDs.IDXGIDevice, ctypes.byref(dxgi_device))
            check_hresult(hr, "Failed to get DXGI device")
            
            # Get the adapter from the DXGI device
            dxgi_adapter = c_void_p()
            hr = dxgi_device.GetParent(DXGI_IIDs.IDXGIAdapter1, ctypes.byref(dxgi_adapter))
            check_hresult(hr, "Failed to get DXGI adapter")
            
            # Get the output from the adapter
            dxgi_output = c_void_p()
            hr = dxgi_adapter.EnumOutputs(self.output_index, ctypes.byref(dxgi_output))
            check_hresult(hr, f"Failed to get DXGI output {self.output_index}")
            
            # Get the output description
            output_desc = DXGI_OUTPUT_DESC()
            hr = dxgi_output.GetDesc(ctypes.byref(output_desc))
            check_hresult(hr, "Failed to get output description")
            
            self.width = output_desc.DesktopCoordinates.right - output_desc.DesktopCoordinates.left
            self.height = output_desc.DesktopCoordinates.bottom - output_desc.DesktopCoordinates.top
            
            # Get IDXGIOutput1 interface
            dxgi_output1 = c_void_p()
            hr = dxgi_output.QueryInterface(DXGI_IIDs.IDXGIOutput1, ctypes.byref(dxgi_output1))
            check_hresult(hr, "Output does not support IDXGIOutput1")
            
            # Create duplication object
            dxgi_output_duplication = c_void_p()
            hr = dxgi_output1.DuplicateOutput(self.device, ctypes.byref(dxgi_output_duplication))
            
            if hr == DXGI_ERROR_NOT_CURRENTLY_AVAILABLE:
                logger.error("Maximum number of applications using DXGI Desktop Duplication reached")
                return False
            
            check_hresult(hr, "Failed to duplicate output")
            
            # Save duplication object
            self.dxgi_output_duplication = dxgi_output_duplication
            
            # Get output duplication description
            dupl_desc = DXGI_OUTDUPL_DESC()
            hr = self.dxgi_output_duplication.GetDesc(ctypes.byref(dupl_desc))
            check_hresult(hr, "Failed to get duplication description")
            
            # Save description
            self.desc = dupl_desc
            
            # Create staging texture for CPU access
            staging_desc = D3D11_TEXTURE2D_DESC()
            staging_desc.Width = self.width
            staging_desc.Height = self.height
            staging_desc.MipLevels = 1
            staging_desc.ArraySize = 1
            staging_desc.Format = dupl_desc.ModeDesc.Format
            staging_desc.SampleDesc.Count = 1
            staging_desc.SampleDesc.Quality = 0
            staging_desc.Usage = D3D11_USAGE_STAGING
            staging_desc.BindFlags = 0
            staging_desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ
            staging_desc.MiscFlags = 0
            
            staging_texture = c_void_p()
            hr = self.device.CreateTexture2D(ctypes.byref(staging_desc), None, ctypes.byref(staging_texture))
            check_hresult(hr, "Failed to create staging texture")
            
            self.staging_texture = staging_texture
            
            # Success!
            self.initialized = True
            logger.info(f"DXGI Desktop Duplication initialized for output {self.output_index} ({self.width}x{self.height})")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing DXGI Desktop Duplication: {e}")
            self._cleanup()
            return False
    
    def _cleanup(self):
        """Clean up and release all resources."""
        try:
            # Release frame if acquired
            if self.acquired_frame:
                self.dxgi_output_duplication.ReleaseFrame()
                self.acquired_frame = None
            
            # Release all objects using context managers for safety
            try:
                if self.staging_texture:
                    self.staging_texture.Release()
                    self.staging_texture = None
            except Exception as e:
                logger.warning(f"Error releasing staging texture: {e}")
                
            try:
                if self.dxgi_output_duplication:
                    self.dxgi_output_duplication.Release()
                    self.dxgi_output_duplication = None
            except Exception as e:
                logger.warning(f"Error releasing output duplication: {e}")
                
            try:
                if self.dxgi_output:
                    self.dxgi_output.Release()
                    self.dxgi_output = None
            except Exception as e:
                logger.warning(f"Error releasing output: {e}")
                
            try:
                if self.device_context:
                    self.device_context.Release()
                    self.device_context = None
            except Exception as e:
                logger.warning(f"Error releasing device context: {e}")
                
            try:
                if self.device:
                    self.device.Release()
                    self.device = None
            except Exception as e:
                logger.warning(f"Error releasing device: {e}")
                
            self.initialized = False
            logger.info("DXGI resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def capture_screenshot(self, timeout_ms: int = 1000) -> Optional[str]:
        """
        Capture a screenshot using DXGI Desktop Duplication.
        
        Args:
            timeout_ms: Timeout in milliseconds to wait for a new frame
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.initialized:
            logger.error("DXGI Desktop Duplication not initialized")
            return None
        
        try:
            # Create frame info structure
            frame_info = DXGI_OUTDUPL_FRAME_INFO()
            desktop_resource = c_void_p()
            
            # Acquire a new frame
            hr = self.dxgi_output_duplication.AcquireNextFrame(
                timeout_ms,
                ctypes.byref(frame_info),
                ctypes.byref(desktop_resource)
            )
            
            # Check for timeout
            if hr == DXGI_ERROR_WAIT_TIMEOUT:
                logger.warning("Timeout waiting for next frame")
                return None
                
            # Handle other errors
            try:
                check_hresult(hr, "Failed to acquire next frame")
            except:
                # If we get here, there was an error, so we don't need to release the frame
                return None
            
            # Mark that we have a frame that needs to be released
            self.acquired_frame = True
            
            # Get the IDXGIResource interface (already has the right interface pointer)
            dxgi_resource = desktop_resource
            
            # Get the texture interface
            texture = c_void_p()
            hr = dxgi_resource.QueryInterface(D3D11_IIDs.ID3D11Texture2D, ctypes.byref(texture))
            check_hresult(hr, "Failed to query ID3D11Texture2D interface")
            
            # Copy to staging texture (CPU accessible)
            self.device_context.CopyResource(self.staging_texture, texture)
            
            # Release the desktop resource
            dxgi_resource.Release()
            
            # Map the staging texture
            mapped_resource = D3D11_MAPPED_SUBRESOURCE()
            hr = self.device_context.Map(
                self.staging_texture, 
                0,
                D3D11_MAP_READ,
                0,
                ctypes.byref(mapped_resource)
            )
            check_hresult(hr, "Failed to map staging texture")
            
            try:
                # Copy the data from GPU to CPU
                buffer_size = mapped_resource.RowPitch * self.height
                buffer = (c_char * buffer_size).from_address(mapped_resource.pData)
                
                # Create an array from the mapped texture data
                img_array = np.frombuffer(buffer, dtype=np.uint8, count=buffer_size)
                
                # Reshape and convert to image
                img_array = img_array.reshape((self.height, mapped_resource.RowPitch // 4, 4))
                
                # Convert BGRA to RGB
                img_array_rgb = img_array[:, :, [2, 1, 0]]
                
                # Create a PIL Image
                img = Image.fromarray(img_array_rgb[:, :, :3])
                
                # Save to file with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(self.screenshot_dir, f"dxgi_output_{self.output_index}_{timestamp}.png")
                img.save(filename)
                
                logger.info(f"Screenshot saved to {filename}")
                return filename
                
            finally:
                # Unmap the texture
                self.device_context.Unmap(self.staging_texture, 0)
                
                # Release the frame
                self.dxgi_output_duplication.ReleaseFrame()
                self.acquired_frame = False
                
            return None
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            
            # Try to release the frame if acquired
            if self.acquired_frame:
                try:
                    self.dxgi_output_duplication.ReleaseFrame()
                except:
                    pass
                self.acquired_frame = False
                
            return None
    
    def __del__(self):
        """Clean up when object is deleted."""
        self._cleanup()


class DXGI_OUTPUT_DESC(Structure):
    _fields_ = [
        ("DeviceName", c_char * 32),
        ("DesktopCoordinates", RECT),
        ("AttachedToDesktop", c_bool),
        ("Rotation", c_uint),
        ("Monitor", c_void_p)
    ]


class DXGIOutputDuplicationCapture:
    """
    A higher-level class that manages multiple outputs and captures from the specified
    monitor or window region.
    """
    
    def __init__(self, screenshot_dir: str = "screenshots"):
        """
        Initialize the DXGI capture system.
        
        Args:
            screenshot_dir: Directory to save screenshots
        """
        self.screenshot_dir = screenshot_dir
        self.outputs = []
        self.initialized = False
        
        # Initialize DXGI for all outputs
        self._initialize_outputs()
    
    def _initialize_outputs(self):
        """Initialize DXGI Desktop Duplication for all available outputs."""
        try:
            # Get the number of monitors
            num_monitors = win32api.GetSystemMetrics(win32con.SM_CMONITORS)
            logger.info(f"Found {num_monitors} monitors")
            
            # Create duplication objects for each monitor
            for i in range(num_monitors):
                try:
                    duplication = DXGIOutputDuplication(i, self.screenshot_dir)
                    if duplication.initialized:
                        self.outputs.append(duplication)
                except Exception as e:
                    logger.error(f"Failed to initialize output {i}: {e}")
            
            self.initialized = len(self.outputs) > 0
            logger.info(f"DXGI Desktop Duplication initialized for {len(self.outputs)} outputs")
            
            return self.initialized
            
        except Exception as e:
            logger.error(f"Error initializing outputs: {e}")
            return False
    
    def capture_full_screen(self) -> Optional[str]:
        """
        Capture a screenshot of the entire primary monitor.
        
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.initialized or not self.outputs:
            logger.error("DXGI Desktop Duplication not initialized")
            return None
        
        # Capture primary monitor (output 0)
        return self.outputs[0].capture_screenshot()
    
    def capture_window(self, hwnd: int) -> Optional[str]:
        """
        Capture a screenshot of the specified window.
        This captures the entire output containing the window and then crops to the window region.
        
        Args:
            hwnd: Handle to the window to capture
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.initialized or not self.outputs:
            logger.error("DXGI Desktop Duplication not initialized")
            return None
        
        try:
            # Get the window rectangle
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Find which monitor the window is on
            monitor_handle = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            
            # Get monitor info
            monitor_info = win32api.GetMonitorInfo(monitor_handle)
            monitor_left, monitor_top, monitor_right, monitor_bottom = monitor_info["Monitor"]
            
            # Find which output this corresponds to
            output_index = 0  # Default to primary
            for i, output in enumerate(self.outputs):
                # Since we don't have a way to directly match the monitor handle to output,
                # we'll assume they're in the same order (which may not always be true)
                if i == output_index:
                    duplication = output
                    break
            else:
                duplication = self.outputs[0]  # Fallback to primary
            
            # Capture the entire output
            screenshot_path = duplication.capture_screenshot()
            if not screenshot_path:
                logger.error("Failed to capture output")
                return None
            
            # Load the screenshot
            img = Image.open(screenshot_path)
            
            # Adjust window coordinates to be relative to the monitor
            relative_left = left - monitor_left
            relative_top = top - monitor_top
            relative_right = relative_left + width
            relative_bottom = relative_top + height
            
            # Ensure coordinates are within bounds
            relative_left = max(0, relative_left)
            relative_top = max(0, relative_top)
            relative_right = min(img.width, relative_right)
            relative_bottom = min(img.height, relative_bottom)
            
            # Crop to window region
            cropped_img = img.crop((relative_left, relative_top, relative_right, relative_bottom))
            
            # Save cropped image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            cropped_path = os.path.join(self.screenshot_dir, f"dxgi_window_{hwnd}_{timestamp}.png")
            cropped_img.save(cropped_path)
            
            logger.info(f"Window screenshot saved to {cropped_path}")
            return cropped_path
            
        except Exception as e:
            logger.error(f"Error capturing window: {e}")
            return None
    
    def __del__(self):
        """Clean up when object is deleted."""
        for output in self.outputs:
            output._cleanup()


def test_dxgi_duplication(window_name: Optional[str] = None):
    """
    Test the DXGI Desktop Duplication capture system.
    
    Args:
        window_name: Optional name of window to capture
    """
    print("\n=================================================")
    print("Testing DXGI Desktop Duplication")
    print("=================================================\n")
    
    # Create screenshot directory
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Create capture object
    capture = DXGIOutputDuplicationCapture(screenshot_dir)
    
    if not capture.initialized:
        print("DXGI Desktop Duplication is not available on this system")
        print("This could be due to Windows version, graphics driver, or required privileges")
        return
    
    print(f"DXGI Desktop Duplication initialized with {len(capture.outputs)} outputs")
    
    # Capture full screen
    print("\nCapturing full screen...")
    fullscreen_path = capture.capture_full_screen()
    
    if fullscreen_path:
        print(f"SUCCESS! Full screen captured: {fullscreen_path}")
    else:
        print("FAILED: Could not capture full screen")
    
    # Capture window if specified
    if window_name:
        # Find the window
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd == 0:
            # Try partial match
            def enum_windows_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if window_name.lower() in window_text.lower():
                        results.append((hwnd, window_text))
                return True
            
            results = []
            win32gui.EnumWindows(enum_windows_callback, results)
            
            if results:
                hwnd, found_name = results[0]
                print(f"Found window: '{found_name}' (handle: {hwnd})")
            else:
                print(f"Could not find window: {window_name}")
                
                # List available windows
                print("\nAvailable windows:")
                def enum_windows_for_list(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        if window_text:
                            windows.append((hwnd, window_text))
                    return True
                
                windows = []
                win32gui.EnumWindows(enum_windows_for_list, windows)
                
                for i, (hwnd, title) in enumerate(windows[:10], 1):  # Show top 10 windows
                    print(f"  {i}. {title} (Handle: {hwnd})")
                return
        
        # Check window display affinity
        try:
            WDA_NONE = 0x00000000
            WDA_MONITOR = 0x00000001
            WDA_EXCLUDEFROMCAPTURE = 0x00000011
            
            GetWindowDisplayAffinity = ctypes.windll.user32.GetWindowDisplayAffinity
            GetWindowDisplayAffinity.argtypes = [wintypes.HWND, POINTER(c_uint)]
            GetWindowDisplayAffinity.restype = c_bool
            
            affinity = c_uint()
            if GetWindowDisplayAffinity(hwnd, ctypes.byref(affinity)):
                affinity_str = "NONE" if affinity.value == WDA_NONE else \
                              "MONITOR" if affinity.value == WDA_MONITOR else \
                              "EXCLUDEFROMCAPTURE" if affinity.value == WDA_EXCLUDEFROMCAPTURE else \
                              f"UNKNOWN ({affinity.value})"
                print(f"Window display affinity: {affinity_str}")
                
                if affinity.value == WDA_EXCLUDEFROMCAPTURE:
                    print("Window has EXCLUDEFROMCAPTURE flag set - standard capture methods will fail")
        except Exception as e:
            print(f"Error checking window display affinity: {e}")
        
        # Capture the window
        print(f"\nCapturing window '{window_name}'...")
        window_path = capture.capture_window(hwnd)
        
        if window_path:
            print(f"SUCCESS! Window captured: {window_path}")
            
            # Try to open the image
            try:
                os.startfile(window_path)
            except:
                pass
        else:
            print("FAILED: Could not capture window")
    
    print("\n=================================================")
    print("DXGI Desktop Duplication Test Complete")
    print("=================================================")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test DXGI Desktop Duplication screen capture")
    parser.add_argument("--window", help="Name of window to capture")
    args = parser.parse_args()
    
    test_dxgi_duplication(args.window) 