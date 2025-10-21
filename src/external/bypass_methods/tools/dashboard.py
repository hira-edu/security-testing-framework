#!/usr/bin/env python3
"""
Monitoring Dashboard for UndownUnlock System
Provides real-time performance monitoring and visualization
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import json
import sys
import os
from collections import deque
import random

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from tools.controller import Controller
from utils.performance_monitor import PerformanceMonitor

class DashboardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UndownUnlock Dashboard")
        self.root.geometry("1200x800")
        
        # Initialize controller
        self.controller = Controller()
        self.initialized = False
        
        # Performance data storage
        self.performance_data = {
            'cpu_usage': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'frame_rate': deque(maxlen=100),
            'frame_time': deque(maxlen=100),
            'active_hooks': deque(maxlen=100),
            'captured_frames': deque(maxlen=100)
        }
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        
        self.setup_ui()
        self.initialize_system()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        self.create_control_panel(main_frame)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left panel - System status
        self.create_status_panel(content_frame)
        
        # Right panel - Performance graphs
        self.create_performance_panel(content_frame)
    
    def create_control_panel(self, parent):
        """Create top control panel"""
        control_frame = ttk.LabelFrame(parent, text="Dashboard Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        ttk.Button(control_frame, text="Initialize System", command=self.initialize_system).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Start Monitoring", command=self.start_monitoring).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Stop Monitoring", command=self.stop_monitoring).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Export Data", command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Data", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        self.status_indicator = ttk.Label(control_frame, text="Not Initialized", foreground="red")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)
    
    def create_status_panel(self, parent):
        """Create system status panel"""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding=10)
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # System health indicators
        health_frame = ttk.Frame(status_frame)
        health_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(health_frame, text="System Health", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        self.health_indicators = {}
        health_items = [
            ("Controller Status", "Not Initialized"),
            ("Hook Status", "Not Installed"),
            ("Capture Status", "Not Active"),
            ("Memory Status", "Normal"),
            ("Performance Status", "Normal")
        ]
        
        for label, value in health_items:
            frame = ttk.Frame(health_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=f"{label}:").pack(side=tk.LEFT)
            self.health_indicators[label] = ttk.Label(frame, text=value, foreground="red")
            self.health_indicators[label].pack(side=tk.RIGHT)
        
        # Current metrics
        metrics_frame = ttk.LabelFrame(status_frame, text="Current Metrics", padding=10)
        metrics_frame.pack(fill=tk.BOTH, expand=True)
        
        self.metric_labels = {}
        metric_items = [
            ("CPU Usage", "0%"),
            ("Memory Usage", "0 MB"),
            ("Frame Rate", "0 FPS"),
            ("Frame Time", "0 ms"),
            ("Active Hooks", "0"),
            ("Captured Frames", "0"),
            ("Target Process", "None"),
            ("Uptime", "0:00:00")
        ]
        
        for i, (label, value) in enumerate(metric_items):
            row = i // 2
            col = i % 2 * 2
            
            ttk.Label(metrics_frame, text=f"{label}:").grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.metric_labels[label] = ttk.Label(metrics_frame, text=value, font=("Arial", 10, "bold"))
            self.metric_labels[label].grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
        
        # Alerts panel
        alerts_frame = ttk.LabelFrame(status_frame, text="System Alerts", padding=10)
        alerts_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.alerts_text = tk.Text(alerts_frame, height=6, wrap=tk.WORD)
        alerts_scrollbar = ttk.Scrollbar(alerts_frame, orient=tk.VERTICAL, command=self.alerts_text.yview)
        self.alerts_text.configure(yscrollcommand=alerts_scrollbar.set)
        
        self.alerts_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alerts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_performance_panel(self, parent):
        """Create performance monitoring panel"""
        perf_frame = ttk.LabelFrame(parent, text="Performance Monitoring", padding=10)
        perf_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        if MATPLOTLIB_AVAILABLE:
            # Create matplotlib figure
            self.fig = Figure(figsize=(8, 6), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.fig, perf_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Create subplots
            self.ax1 = self.fig.add_subplot(2, 2, 1)  # CPU Usage
            self.ax2 = self.fig.add_subplot(2, 2, 2)  # Memory Usage
            self.ax3 = self.fig.add_subplot(2, 2, 3)  # Frame Rate
            self.ax4 = self.fig.add_subplot(2, 2, 4)  # Frame Time
            
            # Initialize plots
            self.setup_plots()
        else:
            # Fallback to text-based display
            ttk.Label(perf_frame, text="Matplotlib not available", foreground="red").pack()
            ttk.Label(perf_frame, text="Install matplotlib for graphs: pip install matplotlib").pack()
    
    def setup_plots(self):
        """Setup matplotlib plots"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # CPU Usage plot
        self.ax1.set_title('CPU Usage (%)')
        self.ax1.set_ylim(0, 100)
        self.ax1.grid(True)
        self.cpu_line, = self.ax1.plot([], [], 'b-', linewidth=2)
        
        # Memory Usage plot
        self.ax2.set_title('Memory Usage (MB)')
        self.ax2.set_ylim(0, 500)
        self.ax2.grid(True)
        self.memory_line, = self.ax2.plot([], [], 'g-', linewidth=2)
        
        # Frame Rate plot
        self.ax3.set_title('Frame Rate (FPS)')
        self.ax3.set_ylim(0, 120)
        self.ax3.grid(True)
        self.fps_line, = self.ax3.plot([], [], 'r-', linewidth=2)
        
        # Frame Time plot
        self.ax4.set_title('Frame Time (ms)')
        self.ax4.set_ylim(0, 50)
        self.ax4.grid(True)
        self.frame_time_line, = self.ax4.plot([], [], 'm-', linewidth=2)
        
        # Adjust layout
        self.fig.tight_layout()
    
    def initialize_system(self):
        """Initialize the UndownUnlock system"""
        try:
            if self.controller.initialize():
                self.initialized = True
                self.status_indicator.config(text="Initialized", foreground="green")
                self.health_indicators["Controller Status"].config(text="Initialized", foreground="green")
                self.add_alert("System initialized successfully", "INFO")
            else:
                self.add_alert("Failed to initialize system", "ERROR")
        except Exception as e:
            self.add_alert(f"Initialization error: {e}", "ERROR")
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.initialized:
            self.add_alert("System not initialized", "WARNING")
            return
        
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_performance, daemon=True)
        self.monitor_thread.start()
        self.add_alert("Performance monitoring started", "INFO")
        
        if MATPLOTLIB_AVAILABLE:
            self.ani = animation.FuncAnimation(self.fig, self.update_plots, interval=1000, blit=False)
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'ani'):
            self.ani.event_source.stop()
        
        self.add_alert("Performance monitoring stopped", "INFO")
    
    def monitor_performance(self):
        """Performance monitoring thread"""
        start_time = time.time()
        
        while self.monitoring:
            try:
                # Simulate performance metrics (replace with real data)
                cpu_usage = random.uniform(10, 80)
                memory_usage = random.uniform(50, 200)
                frame_rate = random.uniform(30, 60)
                frame_time = 1000 / frame_rate if frame_rate > 0 else 0
                active_hooks = random.randint(0, 5)
                captured_frames = random.randint(0, 1000)
                
                # Store data
                self.performance_data['cpu_usage'].append(cpu_usage)
                self.performance_data['memory_usage'].append(memory_usage)
                self.performance_data['frame_rate'].append(frame_rate)
                self.performance_data['frame_time'].append(frame_time)
                self.performance_data['active_hooks'].append(active_hooks)
                self.performance_data['captured_frames'].append(captured_frames)
                
                # Update UI in main thread
                uptime = time.time() - start_time
                self.root.after(0, self.update_metrics, cpu_usage, memory_usage, 
                              frame_rate, frame_time, active_hooks, captured_frames, uptime)
                
                # Check for alerts
                self.check_alerts(cpu_usage, memory_usage, frame_rate)
                
                time.sleep(1)
            except Exception as e:
                self.add_alert(f"Monitoring error: {e}", "ERROR")
                break
    
    def update_metrics(self, cpu, memory, fps, frame_time, hooks, frames, uptime):
        """Update metrics in UI"""
        # Update metric labels
        self.metric_labels["CPU Usage"].config(text=f"{cpu:.1f}%")
        self.metric_labels["Memory Usage"].config(text=f"{memory:.1f} MB")
        self.metric_labels["Frame Rate"].config(text=f"{fps:.1f} FPS")
        self.metric_labels["Frame Time"].config(text=f"{frame_time:.1f} ms")
        self.metric_labels["Active Hooks"].config(text=str(hooks))
        self.metric_labels["Captured Frames"].config(text=str(frames))
        
        # Update uptime
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        self.metric_labels["Uptime"].config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Update health indicators
        self.update_health_indicators(cpu, memory, fps, hooks)
    
    def update_health_indicators(self, cpu, memory, fps, hooks):
        """Update system health indicators"""
        # Hook status
        if hooks > 0:
            self.health_indicators["Hook Status"].config(text="Installed", foreground="green")
        else:
            self.health_indicators["Hook Status"].config(text="Not Installed", foreground="red")
        
        # Capture status (simplified)
        if fps > 0:
            self.health_indicators["Capture Status"].config(text="Active", foreground="green")
        else:
            self.health_indicators["Capture Status"].config(text="Not Active", foreground="red")
        
        # Memory status
        if memory < 100:
            self.health_indicators["Memory Status"].config(text="Normal", foreground="green")
        elif memory < 200:
            self.health_indicators["Memory Status"].config(text="High", foreground="orange")
        else:
            self.health_indicators["Memory Status"].config(text="Critical", foreground="red")
        
        # Performance status
        if cpu < 50:
            self.health_indicators["Performance Status"].config(text="Normal", foreground="green")
        elif cpu < 80:
            self.health_indicators["Performance Status"].config(text="High", foreground="orange")
        else:
            self.health_indicators["Performance Status"].config(text="Critical", foreground="red")
    
    def check_alerts(self, cpu, memory, fps):
        """Check for system alerts"""
        if cpu > 80:
            self.add_alert(f"High CPU usage: {cpu:.1f}%", "WARNING")
        
        if memory > 200:
            self.add_alert(f"High memory usage: {memory:.1f} MB", "WARNING")
        
        if fps < 30:
            self.add_alert(f"Low frame rate: {fps:.1f} FPS", "WARNING")
    
    def add_alert(self, message, level="INFO"):
        """Add alert to alerts panel"""
        timestamp = time.strftime("%H:%M:%S")
        alert_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.alerts_text.insert(tk.END, alert_entry)
        self.alerts_text.see(tk.END)
        
        # Limit alerts
        lines = self.alerts_text.get(1.0, tk.END).split('\n')
        if len(lines) > 50:
            self.alerts_text.delete(1.0, f"{len(lines)-25}.0")
    
    def update_plots(self, frame):
        """Update matplotlib plots"""
        if not MATPLOTLIB_AVAILABLE or not self.monitoring:
            return
        
        try:
            # Get data
            cpu_data = list(self.performance_data['cpu_usage'])
            memory_data = list(self.performance_data['memory_usage'])
            fps_data = list(self.performance_data['frame_rate'])
            frame_time_data = list(self.performance_data['frame_time'])
            
            # Create time axis
            time_axis = list(range(len(cpu_data)))
            
            # Update plots
            self.cpu_line.set_data(time_axis, cpu_data)
            self.memory_line.set_data(time_axis, memory_data)
            self.fps_line.set_data(time_axis, fps_data)
            self.frame_time_line.set_data(time_axis, frame_time_data)
            
            # Update axis limits
            if len(time_axis) > 0:
                self.ax1.set_xlim(0, max(time_axis))
                self.ax2.set_xlim(0, max(time_axis))
                self.ax3.set_xlim(0, max(time_axis))
                self.ax4.set_xlim(0, max(time_axis))
            
            return self.cpu_line, self.memory_line, self.fps_line, self.frame_time_line
        except Exception as e:
            self.add_alert(f"Plot update error: {e}", "ERROR")
            return []
    
    def export_data(self):
        """Export performance data"""
        try:
            data = {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'performance_data': {
                    'cpu_usage': list(self.performance_data['cpu_usage']),
                    'memory_usage': list(self.performance_data['memory_usage']),
                    'frame_rate': list(self.performance_data['frame_rate']),
                    'frame_time': list(self.performance_data['frame_time']),
                    'active_hooks': list(self.performance_data['active_hooks']),
                    'captured_frames': list(self.performance_data['captured_frames'])
                },
                'current_metrics': {
                    label: self.metric_labels[label].cget('text')
                    for label in self.metric_labels
                }
            }
            
            filename = f"dashboard_data_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.add_alert(f"Data exported to {filename}", "INFO")
        except Exception as e:
            self.add_alert(f"Export error: {e}", "ERROR")
    
    def clear_data(self):
        """Clear performance data"""
        for data_list in self.performance_data.values():
            data_list.clear()
        
        self.add_alert("Performance data cleared", "INFO")

def main():
    """Main function"""
    root = tk.Tk()
    app = DashboardGUI(root)
    
    # Handle window close
    def on_closing():
        if app.monitoring:
            app.stop_monitoring()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 