"""
Windows Graphics Capture Module for UndownUnlock

This module implements the Windows Graphics Capture API (available in Windows 10 1809+)
to capture screenshots, even from windows protected with SetWindowDisplayAffinity.

The implementation uses the Windows.Graphics.Capture APIs through interop with C#/.NET
to directly interface with the modern WinRT APIs that weren't designed to be used from Python.
"""

import os
import sys
import time
import ctypes
import logging
import threading
import tempfile
import uuid
from datetime import datetime
from typing import Optional, Tuple, Dict, List, Any
from pathlib import Path

# Third-party imports
import numpy as np
import clr  # Python.NET for .NET interop
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32process
import win32api
import win32ui
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("windows_graphics_capture.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WindowsGraphicsCapture")

# Check if we're on Windows 10 1809 or later
def is_windows_10_1809_or_later():
    """Check if the current Windows version supports Graphics Capture API."""
    try:
        ver_info = sys.getwindowsversion()
        # Windows 10 1809 has build number 17763
        return (ver_info.major >= 10 and ver_info.build >= 17763)
    except Exception as e:
        logger.error(f"Failed to check Windows version: {e}")
        return False

# In a real implementation, we need to load necessary assemblies
def load_required_assemblies():
    """Load the required .NET assemblies for Windows Graphics Capture."""
    try:
        # Add reference to the folder containing our interop DLL
        dll_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(dll_dir)
        
        # Add reference to the required .NET Framework assemblies
        clr.AddReference("System")
        clr.AddReference("System.Runtime")
        clr.AddReference("System.Runtime.InteropServices")
        clr.AddReference("System.Drawing")

        # Attempt to load WinRT support assemblies
        try:
            clr.AddReference("System.Runtime.WindowsRuntime")
        except Exception as runtime_exc:
            logger.debug(f"Optional System.Runtime.WindowsRuntime load failed: {runtime_exc}")

        winrt_loaded = False
        try:
            clr.AddReference("Windows")
            winrt_loaded = True
        except Exception as winmd_error:
            logger.warning(f"Failed to load Windows metadata via standard reference: {winmd_error}")

            # Probe common Windows SDK locations for Windows.winmd if the direct load failed
            sdk_roots = []
            program_files_x86 = os.environ.get("ProgramFiles(x86)")
            if program_files_x86:
                sdk_roots.extend([
                    Path(program_files_x86) / "Windows Kits" / "10" / "UnionMetadata",
                    Path(program_files_x86) / "Windows Kits" / "10" / "References",
                ])

            for root in sdk_roots:
                if not root.exists():
                    continue

                candidate_dirs = sorted(
                    [path for path in root.iterdir() if path.is_dir()],
                    reverse=True
                )

                for directory in candidate_dirs:
                    candidate = directory / "Windows.winmd"
                    if not candidate.exists():
                        continue

                    try:
                        clr.AddReferenceToFileAndPath(str(candidate))
                        logger.info(f"Loaded Windows metadata from {candidate}")
                        winrt_loaded = True
                        break
                    except Exception as candidate_error:
                        logger.warning(f"Failed to load WinRT metadata from {candidate}: {candidate_error}")

                if winrt_loaded:
                    break

            if not winrt_loaded:
                raise
        
        # Try to add reference to our custom interop DLL
        # This DLL would need to be created separately
        try:
            clr.AddReference("WinRTCaptureInterop")
            logger.info("Loaded WinRTCaptureInterop assembly")
        except Exception as e:
            logger.error(f"Failed to load WinRTCaptureInterop assembly: {e}")
            # If the DLL is not found, we'll create it on the fly
            create_interop_assembly()
            try:
                clr.AddReference("WinRTCaptureInterop")
                logger.info("Successfully created and loaded WinRTCaptureInterop assembly")
            except Exception as e2:
                logger.error(f"Failed to load dynamically created interop assembly: {e2}")
                raise

        return True
    except Exception as e:
        logger.error(f"Failed to load required assemblies: {e}")
        return False

