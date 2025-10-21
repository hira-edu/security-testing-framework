import sys
import time
import os
import logging
from typing import Callable, Optional, List, Dict, Any, Tuple

# Import UI Automation dependencies
import comtypes
import comtypes.client
from comtypes.automation import VARIANT, VT_I4, VT_EMPTY
from ctypes import POINTER, byref, c_long, c_int, c_bool, windll, Structure, c_float, cast, c_void_p

# Set up logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("accessibility_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AccessibilityManager")

# Import UI Automation interfaces
try:
    # Import UI Automation interfaces
    from comtypes.gen.UIAutomationClient import *
except ImportError:
    # Generate the required COM interface wrappers
    logger.info("Generating UI Automation COM interfaces...")
    comtypes.client.GetModule("UIAutomationCore.dll")
    from comtypes.gen.UIAutomationClient import *

# Windows API function imports
user32 = windll.user32
kernel32 = windll.kernel32

def create_variant(value: Any, vt: int = VT_I4) -> VARIANT:
    """Create a VARIANT structure for UI Automation property values."""
    var = VARIANT()
    var.vt = vt
    if vt == VT_I4:
        var.lVal = value
    return var

class AccessibilityManager:
    """
    Manages window focus and manipulation using Windows UI Automation accessibility framework.
    This is a legitimate accessibility tool that helps users with focus issues.
    """
    
    def __init__(self):
        """Initialize the Accessibility Manager with UI Automation."""
        logger.info("Initializing Accessibility Manager...")
        
        self.uia = comtypes.client.CreateObject(CUIAutomation._reg_clsid_, 
                                               interface=IUIAutomation)
        self.active = False
        self.event_handlers = {}
        self.focused_windows = []
        self.blacklisted_windows = ["", "Program Manager", "Microsoft Text Input Application", 
                                  "LGControlCenterRTManager", "Media Player"]
        
        # Focus event handling
        self.focus_event_handler = None
        self.current_window_index = 0
        
        # Window state tracking
        self.window_positions = {}
        
        logger.info("Accessibility Manager initialized successfully.")
    
    def start(self):
        """Start monitoring focus changes and accessibility services."""
        if self.active:
            return
            
        logger.info("Starting Accessibility Manager services...")
        self.active = True
        self._register_event_handlers()
        logger.info("Accessibility Manager services started.")
    
    def stop(self):
        """Stop monitoring focus changes and accessibility services."""
        if not self.active:
            return
            
        logger.info("Stopping Accessibility Manager services...")
        self.active = False
        self._unregister_event_handlers()
        logger.info("Accessibility Manager services stopped.")
    
    def _register_event_handlers(self):
        """Register accessibility event handlers for focus tracking."""
        try:
            # Create an event handler for focus changed events
            self.focus_event_handler = FocusChangedEventHandler(self._on_focus_changed)
            self.uia.AddFocusChangedEventHandler(None, self.focus_event_handler)
            logger.info("Focus change event handler registered.")
        except Exception as e:
            logger.error(f"Failed to register event handlers: {e}")
    
    def _unregister_event_handlers(self):
        """Unregister accessibility event handlers."""
        try:
            if self.focus_event_handler:
                self.uia.RemoveFocusChangedEventHandler(self.focus_event_handler)
                self.focus_event_handler = None
            logger.info("Event handlers unregistered.")
        except Exception as e:
            logger.error(f"Failed to unregister event handlers: {e}")
    
    def _on_focus_changed(self, sender):
        """Handle focus changed events from UI Automation."""
        if not self.active:
            return
            
        try:
            # Get information about the newly focused element
            element_name = ""
            window_name = ""
            
            # Try to get the name of the element
            try:
                element_name = sender.CurrentName
            except:
                pass
                
            # Try to get the containing window
            try:
                window = self.get_containing_window(sender)
                if window:
                    window_name = window.CurrentName
            except:
                pass
                
            logger.debug(f"Focus changed to: Element: '{element_name}', Window: '{window_name}'")
            
            # Handle focus restoration if needed
            if window_name and "LockDown Browser" in window_name and hasattr(self, 'last_active_window') and self.last_active_window:
                # Attempt to restore focus to our previous window
                logger.info(f"Detected focus grab by LockDown Browser, restoring focus to: {getattr(self.last_active_window, 'CurrentName', 'Unknown')}")
                self.restore_focus_to_window(self.last_active_window)
                
        except Exception as e:
            logger.error(f"Error handling focus change: {e}")
    
    def get_containing_window(self, element):
        """
        Get the containing window for an automation element.
        """
        try:
            condition = self.uia.CreatePropertyCondition(
                UIA_ControlTypePropertyId, 
                UIA_WindowControlTypeId
            )
            
            window = element.FindFirst(TreeScope_Ancestors, condition)
            return window
        except Exception as e:
            logger.error(f"Failed to get containing window: {e}")
            return None
    
    def find_window_by_name(self, window_name: str, partial_match: bool = False):
        """
        Find a window by its name using UI Automation.
        
        Args:
            window_name: The name/title of the window to find
            partial_match: If True, searches for windows containing the provided name
            
        Returns:
            The found window element or None if not found
        """
        try:
            root_element = self.uia.GetRootElement()
            
            # Create a condition for window elements
            window_condition = self.uia.CreatePropertyCondition(
                UIA_ControlTypePropertyId, 
                UIA_WindowControlTypeId
            )
            
            # Find all windows
            all_windows = root_element.FindAll(TreeScope_Children, window_condition)
            
            # Search for the target window
            for i in range(all_windows.Length):
                window = all_windows.GetElement(i)
                try:
                    current_name = window.CurrentName
                    
                    if (partial_match and window_name in current_name) or (current_name == window_name):
                        return window
                except:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error finding window by name: {e}")
            return None
    
    def get_all_windows(self):
        """
        Get all visible application windows using UI Automation.
        
        Returns:
            A list of window automation elements
        """
        try:
            windows = []
            root_element = self.uia.GetRootElement()
            
            # Create a condition for window elements
            window_condition = self.uia.CreatePropertyCondition(
                UIA_ControlTypePropertyId, 
                UIA_WindowControlTypeId
            )
            
            # Find all windows
            all_windows = root_element.FindAll(TreeScope_Children, window_condition)
            
            # Filter windows
            for i in range(all_windows.Length):
                window = all_windows.GetElement(i)
                try:
                    window_name = window.CurrentName
                    
                    # Skip blacklisted windows and invisible windows
                    if (window_name in self.blacklisted_windows or 
                        not window.CurrentIsEnabled or 
                        window.CurrentOffscreenBehavior == OffscreenBehavior_Offscreen):
                        continue
                        
                    windows.append(window)
                except:
                    continue
            
            return windows
        except Exception as e:
            logger.error(f"Error getting all windows: {e}")
            return []
    
    def set_window_focus(self, window):
        """
        Set focus to a specific window using accessibility patterns.
        
        Args:
            window: The window automation element to focus
        
        Returns:
            True if successful, False otherwise
        """
        if not window:
            return False
            
        try:
            # Try to use the window pattern to activate the window
            pattern = None
            try:
                pattern = window.GetCurrentPattern(UIA_WindowPatternId)
                if pattern:
                    window_pattern = pattern.QueryInterface(IUIAutomationWindowPattern)
                    # Make sure window is not minimized
                    if window_pattern.CurrentWindowVisualState == WindowVisualState_Minimized:
                        window_pattern.SetWindowVisualState(WindowVisualState_Normal)
            except:
                pass
                
            # Set focus using accessibility interfaces
            try:
                # Try to get a legacy accessibility pattern as fallback
                pattern = window.GetCurrentPattern(UIA_LegacyIAccessiblePatternId)
                if pattern:
                    legacy_pattern = pattern.QueryInterface(IUIAutomationLegacyIAccessiblePattern)
                    legacy_pattern.Select(SELFLAG_TAKEFOCUS)
            except:
                pass
                
            # Try direct SetFocus approach
            window.SetFocus()
            
            # Remember this as the last active window for restoration purposes
            self.last_active_window = window
            
            # Get window name for logging
            window_name = "Unknown"
            try:
                window_name = window.CurrentName
            except:
                pass
                
            logger.info(f"Focus set to window: {window_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set window focus: {e}")
            return False
    
    def restore_focus_to_window(self, window):
        """
        Restore focus to a specific window using accessibility patterns.
        This is used when focus is grabbed by another application.
        
        Args:
            window: The window automation element to restore focus to
        
        Returns:
            True if successful, False otherwise
        """
        if not window:
            return False
            
        try:
            # Delayed focus restoration to overcome focus stealing prevention
            time.sleep(0.1)
            return self.set_window_focus(window)
        except Exception as e:
            logger.error(f"Failed to restore window focus: {e}")
            return False
    
    def cycle_windows(self, direction: str = "next"):
        """
        Cycle through open application windows and set focus.
        
        Args:
            direction: Direction to cycle ("next" or "previous")
            
        Returns:
            The window that received focus
        """
        try:
            windows = self.get_all_windows()
            if not windows:
                logger.info("No windows available for cycling")
                return None
                
            # Update the window index based on direction
            if direction == "next":
                self.current_window_index = (self.current_window_index + 1) % len(windows)
            else:
                self.current_window_index = (self.current_window_index - 1) % len(windows)
                
            # Get the window to focus
            window = windows[self.current_window_index]
            
            # Set focus to the window
            self.set_window_focus(window)
            
            # Return the window
            return window
        except Exception as e:
            logger.error(f"Error cycling windows: {e}")
            return None
    
    def minimize_all_windows_except(self, exception_window_name: str = None):
        """
        Minimize all windows except the specified window.
        
        Args:
            exception_window_name: Name of the window to keep visible (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            windows = self.get_all_windows()
            self.window_positions = {}
            
            for window in windows:
                try:
                    window_name = window.CurrentName
                    
                    # Skip the exception window
                    if exception_window_name and exception_window_name in window_name:
                        continue
                        
                    # Save window position and state
                    pattern = window.GetCurrentPattern(UIA_WindowPatternId)
                    if pattern:
                        window_pattern = pattern.QueryInterface(IUIAutomationWindowPattern)
                        
                        # Save current state
                        self.window_positions[window] = window_pattern.CurrentWindowVisualState
                        
                        # Minimize the window
                        window_pattern.SetWindowVisualState(WindowVisualState_Minimized)
                except:
                    continue
            
            # If there is an exception window, focus it
            if exception_window_name:
                exception_window = self.find_window_by_name(exception_window_name, True)
                if exception_window:
                    self.set_window_focus(exception_window)
            
            return True
        except Exception as e:
            logger.error(f"Error minimizing windows: {e}")
            return False
    
    def restore_all_windows(self):
        """
        Restore all previously minimized windows to their original state.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            for window, state in self.window_positions.items():
                try:
                    pattern = window.GetCurrentPattern(UIA_WindowPatternId)
                    if pattern:
                        window_pattern = pattern.QueryInterface(IUIAutomationWindowPattern)
                        
                        # Restore to the previous state
                        if state != WindowVisualState_Minimized:
                            window_pattern.SetWindowVisualState(state)
                except:
                    continue
            
            # Clear the saved positions
            self.window_positions = {}
            
            return True
        except Exception as e:
            logger.error(f"Error restoring windows: {e}")
            return False
    
    def find_window_by_process_name(self, process_name: str):
        """
        Find a window belonging to a specific process.
        
        Args:
            process_name: The name of the process to look for
            
        Returns:
            The found window element or None if not found
        """
        try:
            import psutil
            process_name = process_name.lower()
            
            # Get all windows
            windows = self.get_all_windows()
            
            for window in windows:
                try:
                    # Get the window handle
                    pattern = window.GetCurrentPattern(UIA_LegacyIAccessiblePatternId)
                    if pattern:
                        legacy_pattern = pattern.QueryInterface(IUIAutomationLegacyIAccessiblePattern)
                        hwnd = legacy_pattern.WindowHandle
                        
                        # Get the process ID from the window handle
                        pid = c_int()
                        user32.GetWindowThreadProcessId(hwnd, byref(pid))
                        
                        # Check if the process name matches
                        try:
                            proc = psutil.Process(pid.value)
                            if process_name in proc.name().lower():
                                return window
                        except:
                            continue
                except:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error finding window by process name: {e}")
            return None


class FocusChangedEventHandler(IUIAutomationFocusChangedEventHandler):
    """Event handler for focus change events from UI Automation."""
    
    def __init__(self, callback):
        super(FocusChangedEventHandler, self).__init__()
        self.callback = callback
    
    def HandleFocusChangedEvent(self, sender):
        """Handle focus changed events."""
        try:
            self.callback(sender)
        except Exception as e:
            logger.error(f"Error in focus change handler: {e}")
        return S_OK 