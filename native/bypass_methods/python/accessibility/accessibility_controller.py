import os
import sys
import time
import logging
import keyboard
import threading
import json
from PIL import ImageGrab, Image
from datetime import datetime

# Import the accessibility manager
from accessibility_manager import AccessibilityManager

# Import the named pipe manager for secure communication
from named_pipe_manager import NamedPipeServer

# Import enhanced screen capture to work around SetWindowDisplayAffinity
from enhanced_capture import EnhancedScreenCapture, get_window_handle_by_name

# Import advanced screen capture techniques
from advanced_capture import ScreenCaptureProxy

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("accessibility_controller.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AccessibilityController")

class AccessibilityController:
    """
    Controller for the Accessibility-based window management system.
    Provides keyboard shortcuts for managing window focus and captures.
    Includes a Named Pipe Server for secure inter-process communication.
    Uses multiple advanced screen capture methods to bypass SetWindowDisplayAffinity protection.
    """
    
    def __init__(self):
        """Initialize the controller with accessibility manager and named pipe server."""
        self.accessibility_manager = AccessibilityManager()
        self.pipe_server = NamedPipeServer("UndownUnlockAccessibilityPipe")
        self.running = False
        self.keyboard_thread = None
        self.target_app_name = "LockDown Browser"
        self.alt_windows = []
        self.screenshot_dir = "screenshots"
        
        # Initialize screen capture system using proxy that combines all methods
        self.screen_capture = ScreenCaptureProxy(self.screenshot_dir)
        
        # Ensure screenshot directory exists
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
    
    def start(self):
        """Start the controller, accessibility services, and pipe server."""
        if self.running:
            return
            
        logger.info("Starting accessibility controller...")
        
        # Start the accessibility manager
        self.accessibility_manager.start()
        
        # Set up keyboard hooks
        self.setup_keyboard_hooks()
        
        # Register pipe server message handlers
        self.register_pipe_handlers()
        
        # Start the pipe server
        self.pipe_server.start()
        
        # Start keyboard listener in a thread
        self.running = True
        self.keyboard_thread = threading.Thread(target=self.keyboard_listener)
        self.keyboard_thread.daemon = True
        self.keyboard_thread.start()
        
        logger.info("Accessibility controller started.")
    
    def stop(self):
        """Stop the controller, accessibility services, and pipe server."""
        if not self.running:
            return
            
        logger.info("Stopping accessibility controller...")
        
        # Stop the keyboard listener
        self.running = False
        if self.keyboard_thread:
            self.keyboard_thread.join(timeout=1.0)
        
        # Remove all keyboard hooks
        self.remove_keyboard_hooks()
        
        # Stop the pipe server
        self.pipe_server.stop()
        
        # Stop the accessibility manager
        self.accessibility_manager.stop()
        
        logger.info("Accessibility controller stopped.")
    
    def register_pipe_handlers(self):
        """Register handlers for named pipe messages."""
        
        # Handler for window cycling messages
        self.pipe_server.register_handler("cycle_window", self.handle_cycle_window)
        
        # Handler for focus window messages
        self.pipe_server.register_handler("focus_window", self.handle_focus_window)
        
        # Handler for minimize window messages
        self.pipe_server.register_handler("minimize_windows", self.handle_minimize_windows)
        
        # Handler for restore window messages
        self.pipe_server.register_handler("restore_windows", self.handle_restore_windows)
        
        # Handler for screenshot messages
        self.pipe_server.register_handler("take_screenshot", self.handle_take_screenshot)
        
        # Handler for get window list messages
        self.pipe_server.register_handler("get_window_list", self.handle_get_window_list)
        
        logger.info("Pipe message handlers registered")
    
    def handle_cycle_window(self, message_data, client_id):
        """Handle a window cycling request from a client."""
        try:
            direction = message_data.get("direction", "next")
            logger.info(f"Received cycle_window request from client {client_id}: direction={direction}")
            
            window = self.accessibility_manager.cycle_windows(direction)
            window_name = "Unknown"
            
            try:
                window_name = window.CurrentName
            except:
                pass
            
            return {
                "status": "success",
                "window_name": window_name,
                "message": f"Window cycled to {window_name}"
            }
        except Exception as e:
            logger.error(f"Error handling cycle_window: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def handle_focus_window(self, message_data, client_id):
        """Handle a window focus request from a client."""
        try:
            window_name = message_data.get("window_name", "")
            partial_match = message_data.get("partial_match", True)
            logger.info(f"Received focus_window request from client {client_id}: window_name={window_name}")
            
            if not window_name:
                return {
                    "status": "error",
                    "message": "Window name is required"
                }
            
            window = self.accessibility_manager.find_window_by_name(window_name, partial_match)
            
            if not window:
                return {
                    "status": "error",
                    "message": f"Window '{window_name}' not found"
                }
            
            success = self.accessibility_manager.set_window_focus(window)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Focus set to window '{window_name}'"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to set focus to window '{window_name}'"
                }
        except Exception as e:
            logger.error(f"Error handling focus_window: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def handle_minimize_windows(self, message_data, client_id):
        """Handle a minimize windows request from a client."""
        try:
            exception_window = message_data.get("exception_window", self.target_app_name)
            logger.info(f"Received minimize_windows request from client {client_id}: exception_window={exception_window}")
            
            success = self.accessibility_manager.minimize_all_windows_except(exception_window)
            
            if success:
                return {
                    "status": "success",
                    "message": f"All windows minimized except '{exception_window}'"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to minimize windows"
                }
        except Exception as e:
            logger.error(f"Error handling minimize_windows: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def handle_restore_windows(self, message_data, client_id):
        """Handle a restore windows request from a client."""
        try:
            logger.info(f"Received restore_windows request from client {client_id}")
            
            success = self.accessibility_manager.restore_all_windows()
            
            if success:
                return {
                    "status": "success",
                    "message": "All windows restored"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to restore windows"
                }
        except Exception as e:
            logger.error(f"Error handling restore_windows: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def handle_take_screenshot(self, message_data, client_id):
        """Handle a screenshot request from a client."""
        try:
            logger.info(f"Received take_screenshot request from client {client_id}")
            
            # Get the target window if specified
            target_window = message_data.get("window_name", None)
            
            # Take the screenshot using the combined capture proxy
            # This will try advanced methods first, then fall back to enhanced methods
            filename = self.screen_capture.capture_screenshot(target_window)
            
            if not filename:
                logger.error("Failed to capture screenshot with any method")
                return {
                    "status": "error",
                    "message": "Failed to capture screenshot with any method"
                }
            
            logger.info(f"Screenshot saved to {filename}")
            
            return {
                "status": "success",
                "message": f"Screenshot saved to {filename}",
                "screenshot_path": filename
            }
        except Exception as e:
            logger.error(f"Error handling take_screenshot: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def handle_get_window_list(self, message_data, client_id):
        """Handle a get window list request from a client."""
        try:
            logger.info(f"Received get_window_list request from client {client_id}")
            
            windows = self.accessibility_manager.get_all_windows()
            window_list = []
            
            for window in windows:
                try:
                    window_name = window.CurrentName
                    window_list.append(window_name)
                except:
                    continue
            
            return {
                "status": "success",
                "windows": window_list,
                "count": len(window_list)
            }
        except Exception as e:
            logger.error(f"Error handling get_window_list: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def setup_keyboard_hooks(self):
        """Set up keyboard hotkeys for controlling the application."""
        try:
            # Window cycling
            keyboard.add_hotkey('ctrl+tab', self.cycle_next_window)
            keyboard.add_hotkey('ctrl+shift+tab', self.cycle_prev_window)
            
            # Focus LockDown Browser (when specified)
            keyboard.add_hotkey('ctrl+l', self.focus_lockdown_browser)
            
            # Focus other window
            keyboard.add_hotkey('ctrl+o', self.focus_other_window)
            
            # Screenshot functionality
            keyboard.add_hotkey('ctrl+shift+s', self.take_screenshot)
            
            # Minimize all except target app
            keyboard.add_hotkey('ctrl+m', self.minimize_all_except_target)
            
            # Restore all windows
            keyboard.add_hotkey('ctrl+r', self.restore_all_windows)
            
            logger.info("Keyboard hooks set up successfully.")
        except Exception as e:
            logger.error(f"Failed to set up keyboard hooks: {e}")
    
    def remove_keyboard_hooks(self):
        """Remove all keyboard hooks."""
        try:
            # Clear all keyboard hooks
            keyboard.unhook_all()
            logger.info("Keyboard hooks removed.")
        except Exception as e:
            logger.error(f"Failed to remove keyboard hooks: {e}")
    
    def keyboard_listener(self):
        """Background thread for keyboard event processing."""
        try:
            while self.running:
                time.sleep(0.1)  # Prevent high CPU usage
        except Exception as e:
            logger.error(f"Error in keyboard listener: {e}")
        finally:
            logger.info("Keyboard listener stopped.")
    
    def cycle_next_window(self):
        """Cycle to the next window."""
        try:
            logger.info("Cycling to next window")
            self.accessibility_manager.cycle_windows("next")
        except Exception as e:
            logger.error(f"Error cycling to next window: {e}")
    
    def cycle_prev_window(self):
        """Cycle to the previous window."""
        try:
            logger.info("Cycling to previous window")
            self.accessibility_manager.cycle_windows("previous")
        except Exception as e:
            logger.error(f"Error cycling to previous window: {e}")
    
    def focus_lockdown_browser(self):
        """Focus the LockDown Browser window if it exists."""
        try:
            logger.info("Attempting to focus LockDown Browser")
            lockdown_window = self.accessibility_manager.find_window_by_name(self.target_app_name, True)
            if lockdown_window:
                self.accessibility_manager.set_window_focus(lockdown_window)
                logger.info("LockDown Browser focused")
            else:
                logger.info("LockDown Browser window not found")
        except Exception as e:
            logger.error(f"Error focusing LockDown Browser: {e}")
    
    def focus_other_window(self):
        """Focus another window from the alt windows list."""
        try:
            # Get all windows
            windows = self.accessibility_manager.get_all_windows()
            
            # Filter out the LockDown Browser
            filtered_windows = [w for w in windows if self.target_app_name not in getattr(w, 'CurrentName', '')]
            
            if filtered_windows:
                # Focus the first non-LockDown Browser window
                self.accessibility_manager.set_window_focus(filtered_windows[0])
                logger.info(f"Focused other window: {getattr(filtered_windows[0], 'CurrentName', 'Unknown')}")
            else:
                logger.info("No other windows found to focus")
        except Exception as e:
            logger.error(f"Error focusing other window: {e}")
    
    def take_screenshot(self):
        """Take a screenshot of the current screen or active window."""
        try:
            logger.info("Taking screenshot")
            
            # Try to get the name of the foreground window
            import win32gui
            foreground_hwnd = win32gui.GetForegroundWindow()
            window_name = None
            
            try:
                window_name = win32gui.GetWindowText(foreground_hwnd)
                logger.info(f"Current foreground window: {window_name}")
            except:
                pass
            
            # Take the screenshot using the proxy capture system
            filename = self.screen_capture.capture_screenshot(window_name if window_name else None)
            
            if not filename:
                logger.error("Failed to capture screenshot with any method")
                return
            
            logger.info(f"Screenshot saved to {filename}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
    
    def minimize_all_except_target(self):
        """Minimize all windows except the target application."""
        try:
            logger.info(f"Minimizing all windows except {self.target_app_name}")
            self.accessibility_manager.minimize_all_windows_except(self.target_app_name)
        except Exception as e:
            logger.error(f"Error minimizing windows: {e}")
    
    def restore_all_windows(self):
        """Restore all previously minimized windows."""
        try:
            logger.info("Restoring all windows")
            self.accessibility_manager.restore_all_windows()
        except Exception as e:
            logger.error(f"Error restoring windows: {e}")


if __name__ == "__main__":
    try:
        # Create and start the controller
        controller = AccessibilityController()
        controller.start()
        
        print("UndownUnlock Accessibility Controller started")
        print("Use the following keyboard shortcuts:")
        print("  Ctrl+Tab: Cycle to next window")
        print("  Ctrl+Shift+Tab: Cycle to previous window")
        print("  Ctrl+L: Focus LockDown Browser")
        print("  Ctrl+O: Focus other window")
        print("  Ctrl+Shift+S: Take screenshot")
        print("  Ctrl+M: Minimize all except LockDown Browser")
        print("  Ctrl+R: Restore all windows")
        print("Named Pipe Server running for IPC with other components")
        print("Press Ctrl+C to exit")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Clean up
        if 'controller' in locals():
            controller.stop() 