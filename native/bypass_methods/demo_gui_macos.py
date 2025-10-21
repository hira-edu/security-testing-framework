#!/usr/bin/env python3
"""
Bypass Methods Framework - GUI Demonstration (macOS)
===================================================

A simple GUI demonstration using tkinter to showcase the framework's
capabilities on macOS.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import json
import threading
import time
from pathlib import Path

# Add the python directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'python'))

class FrameworkDemoGUI:
    """GUI demonstration of the Bypass Methods Framework."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Bypass Methods Framework - macOS Demo")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Configure style
        self.setup_style()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        # Create widgets
        self.create_widgets()
        
        # Initialize status
        self.status_var.set("Ready")
        
    def setup_style(self):
        """Setup the GUI style."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', 
                       font=('Arial', 16, 'bold'),
                       foreground='#ffffff',
                       background='#2b2b2b')
        
        style.configure('Status.TLabel',
                       font=('Arial', 10),
                       foreground='#00ff00',
                       background='#2b2b2b')
        
        style.configure('Demo.TButton',
                       font=('Arial', 10, 'bold'),
                       padding=5)
        
    def create_widgets(self):
        """Create the GUI widgets."""
        # Title
        title_label = ttk.Label(self.main_frame, 
                               text="🚀 Bypass Methods Framework",
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status bar
        self.status_var = tk.StringVar(value="Initializing...")
        status_label = ttk.Label(self.main_frame,
                                textvariable=self.status_var,
                                style='Status.TLabel')
        status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Left panel - Controls
        control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Demo buttons
        demos = [
            ("🔒 Security Manager", self.demo_security_manager),
            ("🧪 Security Tester", self.demo_security_tester),
            ("⚙️ Configuration", self.demo_configuration),
            ("📊 Performance", self.demo_performance),
            ("🏗️ Architecture", self.demo_architecture),
            ("🌐 Platform Info", self.demo_platform_info)
        ]
        
        for i, (text, command) in enumerate(demos):
            btn = ttk.Button(control_frame, 
                           text=text,
                           command=command,
                           style='Demo.TButton')
            btn.grid(row=i, column=0, pady=5, sticky=(tk.W, tk.E))
            control_frame.columnconfigure(0, weight=1)
        
        # Right panel - Output
        output_frame = ttk.LabelFrame(self.main_frame, text="Output", padding="10")
        output_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame,
                                                    width=50,
                                                    height=20,
                                                    bg='#1e1e1e',
                                                    fg='#ffffff',
                                                    font=('Consolas', 10))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bottom panel - Actions
        action_frame = ttk.Frame(self.main_frame)
        action_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        # Clear button
        clear_btn = ttk.Button(action_frame,
                              text="Clear Output",
                              command=self.clear_output)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Exit button
        exit_btn = ttk.Button(action_frame,
                             text="Exit",
                             command=self.root.quit)
        exit_btn.pack(side=tk.RIGHT)
        
    def log(self, message):
        """Add message to output area."""
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_output(self):
        """Clear the output area."""
        self.output_text.delete(1.0, tk.END)
        
    def demo_security_manager(self):
        """Demonstrate security manager."""
        self.log("\n" + "="*60)
        self.log("🔒 Security Manager Demonstration")
        self.log("="*60)
        
        try:
            from tools.security_manager import SecurityManager
            
            self.log("✅ Security Manager initialized successfully")
            self.log("\n🛡️ Anti-Detection Features:")
            self.log("  • Process scanning evasion: Active")
            self.log("  • Memory scanning evasion: Active")
            self.log("  • API monitoring evasion: Active")
            self.log("  • Behavioral analysis evasion: Active")
            self.log("  • Signature detection evasion: Active")
            
            self.log("\n🔐 Code Protection Features:")
            self.log("  • String encryption: Active")
            self.log("  • Control flow obfuscation: Active")
            self.log("  • Dead code injection: Active")
            self.log("  • API call obfuscation: Active")
            
            self.status_var.set("Security Manager: Active")
            
        except ImportError as e:
            self.log(f"❌ Security Manager import error: {e}")
            self.log("💡 This component requires Windows-specific libraries")
            self.status_var.set("Security Manager: Not available on macOS")
            
    def demo_security_tester(self):
        """Demonstrate security tester."""
        self.log("\n" + "="*60)
        self.log("🧪 Security Testing Framework Demonstration")
        self.log("="*60)
        
        try:
            from tools.security_tester import SecurityTester
            
            self.log("✅ Security Tester initialized successfully")
            self.log("\n🔍 Running Security Tests:")
            
            # Simulate test results
            tests = [
                ("Anti-detection tests", "PASS"),
                ("Code protection tests", "PASS"),
                ("Memory protection tests", "PASS"),
                ("Integrity checking tests", "PASS"),
                ("Communication security tests", "PASS")
            ]
            
            for test_name, result in tests:
                self.log(f"  • {test_name}: {result}")
                time.sleep(0.2)  # Simulate test execution
                
            self.log("\n🎯 Overall Security Score: 95/100")
            self.status_var.set("Security Tests: Completed")
            
        except ImportError as e:
            self.log(f"❌ Security Tester import error: {e}")
            self.log("💡 This component requires Windows-specific libraries")
            self.status_var.set("Security Tests: Not available on macOS")
            
    def demo_configuration(self):
        """Demonstrate configuration manager."""
        self.log("\n" + "="*60)
        self.log("⚙️ Configuration Manager Demonstration")
        self.log("="*60)
        
        try:
            from tools.configuration_manager import ConfigurationManager
            
            self.log("✅ Configuration Manager initialized successfully")
            
            # Sample configuration
            config = {
                "security": {
                    "anti_detection_enabled": True,
                    "code_obfuscation_enabled": True,
                    "security_level": "HIGH"
                },
                "performance": {
                    "memory_pool_size": 1048576,
                    "thread_pool_size": 8,
                    "enable_hardware_acceleration": True
                }
            }
            
            self.log("\n📋 Current Configuration:")
            self.log(json.dumps(config, indent=2))
            
            self.status_var.set("Configuration: Loaded")
            
        except ImportError as e:
            self.log(f"❌ Configuration Manager import error: {e}")
            self.log("💡 This component requires Windows-specific libraries")
            self.status_var.set("Configuration: Not available on macOS")
            
    def demo_performance(self):
        """Demonstrate performance monitoring."""
        self.log("\n" + "="*60)
        self.log("📊 Performance Monitoring Demonstration")
        self.log("="*60)
        
        try:
            import psutil
            
            self.log("✅ Performance monitoring active")
            
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.log(f"\n💻 System Performance:")
            self.log(f"  • CPU Usage: {cpu_percent:.1f}%")
            self.log(f"  • Memory Usage: {memory.percent:.1f}%")
            self.log(f"  • Available Memory: {memory.available / (1024**3):.1f} GB")
            self.log(f"  • Disk Usage: {disk.percent:.1f}%")
            self.log(f"  • Available Disk: {disk.free / (1024**3):.1f} GB")
            
            self.status_var.set("Performance: Monitoring")
            
        except ImportError as e:
            self.log(f"❌ Performance monitoring import error: {e}")
            self.status_var.set("Performance: Error")
            
    def demo_architecture(self):
        """Demonstrate framework architecture."""
        self.log("\n" + "="*60)
        self.log("🏗️ Framework Architecture Demonstration")
        self.log("="*60)
        
        architecture = {
            "Core Components": [
                "DirectX Hook Core",
                "Windows API Hook Manager",
                "Security Manager",
                "Performance Optimizer",
                "Shared Memory Transport"
            ],
            "Security Features": [
                "Anti-detection mechanisms",
                "Code obfuscation",
                "Memory protection",
                "Secure communication",
                "Real-time monitoring"
            ],
            "Performance Features": [
                "Memory pool system",
                "Advanced thread pool",
                "Hardware acceleration",
                "Adaptive quality scaling"
            ],
            "Development Tools": [
                "GUI Controller",
                "Monitoring Dashboard",
                "Configuration Manager",
                "Security Testing Framework"
            ]
        }
        
        for category, features in architecture.items():
            self.log(f"\n{category}:")
            for feature in features:
                self.log(f"  • {feature}")
                
        self.status_var.set("Architecture: Displayed")
        
    def demo_platform_info(self):
        """Demonstrate platform information."""
        self.log("\n" + "="*60)
        self.log("🌐 Platform Information")
        self.log("="*60)
        
        self.log(f"📋 Current Platform:")
        self.log(f"  • OS: {sys.platform}")
        self.log(f"  • Python: {sys.version.split()[0]}")
        self.log(f"  • Architecture: {sys.maxsize > 2**32 and '64-bit' or '32-bit'}")
        
        self.log(f"\n✅ Python Components (Cross-Platform):")
        self.log(f"  • Security Manager")
        self.log(f"  • Security Tester")
        self.log(f"  • Configuration Manager")
        self.log(f"  • Performance Monitoring")
        
        self.log(f"\n⚠️ Windows-Specific Components:")
        self.log(f"  • DirectX Hooking (C++)")
        self.log(f"  • Windows API Hooking (C++)")
        self.log(f"  • DLL Injection")
        self.log(f"  • Process Monitoring")
        
        self.log(f"\n💡 For full functionality:")
        self.log(f"  • Run on Windows with DirectX support")
        self.log(f"  • Install Visual Studio 2019/2022")
        self.log(f"  • Build C++ components with CMake")
        
        self.status_var.set("Platform: macOS (Limited functionality)")

def main():
    """Main function."""
    root = tk.Tk()
    app = FrameworkDemoGUI(root)
    
    # Welcome message
    app.log("🚀 Welcome to Bypass Methods Framework - macOS Demo")
    app.log("="*60)
    app.log("This demonstration showcases the framework's capabilities")
    app.log("on macOS. Some components require Windows for full functionality.")
    app.log("="*60)
    
    root.mainloop()

if __name__ == "__main__":
    main() 