import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80 + "\n")

def check_python_version():
    """Check if Python version is 3.6 or higher."""
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
        print("Error: Python 3.6 or higher is required.")
        return False
    return True

def install_requirements():
    """Install required packages."""
    print("Installing required packages...")
    
    # Create requirements file
    with open("requirements_accessibility.txt", "w") as f:
        f.write("keyboard==0.13.5\n")
        f.write("Pillow==9.5.0\n")
        f.write("psutil==5.9.5\n")
        f.write("comtypes==1.2.0\n")
        f.write("pywin32==306\n")
        f.write("cryptography==41.0.3\n")  # Added for Named Pipes security
        f.write("matplotlib==3.5.3\n")      # Added for dashboard visualization
        f.write("numpy==1.22.4\n")          # Added for screen capture processing
        f.write("pythoncom\n")              # Added for COM/DCOM interfaces
        f.write("pythonnet==3.0.1\n")       # Added for .NET/WinRT interop
    
    # Install packages
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_accessibility.txt"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to install required packages.")
        return False

def setup_virtual_environment():
    """Set up a virtual environment."""
    venv_dir = "venv"
    
    # Check if virtual environment already exists
    if os.path.exists(venv_dir):
        print(f"Virtual environment '{venv_dir}' already exists.")
        activate_script = os.path.join(venv_dir, "Scripts", "activate")
        if os.path.exists(activate_script):
            print(f"You can activate it with: {activate_script}")
            return True
        else:
            print(f"Warning: Virtual environment seems corrupted.")
    
    print(f"Creating virtual environment '{venv_dir}'...")
    
    try:
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        
        # Get path to pip in the virtual environment
        if os.name == 'nt':  # Windows
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:  # Unix/Linux
            pip_path = os.path.join(venv_dir, "bin", "pip")
        
        # Install requirements in the virtual environment
        print("Installing requirements in the virtual environment...")
        with open("requirements_accessibility.txt", "w") as f:
            f.write("keyboard==0.13.5\n")
            f.write("Pillow==9.5.0\n")
            f.write("psutil==5.9.5\n")
            f.write("comtypes==1.2.0\n")
            f.write("pywin32==306\n")
            f.write("cryptography==41.0.3\n")  # Added for Named Pipes security
            f.write("matplotlib==3.5.3\n")      # Added for dashboard visualization
            f.write("numpy==1.22.4\n")          # Added for screen capture processing
        
        subprocess.run([pip_path, "install", "-r", "requirements_accessibility.txt"], check=True)
        return True
    
    except subprocess.CalledProcessError:
        print("Error: Failed to set up virtual environment.")
        return False