def create_interop_assembly():
    """
    Dynamically creates the interop assembly for Windows Graphics Capture.
    
    This function generates a C# source file containing the necessary interop code
    and compiles it into a DLL using the C# compiler.
    """
    try:
        # Determine the full path for the interop DLL
        dll_dir = os.path.dirname(os.path.abspath(__file__))
        dll_path = os.path.join(dll_dir, "WinRTCaptureInterop.dll")
        
        # Check if the DLL already exists
        if os.path.exists(dll_path):
            logger.info(f"Interop DLL already exists at {dll_path}")
            return True
        
        # We'll need to create a temporary C# source file
        cs_source = """
        using System;
        using System.IO;
        using System.Threading.Tasks;
        using System.Runtime.InteropServices;
        using System.Drawing;
        using System.Drawing.Imaging;
        using Windows.Graphics;
        using Windows.Graphics.Capture;
        using Windows.Graphics.DirectX;
        using Windows.Graphics.DirectX.Direct3D11;
        using Windows.Foundation;

        namespace WinRTCaptureInterop
        {
            public static class GraphicsCaptureInterop
            {
                [ComImport]
                [Guid("3628E81B-3CAC-4C60-B7F4-23CE0E0C3356")]
                [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                public interface IGraphicsCaptureItemInterop
                {
                    IntPtr CreateForWindow(
                        [In] IntPtr window,
                        [In] ref Guid riid);

                    IntPtr CreateForMonitor(
                        [In] IntPtr monitor,
                        [In] ref Guid riid);
                }

                [ComImport]
                [Guid("FAB114F7-63FE-4A8F-BCFD-237094639F53")]
                [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                public interface IDirect3D11CaptureFramePoolInterop
                {
                    IntPtr GetOrCreateSharedTextureForHandle(
                        [In] IntPtr handle,
                        [Out, MarshalAs(UnmanagedType.IUnknown)] out object result);
                }

                [DllImport("user32.dll")]
                public static extern IntPtr GetForegroundWindow();

                [DllImport("user32.dll")]
                public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

                [DllImport("user32.dll", SetLastError = true)]
                public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

                [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
                public static extern int GetWindowTextLength(IntPtr hWnd);

                [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
                public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

                [StructLayout(LayoutKind.Sequential)]
                public struct RECT
                {
                    public int Left;
                    public int Top;
                    public int Right;
                    public int Bottom;
                }

                private static IDirect3D11Device _device;
                private static IDirect3DDevice _d3dDevice;

                static GraphicsCaptureInterop()
                {
                    InitializeDirect3D();
                }

                private static void InitializeDirect3D()
                {
                    // Create D3D11 device
                    var d3dDevice = Direct3D11.CreateDevice(
                        DriverType.Hardware,
                        DeviceCreationFlags.BgraSupport);

                    // Create IDirect3DDevice
                    var dxgiDevice = d3dDevice.QueryInterface<SharpDX.DXGI.Device3>();
                    var interopDevice = CreateDirect3DDeviceFromDXGIDevice(dxgiDevice.NativePointer);
                    _device = d3dDevice;
                    _d3dDevice = interopDevice;
                }

                [DllImport("d3d11.dll", EntryPoint = "CreateDirect3D11DeviceFromDXGIDevice", SetLastError = true)]
                private static extern int D3D11CreateDeviceFromDXGIDevice(IntPtr dxgiDevice, out IntPtr graphicsDevice);

                private static IDirect3DDevice CreateDirect3DDeviceFromDXGIDevice(IntPtr dxgiDevice)
                {
                    D3D11CreateDeviceFromDXGIDevice(dxgiDevice, out IntPtr pUnknown);
                    var inspectable = Marshal.GetObjectForIUnknown(pUnknown);
                    Marshal.Release(pUnknown);
                    return (IDirect3DDevice)inspectable;
                }

                // Main capture method
                public static byte[] CaptureWindow(IntPtr hWnd, string outputPath = null)
                {
                    try
                    {
                        // Early check if window exists
                        if (!IsWindow(hWnd))
                            throw new ArgumentException("Invalid window handle");

                        // Initialize Direct3D
                        InitializeDirect3D();

                        // Create the GraphicsCaptureItem for the window
                        GraphicsCaptureItem item = CreateCaptureItemForWindow(hWnd);
                        if (item == null)
                            throw new Exception("Failed to create capture item for window");

                        // Get the size of the window
                        SizeInt32 size = item.Size;

                        // Create a frame pool
                        Direct3D11CaptureFramePool framePool = Direct3D11CaptureFramePool.Create(
                            _d3dDevice,
                            DirectXPixelFormat.B8G8R8A8UIntNormalized,
                            2,  // Frame count
                            size);

                        // Create a capture session
                        GraphicsCaptureSession session = framePool.CreateCaptureSession(item);

                        // Start capture
                        session.StartCapture();

                        // Wait a bit to ensure we get a frame
                        bool gotFrame = false;
                        Direct3D11CaptureFrame frame = null;
                        byte[] imageBytes = null;

                        // Set up the event handler
                        using var frameSemaphore = new System.Threading.SemaphoreSlim(0);
                        framePool.FrameArrived += (s, e) =>
                        {
                            frame = framePool.TryGetNextFrame();
                            if (frame != null)
                            {
                                gotFrame = true;
                                frameSemaphore.Release();
                            }
                        };

                        // Wait for up to 5 seconds for a frame
                        if (!frameSemaphore.Wait(TimeSpan.FromSeconds(5)))
                        {
                            throw new TimeoutException("Timed out waiting for capture frame");
                        }

                        if (gotFrame && frame != null)
                        {
                            // Get the surface from the frame
                            IDirect3DSurface surface = frame.Surface;

                            // Convert the surface to a bitmap using our helper
                            using var bitmap = SurfaceToBitmap(surface, size.Width, size.Height);
                            
                            // Save to memory stream
                            using var memStream = new MemoryStream();
                            bitmap.Save(memStream, ImageFormat.Png);
                            imageBytes = memStream.ToArray();

                            // If output path was provided, save the file
                            if (!string.IsNullOrEmpty(outputPath))
                            {
                                try
                                {
                                    bitmap.Save(outputPath, ImageFormat.Png);
                                }
                                catch (Exception ex)
                                {
                                    Console.WriteLine($"Error saving to file: {ex.Message}");
                                }
                            }

                            // Clean up
                            frame.Dispose();
                        }

                        // Clean up resources
                        session.Dispose();
                        framePool.Dispose();

                        return imageBytes;
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Capture error: {ex.Message}\n{ex.StackTrace}");
                        return null;
                    }
                }

                public static byte[] CaptureMonitor(IntPtr hMonitor, string outputPath = null)
                {
                    try
                    {
                        if (hMonitor == IntPtr.Zero)
                            throw new ArgumentException("Invalid monitor handle");

                        InitializeDirect3D();

                        GraphicsCaptureItem item = CreateCaptureItemForMonitor(hMonitor);
                        if (item == null)
                            throw new Exception("Failed to create capture item for monitor");

                        SizeInt32 size = item.Size;

                        Direct3D11CaptureFramePool framePool = Direct3D11CaptureFramePool.Create(
                            _d3dDevice,
                            DirectXPixelFormat.B8G8R8A8UIntNormalized,
                            2,
                            size);

                        GraphicsCaptureSession session = framePool.CreateCaptureSession(item);
                        session.StartCapture();

                        bool gotFrame = false;
                        Direct3D11CaptureFrame frame = null;
                        byte[] imageBytes = null;

                        using var frameSemaphore = new System.Threading.SemaphoreSlim(0);
                        framePool.FrameArrived += (s, e) =>
                        {
                            frame = framePool.TryGetNextFrame();
                            if (frame != null)
                            {
                                gotFrame = true;
                                frameSemaphore.Release();
                            }
                        };

                        if (!frameSemaphore.Wait(TimeSpan.FromSeconds(5)))
                        {
                            throw new TimeoutException("Timed out waiting for capture frame");
                        }

                        if (gotFrame && frame != null)
                        {
                            IDirect3DSurface surface = frame.Surface;

                            using var bitmap = SurfaceToBitmap(surface, size.Width, size.Height);

                            using var memStream = new MemoryStream();
                            bitmap.Save(memStream, ImageFormat.Png);
                            imageBytes = memStream.ToArray();

                            if (!string.IsNullOrEmpty(outputPath))
                            {
                                try
                                {
                                    bitmap.Save(outputPath, ImageFormat.Png);
                                }
                                catch (Exception ex)
                                {
                                    Console.WriteLine($"Error saving to file: {ex.Message}");
                                }
                            }

                            frame.Dispose();
                        }

                        session.Dispose();
                        framePool.Dispose();

                        return imageBytes;
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Monitor capture error: {ex.Message}\n{ex.StackTrace}");
                        return null;
                    }
                }

                private static Bitmap SurfaceToBitmap(IDirect3DSurface surface, int width, int height)
                {
                    // Get the underlying DXGI resource
                    var access = surface.QueryInterface<IDirect3DDxgiInterfaceAccess>();
                    var dxgiResource = access.GetInterface<IDXGISurface>();

                    // Lock the surface to get access to the pixels
                    var desc = dxgiResource.Description;
                    var rect = new DXGI_MAPPED_RECT();
                    dxgiResource.Map(out rect, DXGI_MAP_READ);

                    // Create a bitmap from the surface data
                    var bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
                    var bitmapData = bitmap.LockBits(
                        new Rectangle(0, 0, width, height),
                        ImageLockMode.WriteOnly,
                        PixelFormat.Format32bppArgb);

                    // Copy the pixels
                    var sourcePtr = rect.pBits;
                    var destPtr = bitmapData.Scan0;
                    var sourceStride = rect.Pitch;
                    var destStride = bitmapData.Stride;

                    for (int y = 0; y < height; y++)
                    {
                        CopyMemory(
                            new IntPtr(destPtr.ToInt64() + y * destStride),
                            new IntPtr(sourcePtr.ToInt64() + y * sourceStride),
                            (uint)(width * 4));
                    }

                    // Unlock and clean up
                    bitmap.UnlockBits(bitmapData);
                    dxgiResource.Unmap();
                    dxgiResource.Dispose();
                    access.Dispose();

                    return bitmap;
                }

                [DllImport("kernel32.dll", EntryPoint = "CopyMemory", SetLastError = false)]
                private static extern void CopyMemory(IntPtr dest, IntPtr src, uint count);

                private static GraphicsCaptureItem CreateCaptureItemForWindow(IntPtr hwnd)
                {
                    var interop = WindowsRuntimeMarshal.GetActivationFactory(typeof(GraphicsCaptureItem).FullName)
                        .QueryInterface<IGraphicsCaptureItemInterop>();
                    
                    var graphicsCaptureItemGuid = typeof(GraphicsCaptureItem).GUID;
                    IntPtr graphicsCaptureItemPtr = interop.CreateForWindow(
                        hwnd, 
                        ref graphicsCaptureItemGuid);

                    try
                    {
                        var graphicsCaptureItem = Marshal.GetObjectForIUnknown(graphicsCaptureItemPtr) as GraphicsCaptureItem;
                        return graphicsCaptureItem;
                    }
                    finally
                    {
                        Marshal.Release(graphicsCaptureItemPtr);
                    }
                }

                private static GraphicsCaptureItem CreateCaptureItemForMonitor(IntPtr monitorHandle)
                {
                    var interop = WindowsRuntimeMarshal.GetActivationFactory(typeof(GraphicsCaptureItem).FullName)
                        .QueryInterface<IGraphicsCaptureItemInterop>();

                    var graphicsCaptureItemGuid = typeof(GraphicsCaptureItem).GUID;
                    IntPtr graphicsCaptureItemPtr = interop.CreateForMonitor(
                        monitorHandle,
                        ref graphicsCaptureItemGuid);

                    try
                    {
                        var graphicsCaptureItem = Marshal.GetObjectForIUnknown(graphicsCaptureItemPtr) as GraphicsCaptureItem;
                        return graphicsCaptureItem;
                    }
                    finally
                    {
                        Marshal.Release(graphicsCaptureItemPtr);
                    }
                }

                [DllImport("user32.dll")]
                [return: MarshalAs(UnmanagedType.Bool)]
                public static extern bool IsWindow(IntPtr hWnd);

                public static string GetWindowTitle(IntPtr hWnd)
                {
                    int length = GetWindowTextLength(hWnd);
                    if (length == 0)
                        return string.Empty;

                    StringBuilder builder = new StringBuilder(length + 1);
                    GetWindowText(hWnd, builder, builder.Capacity);
                    return builder.ToString();
                }

                public static IntPtr FindWindowByTitle(string title, bool exactMatch = false)
                {
                    IntPtr result = IntPtr.Zero;
                    
                    EnumWindows((hWnd, lParam) =>
                    {
                        if (!IsWindowVisible(hWnd))
                            return true;

                        string windowTitle = GetWindowTitle(hWnd);
                        
                        if (string.IsNullOrEmpty(windowTitle))
                            return true;
                            
                        if ((exactMatch && windowTitle.Equals(title, StringComparison.OrdinalIgnoreCase)) ||
                            (!exactMatch && windowTitle.IndexOf(title, StringComparison.OrdinalIgnoreCase) >= 0))
                        {
                            result = hWnd;
                            return false; // Stop enumeration
                        }
                        
                        return true; // Continue enumeration
                    }, IntPtr.Zero);
                    
                    return result;
                }

                [DllImport("user32.dll")]
                [return: MarshalAs(UnmanagedType.Bool)]
                private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

                [DllImport("user32.dll")]
                [return: MarshalAs(UnmanagedType.Bool)]
                private static extern bool IsWindowVisible(IntPtr hWnd);

                private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
            }
        }
        """
        
        # Create a temporary directory to store the source file
        with tempfile.TemporaryDirectory() as temp_dir:
            cs_file = os.path.join(temp_dir, "WinRTCaptureInterop.cs")
            
            # Write the C# source to the file
            with open(cs_file, "w") as f:
                f.write(cs_source)
            
            # Compile the source file using csc.exe (C# compiler)
            # We need to specify references to the required assemblies
            compiler_path = find_csc_compiler()
            if not compiler_path:
                logger.error("Could not find C# compiler (csc.exe)")
                return False
            
            # Build the command to compile the DLL
            cmd = [
                compiler_path,
                "/target:library",
                "/out:" + dll_path,
                "/reference:System.dll",
                "/reference:System.Drawing.dll",
                "/reference:System.Runtime.dll",
                "/reference:Windows.dll",
                "/reference:System.Runtime.InteropServices.dll",
                cs_file
            ]
            
            # Execute the compiler
            import subprocess
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                shell=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to compile interop assembly: {stderr.decode()}")
                return False
            
            logger.info(f"Successfully compiled interop assembly to {dll_path}")
            return True
    
    except Exception as e:
        logger.error(f"Failed to create interop assembly: {e}")
        return False

