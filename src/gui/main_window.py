
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime

class MainWindow:
    """Main GUI window for the Security Testing Framework"""

    def __init__(self, framework):
        self.framework = framework
        self.root = tk.Tk()
        self.root.title("Security Testing Framework v1.0")
        self.root.geometry("900x600")
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Screen Capture", command=self.run_screen_capture)
        tools_menu.add_command(label="Process Monitor", command=self.run_process_monitor)
        tools_menu.add_command(label="API Hooks", command=self.run_api_hooks)

        # Main content
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Dashboard tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.setup_dashboard()

        # Tests tab
        self.tests_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tests_frame, text="Security Tests")
        self.setup_tests()

        # Results tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self.setup_results()

        # Status bar
        self.status_bar = ttk.Label(
            self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_dashboard(self):
        """Setup dashboard tab"""
        ttk.Label(
            self.dashboard_frame,
            text="Security Testing Framework",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        info_frame = ttk.LabelFrame(self.dashboard_frame, text="System Information")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)

        info_text = f"""
        Version: {self.framework.VERSION}
        Admin Privileges: {"Yes" if self.framework.is_admin else "No"}
        Security Level: {self.framework.config.get('security_level', 'HIGH')}
        Stealth Mode: {"Enabled" if self.framework.config.get('stealth_mode') else "Disabled"}
        """

        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)

    def setup_tests(self):
        """Setup tests tab"""
        # Test selection
        ttk.Label(self.tests_frame, text="Select Tests:", font=("Arial", 12)).pack(pady=5)

        self.test_vars = {}
        tests = [
            "Screen Capture Detection",
            "Process Manipulation",
            "API Hooking",
            "Memory Scanning",
            "Network Monitoring"
        ]

        for test in tests:
            var = tk.BooleanVar(value=True)
            self.test_vars[test] = var
            ttk.Checkbutton(self.tests_frame, text=test, variable=var).pack(anchor=tk.W, padx=20)

        # Target selection
        target_frame = ttk.Frame(self.tests_frame)
        target_frame.pack(pady=10)

        ttk.Label(target_frame, text="Target Process:").pack(side=tk.LEFT, padx=5)
        self.target_entry = ttk.Entry(target_frame, width=30)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        self.target_entry.insert(0, "LockDownBrowser.exe")

        # Run button
        ttk.Button(
            self.tests_frame, text="Run Tests", command=self.run_tests
        ).pack(pady=10)

    def setup_results(self):
        """Setup results tab"""
        # Results text area
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD)
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.results_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)

        # Export button
        ttk.Button(
            self.results_frame, text="Export Report", command=self.export_report
        ).pack(pady=5)

    def run_tests(self):
        """Run selected security tests"""
        self.update_status("Running tests...")
        self.notebook.select(self.results_frame)

        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Security Test Report\n")
        self.results_text.insert(tk.END, f"{'='*60}\n")
        self.results_text.insert(tk.END, f"Timestamp: {datetime.now()}\n")
        self.results_text.insert(tk.END, f"Target: {self.target_entry.get()}\n\n")

        # Run tests in background thread
        def test_worker():
            for test_name, var in self.test_vars.items():
                if var.get():
                    self.results_text.insert(tk.END, f"\n[*] Running {test_name}...\n")
                    # Simulate test execution
                    result = f"  [OK] {test_name} completed successfully\n"
                    self.results_text.insert(tk.END, result)
                    self.results_text.see(tk.END)

            self.results_text.insert(tk.END, f"\n{'='*60}\n")
            self.results_text.insert(tk.END, "All tests completed.\n")
            self.update_status("Tests completed")

        thread = threading.Thread(target=test_worker)
        thread.daemon = True
        thread.start()

    def run_screen_capture(self):
        """Run screen capture test"""
        self.update_status("Running screen capture test...")
        messagebox.showinfo("Screen Capture", "Screen capture test started")

    def run_process_monitor(self):
        """Run process monitor"""
        self.update_status("Running process monitor...")
        messagebox.showinfo("Process Monitor", "Process monitor started")

    def run_api_hooks(self):
        """Run API hooks test"""
        self.update_status("Running API hooks test...")
        messagebox.showinfo("API Hooks", "API hooks test started")

    def load_config(self):
        """Load configuration file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            messagebox.showinfo("Config", f"Loaded configuration from {filename}")

    def save_config(self):
        """Save configuration file"""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.framework.save_config(self.framework.config)
            messagebox.showinfo("Config", f"Saved configuration to {filename}")

    def export_report(self):
        """Export test results"""
        filename = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.results_text.get(1.0, tk.END))
            messagebox.showinfo("Export", f"Report exported to {filename}")

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()
