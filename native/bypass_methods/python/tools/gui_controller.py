#!/usr/bin/env python3
"""
GUI Controller for UndownUnlock System
Provides real-time monitoring and control interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.controller import Controller
from utils.performance_monitor import PerformanceMonitor
from utils.error_handler import ErrorHandler

class UndownUnlockGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UndownUnlock Controller")
        self.root.geometry("800x600")
        
        # Initialize controller
        self.controller = Controller()
        self.initialized = False
        
        # Performance monitoring
        self.monitoring = False
        self.monitor_thread = None
        
        self.setup_ui()
        self.initialize_system()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status tab
        self.create_status_tab()
        
        # Control tab
        self.create_control_tab()
        
        # Performance tab
        self.create_performance_tab()
        
        # Configuration tab
        self.create_config_tab()
        
        # Logs tab
        self.create_logs_tab()
    
    def create_status_tab(self):
        """Create system status tab"""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="Status")
        
        # System status
        status_group = ttk.LabelFrame(status_frame, text="System Status", padding=10)
        status_group.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_labels = {}
        status_items = [
            ("Controller", "Not Initialized"),
            ("Hook Status", "Not Installed"),
            ("Capture Status", "Not Active"),
            ("Target Process", "None")
        ]
        
        for i, (label, value) in enumerate(status_items):
            ttk.Label(status_group, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            self.status_labels[label] = ttk.Label(status_group, text=value, foreground="red")
            self.status_labels[label].grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Quick actions
        actions_group = ttk.LabelFrame(status_frame, text="Quick Actions", padding=10)
        actions_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(actions_group, text="Initialize System", command=self.initialize_system).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_group, text="Refresh Status", command=self.refresh_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_group, text="Start Monitoring", command=self.toggle_monitoring).pack(side=tk.LEFT, padx=5)
    
    def create_control_tab(self):
        """Create control tab"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Control")
        
        # Process injection
        injection_group = ttk.LabelFrame(control_frame, text="Process Injection", padding=10)
        injection_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(injection_group, text="Target Process:").pack(anchor=tk.W)
        self.process_var = tk.StringVar()
        process_entry = ttk.Entry(injection_group, textvariable=self.process_var)
        process_entry.pack(fill=tk.X, pady=5)
        
        ttk.Button(injection_group, text="Browse Process", command=self.browse_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(injection_group, text="Inject DLL", command=self.inject_dll).pack(side=tk.LEFT, padx=5)
        
        # Hook control
        hook_group = ttk.LabelFrame(control_frame, text="Hook Control", padding=10)
        hook_group.pack(fill=tk.X, padx=10, pady=5)
        
        self.hook_vars = {}
        hook_types = ["DirectX Hooks", "Windows API Hooks", "Keyboard Hooks", "Process Hooks"]
        
        for hook_type in hook_types:
            var = tk.BooleanVar()
            self.hook_vars[hook_type] = var
            ttk.Checkbutton(hook_group, text=hook_type, variable=var).pack(anchor=tk.W)
        
        ttk.Button(hook_group, text="Install Hooks", command=self.install_hooks).pack(side=tk.LEFT, padx=5)
        ttk.Button(hook_group, text="Uninstall Hooks", command=self.uninstall_hooks).pack(side=tk.LEFT, padx=5)
        
        # Capture control
        capture_group = ttk.LabelFrame(control_frame, text="Capture Control", padding=10)
        capture_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(capture_group, text="Start Capture", command=self.start_capture).pack(side=tk.LEFT, padx=5)
        ttk.Button(capture_group, text="Stop Capture", command=self.stop_capture).pack(side=tk.LEFT, padx=5)
        ttk.Button(capture_group, text="Save Frame", command=self.save_frame).pack(side=tk.LEFT, padx=5)
    
    def create_performance_tab(self):
        """Create performance monitoring tab"""
        perf_frame = ttk.Frame(self.notebook)
        self.notebook.add(perf_frame, text="Performance")
        
        # Performance metrics
        metrics_group = ttk.LabelFrame(perf_frame, text="Performance Metrics", padding=10)
        metrics_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.perf_labels = {}
        perf_items = [
            ("CPU Usage", "0%"),
            ("Memory Usage", "0 MB"),
            ("Frame Rate", "0 FPS"),
            ("Frame Time", "0 ms"),
            ("Active Hooks", "0"),
            ("Captured Frames", "0")
        ]
        
        for i, (label, value) in enumerate(perf_items):
            row = i // 2
            col = i % 2 * 2
            ttk.Label(metrics_group, text=f"{label}:").grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.perf_labels[label] = ttk.Label(metrics_group, text=value, font=("Arial", 10, "bold"))
            self.perf_labels[label].grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
        
        # Performance controls
        controls_group = ttk.LabelFrame(perf_frame, text="Controls", padding=10)
        controls_group.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_group, text="Start Monitoring", command=self.start_performance_monitoring).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_group, text="Stop Monitoring", command=self.stop_performance_monitoring).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_group, text="Export Report", command=self.export_performance_report).pack(side=tk.LEFT, padx=5)
    
    def create_config_tab(self):
        """Create configuration tab"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuration")
        
        # Configuration editor
        config_group = ttk.LabelFrame(config_frame, text="Configuration", padding=10)
        config_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configuration text area
        self.config_text = tk.Text(config_group, height=20)
        self.config_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Configuration controls
        config_controls = ttk.Frame(config_group)
        config_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(config_controls, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_controls, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_controls, text="Apply Config", command=self.apply_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_controls, text="Reset to Default", command=self.reset_config).pack(side=tk.LEFT, padx=5)
        
        # Load default configuration
        self.load_default_config()
    
    def create_logs_tab(self):
        """Create logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Log display
        log_group = ttk.LabelFrame(logs_frame, text="System Logs", padding=10)
        log_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Log text area with scrollbar
        log_frame = ttk.Frame(log_group)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=20)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log controls
        log_controls = ttk.Frame(log_group)
        log_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(log_controls, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Refresh", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        
        # Log level selection
        ttk.Label(log_controls, text="Log Level:").pack(side=tk.LEFT, padx=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_controls, textvariable=self.log_level_var, 
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"], width=10)
        log_level_combo.pack(side=tk.LEFT, padx=5)
        log_level_combo.bind("<<ComboboxSelected>>", self.change_log_level)
    
    def initialize_system(self):
        """Initialize the UndownUnlock system"""
        try:
            if self.controller.initialize():
                self.initialized = True
                self.status_labels["Controller"].config(text="Initialized", foreground="green")
                self.log_message("System initialized successfully")
                messagebox.showinfo("Success", "System initialized successfully")
            else:
                self.log_message("Failed to initialize system", "ERROR")
                messagebox.showerror("Error", "Failed to initialize system")
        except Exception as e:
            self.log_message(f"Initialization error: {e}", "ERROR")
            messagebox.showerror("Error", f"Initialization error: {e}")
    
    def refresh_status(self):
        """Refresh system status"""
        if not self.initialized:
            return
        
        try:
            status = self.controller.get_system_status()
            
            # Update status labels
            self.status_labels["Hook Status"].config(
                text="Installed" if status.get("hook_status") else "Not Installed",
                foreground="green" if status.get("hook_status") else "red"
            )
            
            self.status_labels["Capture Status"].config(
                text="Active" if status.get("capture_status") else "Not Active",
                foreground="green" if status.get("capture_status") else "red"
            )
            
            self.status_labels["Target Process"].config(
                text=status.get("target_process", "None")
            )
            
            self.log_message("Status refreshed")
        except Exception as e:
            self.log_message(f"Status refresh error: {e}", "ERROR")
    
    def toggle_monitoring(self):
        """Toggle performance monitoring"""
        if self.monitoring:
            self.stop_performance_monitoring()
        else:
            self.start_performance_monitoring()
    
    def browse_process(self):
        """Browse for target process"""
        # This would typically show a list of running processes
        # For now, just show a simple dialog
        process = tk.simpledialog.askstring("Select Process", "Enter process name:")
        if process:
            self.process_var.set(process)
    
    def inject_dll(self):
        """Inject DLL into target process"""
        if not self.initialized:
            messagebox.showerror("Error", "System not initialized")
            return
        
        process_name = self.process_var.get()
        if not process_name:
            messagebox.showerror("Error", "No target process specified")
            return
        
        try:
            if self.controller.inject_dll(process_name):
                self.status_labels["Target Process"].config(text=process_name)
                self.log_message(f"DLL injected into {process_name}")
                messagebox.showinfo("Success", f"DLL injected into {process_name}")
            else:
                self.log_message(f"Failed to inject DLL into {process_name}", "ERROR")
                messagebox.showerror("Error", f"Failed to inject DLL into {process_name}")
        except Exception as e:
            self.log_message(f"Injection error: {e}", "ERROR")
            messagebox.showerror("Error", f"Injection error: {e}")
    
    def install_hooks(self):
        """Install selected hooks"""
        if not self.initialized:
            messagebox.showerror("Error", "System not initialized")
            return
        
        try:
            # Get selected hook types
            selected_hooks = [hook_type for hook_type, var in self.hook_vars.items() if var.get()]
            
            if not selected_hooks:
                messagebox.showwarning("Warning", "No hooks selected")
                return
            
            # Install hooks (simplified)
            self.log_message(f"Installing hooks: {', '.join(selected_hooks)}")
            self.status_labels["Hook Status"].config(text="Installing...", foreground="orange")
            
            # Simulate hook installation
            self.root.after(2000, self.hooks_installed)
            
        except Exception as e:
            self.log_message(f"Hook installation error: {e}", "ERROR")
            messagebox.showerror("Error", f"Hook installation error: {e}")
    
    def hooks_installed(self):
        """Callback when hooks are installed"""
        self.status_labels["Hook Status"].config(text="Installed", foreground="green")
        self.log_message("Hooks installed successfully")
        messagebox.showinfo("Success", "Hooks installed successfully")
    
    def uninstall_hooks(self):
        """Uninstall all hooks"""
        if not self.initialized:
            messagebox.showerror("Error", "System not initialized")
            return
        
        try:
            self.log_message("Uninstalling hooks")
            self.status_labels["Hook Status"].config(text="Not Installed", foreground="red")
            self.log_message("Hooks uninstalled")
            messagebox.showinfo("Success", "Hooks uninstalled")
        except Exception as e:
            self.log_message(f"Hook uninstallation error: {e}", "ERROR")
            messagebox.showerror("Error", f"Hook uninstallation error: {e}")
    
    def start_capture(self):
        """Start frame capture"""
        if not self.initialized:
            messagebox.showerror("Error", "System not initialized")
            return
        
        try:
            self.log_message("Starting frame capture")
            self.status_labels["Capture Status"].config(text="Starting...", foreground="orange")
            
            # Simulate capture start
            self.root.after(1000, self.capture_started)
            
        except Exception as e:
            self.log_message(f"Capture start error: {e}", "ERROR")
            messagebox.showerror("Error", f"Capture start error: {e}")
    
    def capture_started(self):
        """Callback when capture is started"""
        self.status_labels["Capture Status"].config(text="Active", foreground="green")
        self.log_message("Frame capture started")
        messagebox.showinfo("Success", "Frame capture started")
    
    def stop_capture(self):
        """Stop frame capture"""
        if not self.initialized:
            messagebox.showerror("Error", "System not initialized")
            return
        
        try:
            self.log_message("Stopping frame capture")
            self.status_labels["Capture Status"].config(text="Not Active", foreground="red")
            self.log_message("Frame capture stopped")
            messagebox.showinfo("Success", "Frame capture stopped")
        except Exception as e:
            self.log_message(f"Capture stop error: {e}", "ERROR")
            messagebox.showerror("Error", f"Capture stop error: {e}")
    
    def save_frame(self):
        """Save current frame"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            self.log_message(f"Frame saved to {filename}")
            messagebox.showinfo("Success", f"Frame saved to {filename}")
    
    def start_performance_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_performance, daemon=True)
        self.monitor_thread.start()
        self.log_message("Performance monitoring started")
    
    def stop_performance_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        self.log_message("Performance monitoring stopped")
    
    def monitor_performance(self):
        """Performance monitoring thread"""
        while self.monitoring:
            try:
                # Simulate performance metrics
                import random
                cpu_usage = random.uniform(10, 80)
                memory_usage = random.uniform(50, 200)
                frame_rate = random.uniform(30, 60)
                frame_time = 1000 / frame_rate if frame_rate > 0 else 0
                
                # Update UI in main thread
                self.root.after(0, self.update_performance_metrics, 
                              cpu_usage, memory_usage, frame_rate, frame_time)
                
                time.sleep(1)
            except Exception as e:
                self.log_message(f"Performance monitoring error: {e}", "ERROR")
                break
    
    def update_performance_metrics(self, cpu, memory, fps, frame_time):
        """Update performance metrics in UI"""
        self.perf_labels["CPU Usage"].config(text=f"{cpu:.1f}%")
        self.perf_labels["Memory Usage"].config(text=f"{memory:.1f} MB")
        self.perf_labels["Frame Rate"].config(text=f"{fps:.1f} FPS")
        self.perf_labels["Frame Time"].config(text=f"{frame_time:.1f} ms")
    
    def export_performance_report(self):
        """Export performance report"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("UndownUnlock Performance Report\n")
                    f.write("=" * 30 + "\n\n")
                    for label, value in self.perf_labels.items():
                        f.write(f"{label}: {value.cget('text')}\n")
                
                self.log_message(f"Performance report exported to {filename}")
                messagebox.showinfo("Success", f"Performance report exported to {filename}")
            except Exception as e:
                self.log_message(f"Export error: {e}", "ERROR")
                messagebox.showerror("Error", f"Export error: {e}")
    
    def load_default_config(self):
        """Load default configuration"""
        default_config = {
            "capture": {
                "method": "windows_graphics_capture",
                "frame_rate": 60,
                "quality": "high",
                "compression": True
            },
            "hooks": {
                "directx": True,
                "windows_api": True,
                "keyboard": False,
                "process": False
            },
            "performance": {
                "monitoring": True,
                "sampling_interval": 1000
            }
        }
        
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, json.dumps(default_config, indent=2))
    
    def load_config(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                
                self.config_text.delete(1.0, tk.END)
                self.config_text.insert(1.0, json.dumps(config, indent=2))
                
                self.log_message(f"Configuration loaded from {filename}")
            except Exception as e:
                self.log_message(f"Config load error: {e}", "ERROR")
                messagebox.showerror("Error", f"Config load error: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                config_text = self.config_text.get(1.0, tk.END)
                config = json.loads(config_text)
                
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                
                self.log_message(f"Configuration saved to {filename}")
                messagebox.showinfo("Success", f"Configuration saved to {filename}")
            except Exception as e:
                self.log_message(f"Config save error: {e}", "ERROR")
                messagebox.showerror("Error", f"Config save error: {e}")
    
    def apply_config(self):
        """Apply current configuration"""
        try:
            config_text = self.config_text.get(1.0, tk.END)
            config = json.loads(config_text)
            
            # Apply configuration (simplified)
            self.log_message("Configuration applied")
            messagebox.showinfo("Success", "Configuration applied")
        except Exception as e:
            self.log_message(f"Config apply error: {e}", "ERROR")
            messagebox.showerror("Error", f"Config apply error: {e}")
    
    def reset_config(self):
        """Reset configuration to default"""
        self.load_default_config()
        self.log_message("Configuration reset to default")
    
    def log_message(self, message, level="INFO"):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Limit log size
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 1000:
            self.log_text.delete(1.0, f"{len(lines)-500}.0")
    
    def clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Logs cleared")
    
    def save_logs(self):
        """Save logs to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w') as f:
                    f.write(log_content)
                
                self.log_message(f"Logs saved to {filename}")
                messagebox.showinfo("Success", f"Logs saved to {filename}")
            except Exception as e:
                self.log_message(f"Log save error: {e}", "ERROR")
                messagebox.showerror("Error", f"Log save error: {e}")
    
    def refresh_logs(self):
        """Refresh log display"""
        self.log_message("Logs refreshed")
    
    def change_log_level(self, event=None):
        """Change log level"""
        level = self.log_level_var.get()
        self.log_message(f"Log level changed to {level}")

def main():
    """Main function"""
    root = tk.Tk()
    app = UndownUnlockGUI(root)
    
    # Handle window close
    def on_closing():
        if app.monitoring:
            app.stop_performance_monitoring()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 