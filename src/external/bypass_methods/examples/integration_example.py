#!/usr/bin/env python
"""
Integration Example for UndownUnlock Accessibility Framework

This script demonstrates how to integrate the accessibility framework
with other applications using the Named Pipes client-server architecture.
It shows how to:
1. Control window focus programmatically
2. Take screenshots automatically when detecting specific windows
3. Monitor window changes and respond to events
4. Integrate with external applications
"""

import os
import sys
import time
import logging
import threading
import argparse
from typing import Dict, Any, List, Optional
import json

# Import the remote client for Named Pipe communication
from remote_client import RemoteClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integration_example.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IntegrationExample")


class WindowActivityMonitor:
    """
    Monitors window activity and performs actions based on window changes.
    Demonstrates how external applications can use the accessibility framework.
    """
    
    def __init__(self, pipe_name: str = "UndownUnlockAccessibilityPipe", 
                 target_app: str = "LockDown Browser", 
                 monitor_interval: float = 5.0):
        """
        Initialize the window activity monitor.
        
        Args:
            pipe_name: Named pipe to connect to
            target_app: Target application to monitor
            monitor_interval: Interval in seconds to check window state
        """
        self.client = RemoteClient(pipe_name)
        self.target_app = target_app
        self.monitor_interval = monitor_interval
        self.running = False
        self.monitor_thread = None
        self.window_list = []
        self.target_window_active = False
        self.screenshot_dir = "auto_screenshots"
        
        # Create screenshot directory if it doesn't exist
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        logger.info(f"Window Activity Monitor initialized with target: {target_app}")
    
    def start(self):
        """Start monitoring window activity."""
        # Connect to the accessibility controller
        if not self.client.connect():
            logger.error("Failed to connect to the accessibility controller")
            return False
        
        logger.info("Connected to accessibility controller")
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Window activity monitoring started")
        return True
    
    def stop(self):
        """Stop monitoring window activity."""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        self.client.disconnect()
        logger.info("Window activity monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that checks window state periodically."""
        last_window_count = 0
        
        while self.running:
            try:
                # Get list of windows
                response = self.client.get_window_list()
                
                if response.get("status") != "success":
                    logger.warning(f"Failed to get window list: {response.get('message')}")
                    time.sleep(self.monitor_interval)
                    continue
                
                # Process window list
                self.window_list = response.get("windows", [])
                current_window_count = response.get("count", 0)
                
                # Check if target application is in the window list
                target_found = any(self.target_app.lower() in window.lower() for window in self.window_list)
                
                # Detect new window appearance
                if current_window_count > last_window_count:
                    self._handle_new_window(self.window_list)
                
                # Detect target window activation
                if target_found and not self.target_window_active:
                    self._handle_target_activated()
                    self.target_window_active = True
                elif not target_found and self.target_window_active:
                    self._handle_target_deactivated()
                    self.target_window_active = False
                
                last_window_count = current_window_count
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                
            time.sleep(self.monitor_interval)
    
    def _handle_new_window(self, window_list: List[str]):
        """Handle the appearance of a new window."""
        logger.info("New window detected")
        logger.info(f"Current windows: {window_list}")
        
        # Take a screenshot when a new window appears
        self._take_auto_screenshot("new_window")
    
    def _handle_target_activated(self):
        """Handle the activation of the target application."""
        logger.info(f"Target application '{self.target_app}' detected")
        
        # Example: Take a screenshot when target app is activated
        self._take_auto_screenshot("target_activated")
        
        # Example: Minimize other windows to help focus on target
        response = self.client.minimize_windows(self.target_app)
        if response.get("status") == "success":
            logger.info("Minimized other windows to focus on target application")
        else:
            logger.warning(f"Failed to minimize windows: {response.get('message')}")
    
    def _handle_target_deactivated(self):
        """Handle the deactivation of the target application."""
        logger.info(f"Target application '{self.target_app}' no longer detected")
        
        # Example: Take a screenshot when target app is deactivated
        self._take_auto_screenshot("target_deactivated")
        
        # Example: Restore minimized windows
        response = self.client.restore_windows()
        if response.get("status") == "success":
            logger.info("Restored minimized windows")
        else:
            logger.warning(f"Failed to restore windows: {response.get('message')}")
    
    def _take_auto_screenshot(self, event_type: str):
        """Take an automatic screenshot when certain events occur."""
        # For target app activation/deactivation, try to capture that specific window
        target_window = None
        if event_type in ["target_activated", "target_deactivated"]:
            target_window = self.target_app
        
        # Take screenshot with window targeting if applicable
        response = self.client.take_screenshot(target_window)
        
        if response.get("status") == "success":
            # Get the screenshot path from the response and copy it to our directory
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            src_path = response.get("screenshot_path", "")
            
            if src_path and os.path.exists(src_path):
                # Create our own copy with a descriptive name
                window_part = f"_{target_window}" if target_window else ""
                filename = f"{timestamp}_{event_type}{window_part}.png"
                dest_path = os.path.join(self.screenshot_dir, filename)
                
                try:
                    # Create a copy of the screenshot with our custom filename
                    with open(src_path, "rb") as src_file:
                        with open(dest_path, "wb") as dest_file:
                            dest_file.write(src_file.read())
                    
                    logger.info(f"Auto screenshot saved for event '{event_type}': {dest_path}")
                except Exception as e:
                    logger.error(f"Error copying screenshot: {e}")
            else:
                logger.warning(f"Screenshot path not found or invalid: {src_path}")
        else:
            logger.warning(f"Failed to take screenshot: {response.get('message')}")


class AutoFocusManager:
    """
    Automatically manages window focus based on a schedule or specific events.
    Shows how to programmatically control window focus for specific applications.
    """
    
    def __init__(self, pipe_name: str = "UndownUnlockAccessibilityPipe"):
        """Initialize the auto focus manager."""
        self.client = RemoteClient(pipe_name)
        self.running = False
        self.schedule_thread = None
        self.focus_schedule = []
        logger.info("Auto Focus Manager initialized")
    
    def start(self):
        """Start the auto focus manager."""
        # Connect to the accessibility controller
        if not self.client.connect():
            logger.error("Failed to connect to the accessibility controller")
            return False
        
        # Start schedule thread
        self.running = True
        self.schedule_thread = threading.Thread(target=self._schedule_loop)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()
        
        logger.info("Auto Focus Manager started")
        return True
    
    def stop(self):
        """Stop the auto focus manager."""
        self.running = False
        if self.schedule_thread and self.schedule_thread.is_alive():
            self.schedule_thread.join(timeout=5.0)
        
        self.client.disconnect()
        logger.info("Auto Focus Manager stopped")
    
    def add_focus_schedule(self, window_name: str, interval_seconds: float, 
                           duration_seconds: float = 10.0):
        """
        Add a window to the focus schedule.
        
        Args:
            window_name: Name of the window to focus
            interval_seconds: How often to focus this window
            duration_seconds: How long to keep focus before returning to previous window
        """
        self.focus_schedule.append({
            "window_name": window_name,
            "interval": interval_seconds,
            "duration": duration_seconds,
            "last_focus": 0,
            "active": True
        })
        logger.info(f"Added {window_name} to focus schedule (every {interval_seconds}s)")
    
    def remove_from_schedule(self, window_name: str):
        """Remove a window from the focus schedule."""
        self.focus_schedule = [item for item in self.focus_schedule 
                              if item["window_name"] != window_name]
        logger.info(f"Removed {window_name} from focus schedule")
    
    def _schedule_loop(self):
        """Main scheduling loop that manages window focus."""
        while self.running:
            current_time = time.time()
            
            for item in self.focus_schedule:
                if not item["active"]:
                    continue
                
                # Check if it's time to focus this window
                if current_time - item["last_focus"] >= item["interval"]:
                    # Try to focus the window
                    logger.info(f"Scheduled focus: {item['window_name']}")
                    response = self.client.focus_window(item["window_name"])
                    
                    if response.get("status") == "success":
                        logger.info(f"Successfully focused {item['window_name']}")
                        item["last_focus"] = current_time
                        
                        # If duration is specified, schedule return to previous window
                        if item["duration"] > 0:
                            # Wait for duration
                            time.sleep(item["duration"])
                            
                            # Cycle to previous window
                            self.client.cycle_window("previous")
                            logger.info("Returned to previous window after scheduled focus")
                    else:
                        logger.warning(f"Failed to focus {item['window_name']}: {response.get('message')}")
            
            # Sleep briefly to avoid consuming too much CPU
            time.sleep(1.0)


def demo_window_monitor(target_app: str, duration: int = 60):
    """
    Run a demonstration of the window activity monitor.
    
    Args:
        target_app: Target application to monitor
        duration: How long to run the demonstration (seconds)
    """
    print(f"\n===== Window Activity Monitor Demo ({duration}s) =====")
    print(f"Target application: {target_app}")
    
    # Create and start the monitor
    monitor = WindowActivityMonitor(target_app=target_app)
    
    if not monitor.start():
        print("Failed to start window monitor. Make sure the controller is running.")
        return
    
    try:
        print(f"Monitoring window activity for {duration} seconds...")
        print("Events will be logged and screenshots taken automatically.")
        print("Press Ctrl+C to stop early.")
        
        # Wait for the specified duration
        for i in range(duration):
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                print(f"{i} seconds elapsed...")
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    
    finally:
        # Stop the monitor
        monitor.stop()
        print("\nWindow Activity Monitor stopped.")
        print(f"Check 'auto_screenshots' directory for captured screenshots.")


def demo_auto_focus(duration: int = 60):
    """
    Run a demonstration of the auto focus manager.
    
    Args:
        duration: How long to run the demonstration (seconds)
    """
    print(f"\n===== Auto Focus Manager Demo ({duration}s) =====")
    
    # Create and start the focus manager
    focus_manager = AutoFocusManager()
    
    if not focus_manager.start():
        print("Failed to start auto focus manager. Make sure the controller is running.")
        return
    
    try:
        # Get list of windows for user to choose from
        client = RemoteClient()
        if not client.connect():
            print("Failed to connect to the accessibility controller.")
            return
        
        response = client.get_window_list()
        client.disconnect()
        
        if response.get("status") != "success":
            print(f"Failed to get window list: {response.get('message')}")
            return
        
        windows = response.get("windows", [])
        
        if not windows:
            print("No windows found to focus.")
            return
        
        # Display available windows
        print("\nAvailable windows:")
        for i, window in enumerate(windows):
            print(f"  {i+1}. {window}")
        
        # Ask user to choose windows for auto-focus
        try:
            choices = input("\nEnter window numbers to auto-focus (comma-separated): ")
            selected_indices = [int(x.strip()) - 1 for x in choices.split(",")]
            
            # Validate selections
            valid_indices = [i for i in selected_indices if 0 <= i < len(windows)]
            if not valid_indices:
                print("No valid windows selected.")
                return
            
            # Add selected windows to focus schedule
            for idx in valid_indices:
                window_name = windows[idx]
                focus_manager.add_focus_schedule(
                    window_name=window_name,
                    interval_seconds=15.0,  # Focus every 15 seconds
                    duration_seconds=5.0    # Keep focus for 5 seconds
                )
            
            print("\nAuto Focus Manager configured with the following schedule:")
            for idx in valid_indices:
                print(f"  - {windows[idx]}: Every 15 seconds (5 second duration)")
            
            print(f"\nRunning auto focus for {duration} seconds...")
            print("Press Ctrl+C to stop early.")
            
            # Wait for the specified duration
            time.sleep(duration)
            
        except (ValueError, IndexError) as e:
            print(f"Error in selection: {e}")
        
    except KeyboardInterrupt:
        print("\nAuto focus stopped by user.")
    
    finally:
        # Stop the focus manager
        focus_manager.stop()
        print("\nAuto Focus Manager stopped.")


def main():
    """Main entry point for the integration example."""
    parser = argparse.ArgumentParser(
        description="UndownUnlock Accessibility Framework Integration Example"
    )
    
    parser.add_argument("--mode", choices=["monitor", "focus", "both"], default="both",
                      help="Demo mode: window monitor, auto focus, or both")
    
    parser.add_argument("--target", default="LockDown Browser",
                      help="Target application for window monitoring")
    
    parser.add_argument("--duration", type=int, default=60,
                      help="Duration of the demonstration in seconds")
    
    args = parser.parse_args()
    
    print("\n=================================================")
    print("  UndownUnlock Accessibility Framework Integration")
    print("=================================================")
    print("\nThis demonstration shows how to integrate with the accessibility")
    print("framework for automated window management and monitoring.")
    print("\nMake sure the accessibility controller is running before continuing.")
    
    input("\nPress Enter to begin the demonstration...")
    
    if args.mode in ["monitor", "both"]:
        demo_window_monitor(args.target, args.duration)
    
    if args.mode in ["focus", "both"]:
        demo_auto_focus(args.duration)
    
    print("\n=================================================")
    print("  Integration Demonstration Complete")
    print("=================================================")
    print("\nThis example demonstrated how to:")
    print("  1. Monitor window activity and respond to changes")
    print("  2. Automatically manage window focus based on a schedule")
    print("  3. Take screenshots when specific events occur")
    print("  4. Integrate with the accessibility framework in your own applications")
    print("\nCheck the source code for implementation details and customize")
    print("it for your own use cases.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 