def find_csc_compiler():
    """Find the C# compiler (csc.exe) on the system."""
    try:
        # Check Windows SDK locations
        sdk_paths = [
            r"C:\Windows\Microsoft.NET\Framework\v4.0.30319",
            r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319",
            r"C:\Program Files (x86)\MSBuild\14.0\Bin",
            r"C:\Program Files (x86)\MSBuild\15.0\Bin",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin",
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn",
            r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\Roslyn",
            r"C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\Roslyn",
        ]
        
        for path in sdk_paths:
            csc_path = os.path.join(path, "csc.exe")
            if os.path.exists(csc_path):
                logger.info(f"Found C# compiler at {csc_path}")
                return csc_path
        
        # If not found in standard locations, try to find using where command
        import subprocess
        process = subprocess.Popen(
            ["where", "csc.exe"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            shell=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            csc_path = stdout.decode().strip().split('\n')[0]
            logger.info(f"Found C# compiler using 'where' command: {csc_path}")
            return csc_path
        
        logger.warning("Could not find C# compiler")
        return None
    except Exception as e:
        logger.error(f"Error finding C# compiler: {e}")
        return None

class WindowsGraphicsCapture:
    """
    Implementation of Windows Graphics Capture API for taking screenshots
    even of windows protected with SetWindowDisplayAffinity.
    """
    
    def __init__(self, screenshot_dir: str = "screenshots"):
        """
        Initialize the Windows Graphics Capture system.
        
        Args:
            screenshot_dir: Directory to save screenshots
        """
        self.screenshot_dir = screenshot_dir
        
        # Check if directory exists, create if not
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Check if running on Windows 10 1809 or later
        self.is_supported = is_windows_10_1809_or_later()
        if not self.is_supported:
            logger.warning("Windows Graphics Capture API requires Windows 10 1809 or later")
            return
            
        # Load required assemblies
        if not load_required_assemblies():
            logger.error("Failed to load required assemblies for Windows Graphics Capture")
            self.is_supported = False
            return
            
        try:
            # Import the necessary namespaces
            global System, Windows, WinRTCaptureInterop
            import System
            from System import IntPtr
            import Windows
            import WinRTCaptureInterop
            logger.info("Successfully imported Windows Graphics Capture namespaces")
            self.is_supported = True
        except Exception as e:
            logger.error(f"Failed to import necessary namespaces: {e}")
            self.is_supported = False
    
    def capture_window(self, window_name: str = None, hwnd: int = None) -> Optional[str]:
        """
        Capture a screenshot of the specified window using Windows Graphics Capture API.
        
        Args:
            window_name: Name of the window to capture
            hwnd: Window handle to capture (takes precedence over window_name)
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.is_supported:
            logger.error("Windows Graphics Capture API is not supported on this system")
            return None
            
        try:
            # Get the window handle if needed
            if hwnd is None and window_name:
                # First try to find using the .NET interop method
                hwnd = int(WinRTCaptureInterop.GraphicsCaptureInterop.FindWindowByTitle(window_name, False))
                
                # If not found, try using Win32 API
                if hwnd == 0:
                    hwnd = win32gui.FindWindow(None, window_name)
                    if hwnd == 0:
                        # Try partial match
                        hwnd = self._find_window_by_partial_title(window_name)
            
            if not hwnd or hwnd == 0:
                logger.error(f"Could not find window: {window_name}")
                return None
                
            # Create a unique filename for the screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"wgc_capture_{timestamp}.png"
            file_path = os.path.join(self.screenshot_dir, filename)
            
            # Perform the capture
            logger.info(f"Capturing window {hwnd} using Windows Graphics Capture API")
            result = WinRTCaptureInterop.GraphicsCaptureInterop.CaptureWindow(System.IntPtr(hwnd), file_path)
            
            if result and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logger.info(f"Screenshot saved to {file_path}")
                return file_path
            else:
                # If the file wasn't created but we got binary data back
                if result and not os.path.exists(file_path):
                    # Convert the byte array to a PIL Image and save it
                    import array
                    byte_array = array.array('B', result)
                    from io import BytesIO
                    image = Image.open(BytesIO(byte_array))
                    image.save(file_path)
                    logger.info(f"Screenshot saved to {file_path} from binary data")
                    return file_path
                
                logger.error("Failed to capture screenshot with Windows Graphics Capture API")
                return None
        
        except Exception as e:
            logger.error(f"Error capturing screenshot with Windows Graphics Capture API: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _find_window_by_partial_title(self, partial_title: str) -> int:
        """
        Find a window by partial title.
        
        Args:
            partial_title: Partial window title to search for
            
        Returns:
            Window handle or 0 if not found
        """
        try:
            def enum_windows_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if partial_title.lower() in window_text.lower():
                        results.append(hwnd)
                return True
            
            results = []
            win32gui.EnumWindows(enum_windows_callback, results)
            
            if results:
                return results[0]
            return 0
        except Exception as e:
            logger.error(f"Error finding window by partial title: {e}")
            return 0
    
    def capture_monitor(self, monitor_index: int = 0) -> Optional[str]:
        """
        Capture a screenshot of the specified monitor using Windows Graphics Capture API.
        
        Args:
            monitor_index: Index of the monitor to capture (0 is the primary monitor)
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.is_supported:
            logger.error("Windows Graphics Capture API is not supported on this system")
            return None
            
        try:
            # Get the monitor handle
            monitors = self._get_monitor_handles()
            if monitor_index >= len(monitors):
                logger.error(f"Monitor index {monitor_index} is out of range. Only {len(monitors)} monitors available.")
                return None
                
            monitor_handle = monitors[monitor_index]
            
            # Create a unique filename for the screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"wgc_monitor_{monitor_index}_{timestamp}.png"
            file_path = os.path.join(self.screenshot_dir, filename)
            
            logger.info(f"Capturing monitor {monitor_index} using Windows Graphics Capture API")
            result = WinRTCaptureInterop.GraphicsCaptureInterop.CaptureMonitor(
                IntPtr(int(monitor_handle)),
                file_path
            )

            if result and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logger.info(f"Monitor screenshot saved to {file_path}")
                return file_path

            if result and not os.path.exists(file_path):
                import array
                from io import BytesIO

                byte_array = array.array('B', result)
                image = Image.open(BytesIO(byte_array))
                image.save(file_path)
                logger.info(f"Monitor screenshot saved to {file_path} from binary data")
                return file_path

            logger.error("Failed to capture monitor with Windows Graphics Capture API")
            return None
            
        except Exception as e:
            logger.error(f"Error capturing monitor with Windows Graphics Capture API: {e}")
            return None
    
    def _get_monitor_handles(self) -> List[int]:
        """
        Get handles for all monitors in the system.
        
        Returns:
            List of monitor handles
        """
        try:
            monitors = []
            
            def enum_monitors_callback(monitor, dc, rect, data):
                monitors.append(monitor)
                return True
                
            win32api.EnumDisplayMonitors(None, None, enum_monitors_callback, 0)
            return monitors
        except Exception as e:
            logger.error(f"Error getting monitor handles: {e}")
            return []

def test_windows_graphics_capture(window_name: Optional[str] = None):
    """
    Test the Windows Graphics Capture implementation.
    
    Args:
        window_name: Optional window name to capture
    """
    print("\n=================================================")
    print("Testing Windows Graphics Capture API")
    print("=================================================\n")
    
    # Create the capture object
    capture = WindowsGraphicsCapture("screenshots")
    
    if not capture.is_supported:
        print("Windows Graphics Capture API is not supported on this system.")
        print("This feature requires Windows 10 version 1809 (build 17763) or later.")
        return
    
    print("Windows Graphics Capture API is supported on this system.")
    
    # If no window name provided, use the foreground window
    if not window_name:
        hwnd = win32gui.GetForegroundWindow()
        window_name = win32gui.GetWindowText(hwnd)
        print(f"Using current foreground window: '{window_name}' (handle: {hwnd})")
    else:
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
                hwnd, window_name = results[0]
                print(f"Found window: '{window_name}' (handle: {hwnd})")
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
    
    # Check if the window has affinity set
    try:
        WDA_NONE = 0x00000000
        WDA_MONITOR = 0x00000001
        WDA_EXCLUDEFROMCAPTURE = 0x00000011
        
        GetWindowDisplayAffinity = ctypes.windll.user32.GetWindowDisplayAffinity
        GetWindowDisplayAffinity.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        GetWindowDisplayAffinity.restype = wintypes.BOOL
        
        affinity = wintypes.DWORD()
        if GetWindowDisplayAffinity(hwnd, ctypes.byref(affinity)):
            affinity_str = "NONE" if affinity.value == WDA_NONE else \
                          "MONITOR" if affinity.value == WDA_MONITOR else \
                          "EXCLUDEFROMCAPTURE" if affinity.value == WDA_EXCLUDEFROMCAPTURE else \
                          f"UNKNOWN ({affinity.value})"
            print(f"Window display affinity: {affinity_str}")
    except Exception as e:
        print(f"Error checking window display affinity: {e}")
    
    # Try to capture the window
    print(f"\nAttempting to capture window: '{window_name}'")
    screenshot_path = capture.capture_window(window_name=window_name)
    
    if screenshot_path:
        print(f"SUCCESS! Screenshot saved to: {screenshot_path}")
        
        # On Windows, try to open the screenshot
        try:
            os.startfile(screenshot_path)
        except:
            print(f"Screenshot saved to: {os.path.abspath(screenshot_path)}")
    else:
        print("FAILED. Could not capture the window.")
    
    print("\n=================================================")
    print("Windows Graphics Capture Test Complete")
    print("=================================================")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Windows Graphics Capture API")
    parser.add_argument("--window", help="Name of window to capture")
    args = parser.parse_args()
    
    test_windows_graphics_capture(args.window) 
