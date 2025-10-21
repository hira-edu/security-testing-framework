#!/usr/bin/env python
"""
Dashboard Example for UndownUnlock Accessibility Framework

This script demonstrates how to build a simple monitoring dashboard
using the UndownUnlock accessibility framework, showing real-time
statistics about window activity and focus changes.

Requirements:
- Tkinter for the GUI
- matplotlib for charts
- pandas for data analysis
"""

import os
import sys
import time
import logging
import threading
import json
import random
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend for matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation

# Import the remote client for Named Pipe communication
from remote_client import RemoteClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Dashboard")


class WindowActivityTracker:
    """
    Tracks window activity and maintains statistics about window usage.
    """
    
    def __init__(self, pipe_name: str = "UndownUnlockAccessibilityPipe", 
                 history_size: int = 100):
        """
        Initialize the window activity tracker.
        
        Args:
            pipe_name: Named pipe to connect to
            history_size: How many data points to keep in history
        """
        self.client = RemoteClient(pipe_name)
        self.history_size = history_size
        self.running = False
        self.monitor_thread = None
        
        # Data structures for tracking
        self.window_list = []
        self.window_count_history = deque(maxlen=history_size)
        self.focus_history = deque(maxlen=history_size)
        self.window_duration = defaultdict(float)  # Window name -> duration in seconds
        self.current_focus = None
        self.last_update_time = None
        
        # Callback for when data updates
        self.update_callbacks = []
        
        logger.info("Window Activity Tracker initialized")
    
    def start(self):
        """Start tracking window activity."""
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
        
        logger.info("Window activity tracking started")
        self.last_update_time = time.time()
        return True
    
    def stop(self):
        """Stop tracking window activity."""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        self.client.disconnect()
        logger.info("Window activity tracking stopped")
    
    def register_update_callback(self, callback):
        """Register a callback function that will be called when data updates."""
        self.update_callbacks.append(callback)
    
    def _notify_update(self):
        """Notify all registered callbacks that data has been updated."""
        for callback in self.update_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop that tracks window activity."""
        update_interval = 1.0  # Update every second
        
        while self.running:
            try:
                # Get list of windows
                response = self.client.get_window_list()
                
                if response.get("status") != "success":
                    logger.warning(f"Failed to get window list: {response.get('message')}")
                    time.sleep(update_interval)
                    continue
                
                # Get current time
                current_time = time.time()
                timestamp = datetime.now()
                
                # Process window list
                self.window_list = response.get("windows", [])
                window_count = response.get("count", 0)
                
                # Add to history
                self.window_count_history.append((timestamp, window_count))
                
                # Update duration for current focus
                if self.current_focus and self.last_update_time:
                    duration = current_time - self.last_update_time
                    self.window_duration[self.current_focus] += duration
                
                # Attempt to determine current focus
                # In a real implementation, we would get this from the controller
                # For this example, we'll just pick a random window from the list
                if self.window_list:
                    new_focus = random.choice(self.window_list)
                    if new_focus != self.current_focus:
                        self.focus_history.append((timestamp, new_focus))
                        self.current_focus = new_focus
                
                self.last_update_time = current_time
                
                # Notify any registered callbacks
                self._notify_update()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                
            time.sleep(update_interval)
    
    def get_window_count_data(self) -> List[Tuple[datetime, int]]:
        """Get window count history data."""
        return list(self.window_count_history)
    
    def get_focus_history_data(self) -> List[Tuple[datetime, str]]:
        """Get focus history data."""
        return list(self.focus_history)
    
    def get_window_duration_data(self) -> Dict[str, float]:
        """Get window duration data."""
        return dict(self.window_duration)
    
    def get_current_window_list(self) -> List[str]:
        """Get the current list of windows."""
        return self.window_list
    
    def get_window_count(self) -> int:
        """Get the current number of windows."""
        return len(self.window_list)
    
    def get_current_focus(self) -> Optional[str]:
        """Get the currently focused window."""
        return self.current_focus
    
    def focus_window(self, window_name: str) -> bool:
        """Focus a specific window by name."""
        response = self.client.focus_window(window_name)
        return response.get("status") == "success"
    
    def cycle_window(self, direction: str = "next") -> bool:
        """Cycle to the next or previous window."""
        response = self.client.cycle_window(direction)
        return response.get("status") == "success"
    
    def minimize_windows(self, exception_window: Optional[str] = None) -> bool:
        """Minimize all windows except the specified one."""
        response = self.client.minimize_windows(exception_window)
        return response.get("status") == "success"
    
    def restore_windows(self) -> bool:
        """Restore all minimized windows."""
        response = self.client.restore_windows()
        return response.get("status") == "success"
    
    def take_screenshot(self) -> Optional[str]:
        """Take a screenshot and return the path."""
        response = self.client.take_screenshot()
        if response.get("status") == "success":
            return response.get("screenshot_path")
        return None


class DashboardApp:
    """
    Main dashboard application that displays window activity statistics.
    """
    
    def __init__(self, root):
        """
        Initialize the dashboard application.
        
        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.root.title("UndownUnlock Accessibility Dashboard")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Set style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use 'clam' theme for better visuals
        
        # Create tracker
        self.tracker = WindowActivityTracker()
        self.tracker.register_update_callback(self.update_dashboard)
        
        # Create UI
        self.create_ui()
        
        # Track whether dashboard is running
        self.running = False
    
    def create_ui(self):
        """Create the dashboard UI."""
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status frame at the top
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding=10)
        self.status_frame.pack(fill=tk.X, pady=5)
        
        # Connect button
        self.connect_button = ttk.Button(self.status_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(self.status_frame, text="Not connected")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Current stats frame
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="Current Statistics", padding=10)
        self.stats_frame.pack(fill=tk.X, pady=5)
        
        # Window count
        self.window_count_label = ttk.Label(self.stats_frame, text="Windows: 0")
        self.window_count_label.grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        
        # Current focus
        self.focus_label = ttk.Label(self.stats_frame, text="Focus: None")
        self.focus_label.grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        
        # Actions frame
        self.actions_frame = ttk.LabelFrame(self.main_frame, text="Actions", padding=10)
        self.actions_frame.pack(fill=tk.X, pady=5)
        
        # Cycle next button
        self.cycle_next_button = ttk.Button(self.actions_frame, text="Cycle Next", 
                                          command=lambda: self.tracker.cycle_window("next"))
        self.cycle_next_button.grid(row=0, column=0, padx=5, pady=2)
        
        # Cycle previous button
        self.cycle_prev_button = ttk.Button(self.actions_frame, text="Cycle Previous", 
                                          command=lambda: self.tracker.cycle_window("previous"))
        self.cycle_prev_button.grid(row=0, column=1, padx=5, pady=2)
        
        # Minimize button
        self.minimize_button = ttk.Button(self.actions_frame, text="Minimize Others", 
                                        command=self.minimize_others)
        self.minimize_button.grid(row=0, column=2, padx=5, pady=2)
        
        # Restore button
        self.restore_button = ttk.Button(self.actions_frame, text="Restore All", 
                                       command=self.tracker.restore_windows)
        self.restore_button.grid(row=0, column=3, padx=5, pady=2)
        
        # Screenshot button
        self.screenshot_button = ttk.Button(self.actions_frame, text="Take Screenshot", 
                                          command=self.take_screenshot)
        self.screenshot_button.grid(row=0, column=4, padx=5, pady=2)
        
        # Window list frame
        self.window_list_frame = ttk.LabelFrame(self.main_frame, text="Window List", padding=10)
        self.window_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Window list with scrollbar
        self.window_list_scrollbar = ttk.Scrollbar(self.window_list_frame)
        self.window_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.window_listbox = tk.Listbox(self.window_list_frame, 
                                        yscrollcommand=self.window_list_scrollbar.set)
        self.window_listbox.pack(fill=tk.BOTH, expand=True)
        self.window_list_scrollbar.config(command=self.window_listbox.yview)
        
        # Focus selected button
        self.focus_selected_button = ttk.Button(self.window_list_frame, text="Focus Selected", 
                                              command=self.focus_selected)
        self.focus_selected_button.pack(pady=5)
        
        # Graphs frame
        self.graphs_frame = ttk.LabelFrame(self.main_frame, text="Activity Graphs", padding=10)
        self.graphs_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create notebook for multiple graphs
        self.notebook = ttk.Notebook(self.graphs_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Window count history tab
        self.window_count_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.window_count_frame, text="Window Count")
        
        # Window duration tab
        self.window_duration_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.window_duration_frame, text="Window Duration")
        
        # Create figures for plots
        self.create_plots()
        
        # Disable all action buttons initially
        self.set_buttons_state(tk.DISABLED)
    
    def create_plots(self):
        """Create matplotlib plots for the dashboard."""
        # Window count plot
        self.window_count_fig = Figure(figsize=(5, 3), dpi=100)
        self.window_count_ax = self.window_count_fig.add_subplot(111)
        self.window_count_ax.set_title("Window Count History")
        self.window_count_ax.set_xlabel("Time")
        self.window_count_ax.set_ylabel("Window Count")
        self.window_count_canvas = FigureCanvasTkAgg(self.window_count_fig, master=self.window_count_frame)
        self.window_count_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Window duration plot
        self.window_duration_fig = Figure(figsize=(5, 3), dpi=100)
        self.window_duration_ax = self.window_duration_fig.add_subplot(111)
        self.window_duration_ax.set_title("Window Focus Duration")
        self.window_duration_ax.set_xlabel("Window")
        self.window_duration_ax.set_ylabel("Duration (seconds)")
        self.window_duration_canvas = FigureCanvasTkAgg(self.window_duration_fig, master=self.window_duration_frame)
        self.window_duration_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_dashboard(self):
        """Update the dashboard with current data."""
        if not self.running:
            return
        
        # Update window count label
        window_count = self.tracker.get_window_count()
        self.window_count_label.config(text=f"Windows: {window_count}")
        
        # Update focus label
        current_focus = self.tracker.get_current_focus()
        focus_text = current_focus if current_focus else "None"
        self.focus_label.config(text=f"Focus: {focus_text}")
        
        # Update window list
        window_list = self.tracker.get_current_window_list()
        self.window_listbox.delete(0, tk.END)
        for window in window_list:
            self.window_listbox.insert(tk.END, window)
        
        # Update window count plot
        window_count_data = self.tracker.get_window_count_data()
        if window_count_data:
            timestamps, counts = zip(*window_count_data)
            
            self.window_count_ax.clear()
            self.window_count_ax.set_title("Window Count History")
            self.window_count_ax.set_xlabel("Time")
            self.window_count_ax.set_ylabel("Window Count")
            self.window_count_ax.plot(timestamps, counts, 'b-')
            self.window_count_ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.window_count_fig.autofmt_xdate(rotation=45)
            self.window_count_canvas.draw()
        
        # Update window duration plot
        window_duration_data = self.tracker.get_window_duration_data()
        if window_duration_data:
            # Sort by duration
            sorted_data = sorted(window_duration_data.items(), key=lambda x: x[1], reverse=True)
            # Take top 5 for readability
            top_data = sorted_data[:5]
            windows, durations = zip(*top_data)
            
            self.window_duration_ax.clear()
            self.window_duration_ax.set_title("Top 5 Windows by Focus Duration")
            self.window_duration_ax.set_xlabel("Window")
            self.window_duration_ax.set_ylabel("Duration (seconds)")
            
            # Truncate window names for display
            display_names = [w[:20] + "..." if len(w) > 20 else w for w in windows]
            
            bars = self.window_duration_ax.bar(display_names, durations)
            
            # Add values on top of bars
            for bar in bars:
                height = bar.get_height()
                self.window_duration_ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.1,
                    f'{height:.1f}',
                    ha='center', va='bottom', rotation=0
                )
            
            self.window_duration_ax.set_xticklabels(display_names, rotation=45, ha='right')
            self.window_duration_fig.tight_layout()
            self.window_duration_canvas.draw()
    
    def toggle_connection(self):
        """Toggle connection to the accessibility controller."""
        if not self.running:
            # Connect
            if self.tracker.start():
                self.running = True
                self.status_label.config(text="Connected")
                self.connect_button.config(text="Disconnect")
                self.set_buttons_state(tk.NORMAL)
                
                # Schedule periodic updates
                self.root.after(1000, self.schedule_update)
            else:
                messagebox.showerror("Connection Error", 
                                   "Failed to connect to the accessibility controller.\n"
                                   "Make sure it is running.")
        else:
            # Disconnect
            self.tracker.stop()
            self.running = False
            self.status_label.config(text="Not connected")
            self.connect_button.config(text="Connect")
            self.set_buttons_state(tk.DISABLED)
    
    def set_buttons_state(self, state):
        """Set the state of all action buttons."""
        buttons = [
            self.cycle_next_button,
            self.cycle_prev_button,
            self.minimize_button,
            self.restore_button,
            self.screenshot_button,
            self.focus_selected_button
        ]
        
        for button in buttons:
            button.config(state=state)
    
    def schedule_update(self):
        """Schedule the next dashboard update."""
        if self.running:
            self.update_dashboard()
            self.root.after(1000, self.schedule_update)
    
    def focus_selected(self):
        """Focus the selected window in the listbox."""
        selection = self.window_listbox.curselection()
        if selection:
            index = selection[0]
            window_name = self.window_listbox.get(index)
            self.tracker.focus_window(window_name)
    
    def minimize_others(self):
        """Minimize all windows except the current focus."""
        current_focus = self.tracker.get_current_focus()
        if current_focus:
            self.tracker.minimize_windows(current_focus)
        else:
            messagebox.showinfo("No Focus", "No window is currently in focus.")
    
    def take_screenshot(self):
        """Take a screenshot and show confirmation."""
        screenshot_path = self.tracker.take_screenshot()
        if screenshot_path:
            messagebox.showinfo("Screenshot", f"Screenshot saved to: {screenshot_path}")
        else:
            messagebox.showerror("Screenshot Error", "Failed to take screenshot.")


def main():
    """Main entry point for the dashboard example."""
    root = tk.Tk()
    app = DashboardApp(root)
    
    # Handle window close
    def on_closing():
        if app.running:
            app.toggle_connection()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main() 