def create_launchers():
    """Create batch files to start the application and the remote client."""
    print("Creating launcher scripts...")
    
    # Create main controller launcher
    with open("launch_controller.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting UndownUnlock Accessibility Controller...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python accessibility_controller.py\n")
        f.write("pause\n")
    
    # Create remote client launcher
    with open("launch_client.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting UndownUnlock Remote Client...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python remote_client.py --interactive\n")
        f.write("pause\n")
    
    # Create a command-line shortcut for the remote client
    with open("client.bat", "w") as f:
        f.write("@echo off\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python remote_client.py %*\n")
    
    # Create integration example launcher
    with open("launch_integration.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting UndownUnlock Integration Example...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python integration_example.py %*\n")
        f.write("pause\n")
    
    # Create automated test launcher
    with open("run_tests.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Running UndownUnlock Automated Tests...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python automated_test.py --start-controller --stop-controller %*\n")
        f.write("pause\n")
    
    # Create dashboard launcher
    with open("launch_dashboard.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting UndownUnlock Dashboard...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python dashboard_example.py\n")
        f.write("pause\n")
    
    # Create launcher for enhanced capture demo
    with open("launch_capture_demo.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting Enhanced Screen Capture Demo...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python enhanced_capture.py\n")
        f.write("pause\n")
    
    # Create launcher for enhanced capture test
    with open("test_capture.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting Enhanced Screen Capture Test...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python test_enhanced_capture.py %*\n")
        f.write("pause\n")
    
    # Create launcher for advanced capture demo
    with open("launch_advanced_capture.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting Advanced Screen Capture Demo...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python advanced_capture.py --window \"LockDown Browser\"\n")
        f.write("pause\n")
    
    # Create launcher for Windows Graphics Capture demo
    with open("launch_wgc_capture.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting Windows Graphics Capture Test...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python windows_graphics_capture.py\n")
        f.write("pause\n")
    
    # Create launcher for DXGI Desktop Duplication test
    with open("launch_dxgi_capture.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting DXGI Desktop Duplication Test...\n")
        f.write("call venv\\Scripts\\activate.bat\n")
        f.write("python dxgi_desktop_duplication.py\n")
        f.write("pause\n")
    
    print("Created launcher scripts:")
    print("  - launch_controller.bat - Starts the accessibility controller")
    print("  - launch_client.bat - Starts the remote client in interactive mode")
    print("  - client.bat - Command-line client for scripting (use with --help for options)")
    print("  - launch_integration.bat - Runs the integration example")
    print("  - run_tests.bat - Runs the automated tests")
    print("  - launch_dashboard.bat - Runs the monitoring dashboard")
    print("  - launch_capture_demo.bat - Runs the screen capture demo")
    print("  - test_capture.bat - Runs the enhanced screen capture test")
    print("  - launch_advanced_capture.bat - Runs the advanced screen capture demo")
    print("  - launch_wgc_capture.bat - Runs the Windows Graphics Capture test")
    print("  - launch_dxgi_capture.bat - Runs the DXGI Desktop Duplication test")
    
    print("Created launch_wgc_capture.bat for testing Windows Graphics Capture API")
    print("Created launch_dxgi_capture.bat for testing DXGI Desktop Duplication")
    
    return True

def create_screenshot_directory():
    """Create directories for screenshots."""
    print("Creating screenshot directories...")
    
    dirs = ["screenshots", "auto_screenshots"]
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"  - Created directory: {dir_name}")
    
    return True

def main():
    """Main setup function."""
    print_header("UndownUnlock Accessibility Framework Setup")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        (install_requirements, "Installing requirements"),
        (setup_virtual_environment, "Setting up virtual environment"),
        (create_launchers, "Creating launcher scripts"),
        (create_screenshot_directory, "Creating screenshot directories")
    ]
    
    # Run setup steps
    for step_func, step_name in steps:
        print(f"\n>> {step_name}...")
        if not step_func():
            print(f"Error in step: {step_name}")
            sys.exit(1)
    
    print_header("Setup Complete")
    print("The UndownUnlock Accessibility Framework has been successfully set up!")
    
    print("\nTo start the application, you can:")
    print("  1. Run the main controller: launch_controller.bat")
    print("  2. Run the remote client: launch_client.bat")
    
    print("\nAvailable keyboard shortcuts when the controller is running:")
    print("  - Alt+Shift+C: Cycle to the next window")
    print("  - Alt+Shift+X: Cycle to the previous window")
    print("  - Alt+Shift+L: Focus the LockDown Browser window")
    print("  - Alt+Shift+S: Take a screenshot")
    print("  - Alt+Shift+M: Minimize all windows except LockDown Browser")
    print("  - Alt+Shift+R: Restore all minimized windows")
    
    print("\nYou can also use the remote client to control the application from another process:")
    print("  - Interactive mode: launch_client.bat")
    print("  - Command-line mode: client.bat --help")
    
    print("\nAdditional tools and examples:")
    print("  - Integration example: launch_integration.bat")
    print("  - Monitoring dashboard: launch_dashboard.bat")
    print("  - Automated tests: run_tests.bat")
    print("  - Screen capture demo: launch_capture_demo.bat")
    print("  - Enhanced screen capture test: test_capture.bat")
    print("  - Advanced screen capture demo: launch_advanced_capture.bat")
    print("  - Windows Graphics Capture test: launch_wgc_capture.bat")
    print("  - DXGI Desktop Duplication test: launch_dxgi_capture.bat")
    
    print("\nDocumentation:")
    print("  - For detailed information, see README_accessibility.md")
    print("  - For a comparison with the DLL approach, see README_modern_approach.md")

if __name__ == "__main__":
    main() 