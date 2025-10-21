# UndownUnlock Troubleshooting Guide

This guide provides solutions for common issues encountered when using the UndownUnlock system. If you don't find your issue here, please check the [GitHub Issues](https://github.com/your-repo/bypass-methods/issues) or create a new one.

## Table of Contents
1. [Common Issues](#common-issues)
2. [Build and Installation Problems](#build-and-installation-problems)
3. [Runtime Errors](#runtime-errors)
4. [Performance Issues](#performance-issues)
5. [Hook Detection Problems](#hook-detection-problems)
6. [Capture Issues](#capture-issues)
7. [Memory and Resource Problems](#memory-and-resource-problems)
8. [Python Integration Issues](#python-integration-issues)
9. [Diagnostic Tools](#diagnostic-tools)
10. [Getting Help](#getting-help)

## Common Issues

### Issue: "Failed to initialize DirectX hook core"

**Symptoms:**
- Error message: "Failed to initialize DirectX hook core"
- Application crashes on startup
- Hooks not working

**Possible Causes:**
1. Missing DirectX runtime
2. Insufficient permissions
3. Antivirus blocking the application
4. Corrupted installation

**Solutions:**

#### 1. Check DirectX Installation
```bash
# Run DirectX Diagnostic Tool
dxdiag

# Check DirectX version in the System tab
# Ensure DirectX 11 or higher is installed
```

#### 2. Run as Administrator
```bash
# Right-click on the application and select "Run as administrator"
# Or run from command line with elevated privileges
```

#### 3. Disable Antivirus Temporarily
- Temporarily disable antivirus software
- Add the application to antivirus exclusions
- Test if the issue persists

#### 4. Reinstall DirectX Runtime
```bash
# Download and install latest DirectX runtime from Microsoft
# https://www.microsoft.com/en-us/download/details.aspx?id=35
```

### Issue: "DLL injection failed"

**Symptoms:**
- Error message: "DLL injection failed"
- Target process not found
- Permission denied errors

**Solutions:**

#### 1. Check Process Name
```python
# Verify the target process name is correct
import psutil

for proc in psutil.process_iter(['pid', 'name']):
    print(f"{proc.info['pid']}: {proc.info['name']}")
```

#### 2. Run as Administrator
```bash
# DLL injection requires administrator privileges
# Run the injector as administrator
```

#### 3. Check Target Process Architecture
```python
# Ensure target process architecture matches DLL architecture
import psutil

process = psutil.Process(pid)
print(f"Process architecture: {process.arch()}")
```

#### 4. Disable DEP (Data Execution Prevention)
```bash
# For 32-bit applications on 64-bit systems
bcdedit /set nx AlwaysOff
# Restart required
```

### Issue: "Frame capture not working"

**Symptoms:**
- No frames being captured
- Black or corrupted frames
- High CPU usage during capture

**Solutions:**

#### 1. Check Capture Method
```python
from capture.enhanced_capture import EnhancedCapture

capture = EnhancedCapture()
info = capture.get_capture_info()
print(f"Current method: {info['method_name']}")
print(f"Frame rate: {info['frame_rate']}")
```

#### 2. Verify Target Application
```python
# Ensure target application is using DirectX
# Check if application is in fullscreen mode
# Try windowed mode if fullscreen doesn't work
```

#### 3. Check Graphics Drivers
```bash
# Update graphics drivers to latest version
# Ensure DirectX support is enabled
```

#### 4. Monitor Performance
```python
from utils.performance_monitor import PerformanceMonitor

perf_monitor = PerformanceMonitor.GetInstance()
stats = perf_monitor.GetStats()
print(f"CPU usage: {stats.cpuUsage}%")
print(f"Memory usage: {stats.memoryUsage}MB")
```

## Build and Installation Problems

### Issue: CMake Configuration Fails

**Symptoms:**
- CMake configuration errors
- Missing dependencies
- Build system not found

**Solutions:**

#### 1. Check Prerequisites
```bash
# Verify all required tools are installed
cmake --version
git --version
python --version

# Check Visual Studio installation
# Ensure C++ development tools are installed
```

#### 2. Install Missing Dependencies
```bash
# Install vcpkg for package management
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
./bootstrap-vcpkg.bat
./vcpkg integrate install

# Install required packages
./vcpkg install gtest
./vcpkg install directx-headers
```

#### 3. Fix CMake Configuration
```bash
# Clean build directory
rm -rf build
mkdir build
cd build

# Configure with specific generator
cmake .. -G "Visual Studio 16 2019" -A x64
```

#### 4. Check Environment Variables
```bash
# Ensure PATH includes required tools
echo $PATH

# Set required environment variables
set CMAKE_PREFIX_PATH=C:\vcpkg\installed\x64-windows
```

### Issue: Python Dependencies Installation Fails

**Symptoms:**
- pip install errors
- Missing Python packages
- Version conflicts

**Solutions:**

#### 1. Create Virtual Environment
```bash
# Create isolated Python environment
python -m venv venv
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### 2. Install Dependencies
```bash
# Install base requirements
pip install -r python/requirements/requirements.txt

# Install accessibility requirements
pip install -r python/requirements/requirements_accessibility.txt

# Install development requirements
pip install -r python/requirements/requirements32.txt
```

#### 3. Fix Version Conflicts
```bash
# Check installed packages
pip list

# Uninstall conflicting packages
pip uninstall conflicting-package

# Install specific versions
pip install package==version
```

#### 4. Use Alternative Package Manager
```bash
# Try conda if pip fails
conda create -n undownunlock python=3.8
conda activate undownunlock
conda install package-name
```

## Runtime Errors

### Issue: "Access violation" or "Segmentation fault"

**Symptoms:**
- Application crashes with access violation
- Segmentation fault errors
- Memory corruption

**Solutions:**

#### 1. Enable Debug Build
```bash
# Build in debug mode
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build . --config Debug
```

#### 2. Use Memory Tracking
```cpp
#include "utils/memory_tracker.h"

auto& memoryTracker = MemoryTracker::GetInstance();
memoryTracker.EnableTracking(true);
memoryTracker.SetLeakThreshold(1024 * 1024);

// Check for memory leaks
auto leaks = memoryTracker.GetLeaks();
if (!leaks.empty()) {
    for (const auto& leak : leaks) {
        std::cout << "Memory leak: " << leak.context 
                  << " (" << leak.size << " bytes)" << std::endl;
    }
}
```

#### 3. Enable Error Logging
```cpp
#include "utils/error_handler.h"

auto& errorHandler = ErrorHandler::GetInstance();
errorHandler.SetLogLevel(ErrorSeverity::LOW);
errorHandler.SetLogFile("debug.log");
errorHandler.EnableConsoleOutput(true);
```

#### 4. Use Debugger
```bash
# Attach debugger to running process
# Set breakpoints at crash location
# Examine call stack and memory state
```

### Issue: "COM interface error" or "DirectX error"

**Symptoms:**
- COM interface creation fails
- DirectX device creation errors
- Interface query failures

**Solutions:**

#### 1. Check COM Initialization
```cpp
// Ensure COM is initialized
HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
if (FAILED(hr)) {
    // Handle COM initialization failure
}
```

#### 2. Use RAII Wrappers
```cpp
#include "hooks/com_interface_wrapper.h"

// Use RAII wrappers for COM interfaces
ComPtr<ID3D11Device> device;
ComPtr<ID3D11DeviceContext> context;

// Automatic cleanup when scope ends
```

#### 3. Check DirectX Device Creation
```cpp
// Verify DirectX device creation
D3D_FEATURE_LEVEL featureLevel;
HRESULT hr = D3D11CreateDevice(
    nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0,
    nullptr, 0, D3D11_SDK_VERSION,
    &device, &featureLevel, &context
);

if (FAILED(hr)) {
    // Handle device creation failure
}
```

#### 4. Enable DirectX Debug Layer
```cpp
// Enable DirectX debug layer for detailed error information
UINT flags = D3D11_CREATE_DEVICE_DEBUG;
```

## Performance Issues

### Issue: High CPU Usage

**Symptoms:**
- Excessive CPU usage during capture
- System becomes unresponsive
- Frame rate drops

**Solutions:**

#### 1. Optimize Capture Settings
```python
# Reduce capture quality
config = {
    'capture_method': 'windows_graphics_capture',
    'frame_rate': 30,  # Reduce from 60
    'compression': True,
    'quality': 'medium'  # Reduce from high
}
```

#### 2. Monitor Performance
```cpp
#include "utils/performance_monitor.h"

auto& perfMonitor = PerformanceMonitor::GetInstance();
perfMonitor.EnableMonitoring(true);

// Check performance metrics
auto stats = perfMonitor.GetStats();
if (stats.cpuUsage > 80.0) {
    // Reduce capture frequency or quality
}
```

#### 3. Use Hardware Acceleration
```cpp
// Enable hardware acceleration for frame processing
extractor.SetHardwareAcceleration(true);
extractor.SetQualityLevel(QualityLevel::MEDIUM);
```

#### 4. Optimize Memory Usage
```cpp
// Use memory pools for frequent allocations
#include "optimization/memory_pool.h"

MemoryPool pool;
pool.Initialize(1024 * 1024);  // 1MB pool
```

### Issue: Memory Leaks

**Symptoms:**
- Memory usage continuously increases
- Application becomes slower over time
- Out of memory errors

**Solutions:**

#### 1. Enable Memory Tracking
```cpp
#include "utils/memory_tracker.h"

auto& memoryTracker = MemoryTracker::GetInstance();
memoryTracker.EnableTracking(true);

// Generate memory report
memoryTracker.GenerateReport("memory_report.txt");
```

#### 2. Use Smart Pointers
```cpp
// Replace raw pointers with smart pointers
std::unique_ptr<FrameExtractor> extractor;
std::shared_ptr<FrameData> frameData;

// Use RAII wrappers
ScopedHandle handle(CreateFile(...));
```

#### 3. Check Resource Cleanup
```cpp
// Ensure all resources are properly cleaned up
class ResourceManager {
public:
    ~ResourceManager() {
        // Clean up all resources
        for (auto& resource : resources_) {
            resource->Release();
        }
    }
private:
    std::vector<IUnknown*> resources_;
};
```

#### 4. Monitor Memory Usage
```cpp
// Track memory usage over time
auto stats = memoryTracker.GetStats();
if (stats.currentUsage > threshold) {
    // Investigate memory usage
    auto leaks = memoryTracker.GetLeaks();
    // Handle memory leaks
}
```

## Hook Detection Problems

### Issue: Hooks Being Detected

**Symptoms:**
- Target application detects hooks
- Anti-cheat systems flag the application
- Application refuses to run

**Solutions:**

#### 1. Use Anti-Detection Features
```cpp
#include "security/anti_detection.h"

// Enable anti-detection mechanisms
AntiDetection antiDetection;
antiDetection.EnableHookConcealment(true);
antiDetection.EnableTimingNormalization(true);
antiDetection.EnableCallStackSpoofing(true);
```

#### 2. Implement Code Obfuscation
```cpp
#include "security/obfuscation.h"

// Obfuscate critical functions
Obfuscation obfuscation;
obfuscation.ObfuscateFunction("HookFunction");
obfuscation.EncryptStrings();
obfuscation.ObfuscateImports();
```

#### 3. Use Integrity Checking
```cpp
#include "security/integrity_checker.h"

// Verify code integrity
IntegrityChecker checker;
if (!checker.VerifyCodeIntegrity()) {
    // Handle integrity violation
    checker.RestoreCodeIntegrity();
}
```

#### 4. Implement Timing Normalization
```cpp
// Normalize timing to prevent detection
LARGE_INTEGER frequency, start, end;
QueryPerformanceFrequency(&frequency);
QueryPerformanceCounter(&start);

// Perform operation
PerformOperation();

QueryPerformanceCounter(&end);
double elapsed = (end.QuadPart - start.QuadPart) * 1000.0 / frequency.QuadPart;

// Normalize timing
NormalizeTiming(elapsed);
```

## Capture Issues

### Issue: Black or Corrupted Frames

**Symptoms:**
- Captured frames are black
- Frame data is corrupted
- Wrong frame format

**Solutions:**

#### 1. Check Frame Format
```cpp
// Verify frame format compatibility
DXGI_FORMAT format = texture->GetDesc().Format;
if (format != DXGI_FORMAT_R8G8B8A8_UNORM) {
    // Convert format
    ConvertTextureFormat(texture, DXGI_FORMAT_R8G8B8A8_UNORM);
}
```

#### 2. Verify Staging Texture
```cpp
// Ensure staging texture is properly created
D3D11_TEXTURE2D_DESC desc = {};
desc.Width = width;
desc.Height = height;
desc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
desc.Usage = D3D11_USAGE_STAGING;
desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;

ComPtr<ID3D11Texture2D> stagingTexture;
HRESULT hr = device->CreateTexture2D(&desc, nullptr, &stagingTexture);
```

#### 3. Check Frame Extraction
```cpp
// Verify frame extraction process
FrameExtractor extractor;
if (!extractor.Initialize(device)) {
    // Handle initialization failure
}

FrameData frameData;
if (!extractor.ExtractFrame(sourceTexture, frameData)) {
    // Handle extraction failure
}

// Verify frame data
if (frameData.data == nullptr || frameData.size == 0) {
    // Handle invalid frame data
}
```

#### 4. Use Alternative Capture Method
```python
# Try different capture methods
from capture.enhanced_capture import EnhancedCapture

capture = EnhancedCapture()
capture.add_capture_method(WindowsGraphicsCapture())
capture.add_capture_method(DXGIDesktopDuplication())

# Let the system choose the best method
capture.start_capture()
```

### Issue: Frame Rate Issues

**Symptoms:**
- Low frame rate
- Frame drops
- Inconsistent timing

**Solutions:**

#### 1. Optimize Frame Processing
```cpp
// Use efficient frame processing
extractor.SetCompressionEnabled(true);
extractor.SetCompressionLevel(6);  // Balance quality and performance
extractor.SetQualityLevel(QualityLevel::MEDIUM);
```

#### 2. Monitor Frame Rate
```cpp
// Track frame rate performance
auto& perfMonitor = PerformanceMonitor::GetInstance();
perfMonitor.RecordMetric("FrameRate", currentFrameRate);

auto stats = perfMonitor.GetStats();
if (stats.averageFrameRate < targetFrameRate) {
    // Optimize capture settings
    ReduceCaptureQuality();
}
```

#### 3. Use Frame Buffering
```cpp
// Implement frame buffering to smooth frame delivery
class FrameBuffer {
public:
    void AddFrame(const FrameData& frame) {
        std::lock_guard<std::mutex> lock(mutex_);
        frames_.push_back(frame);
        if (frames_.size() > maxFrames_) {
            frames_.pop_front();
        }
    }
    
    FrameData GetFrame() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!frames_.empty()) {
            FrameData frame = frames_.front();
            frames_.pop_front();
            return frame;
        }
        return FrameData{};
    }
private:
    std::deque<FrameData> frames_;
    std::mutex mutex_;
    size_t maxFrames_ = 3;
};
```

## Memory and Resource Problems

### Issue: Out of Memory Errors

**Symptoms:**
- "Out of memory" errors
- Application crashes
- System becomes unresponsive

**Solutions:**

#### 1. Monitor Memory Usage
```cpp
#include "utils/memory_tracker.h"

auto& memoryTracker = MemoryTracker::GetInstance();
auto stats = memoryTracker.GetStats();

if (stats.currentUsage > memoryLimit) {
    // Free unused resources
    FreeUnusedResources();
    
    // Reduce capture quality
    ReduceCaptureQuality();
}
```

#### 2. Implement Memory Pools
```cpp
#include "optimization/memory_pool.h"

// Use memory pools for frequent allocations
MemoryPool pool;
pool.Initialize(1024 * 1024 * 10);  // 10MB pool

void* buffer = pool.Allocate(1024);
// Use buffer
pool.Free(buffer);
```

#### 3. Optimize Resource Usage
```cpp
// Reuse resources instead of creating new ones
class ResourceCache {
public:
    ID3D11Texture2D* GetStagingTexture(int width, int height) {
        auto key = std::make_pair(width, height);
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            return it->second;
        }
        
        // Create new texture
        auto texture = CreateStagingTexture(width, height);
        cache_[key] = texture;
        return texture;
    }
private:
    std::map<std::pair<int, int>, ID3D11Texture2D*> cache_;
};
```

#### 4. Implement Garbage Collection
```cpp
// Periodically clean up unused resources
class ResourceManager {
public:
    void CleanupUnusedResources() {
        auto now = std::chrono::steady_clock::now();
        
        for (auto it = resources_.begin(); it != resources_.end();) {
            if (now - it->second.lastUsed > cleanupThreshold) {
                it->second.resource->Release();
                it = resources_.erase(it);
            } else {
                ++it;
            }
        }
    }
private:
    struct ResourceEntry {
        IUnknown* resource;
        std::chrono::steady_clock::time_point lastUsed;
    };
    std::map<void*, ResourceEntry> resources_;
};
```

## Python Integration Issues

### Issue: Python Module Import Errors

**Symptoms:**
- Module not found errors
- Import failures
- Missing dependencies

**Solutions:**

#### 1. Check Python Path
```python
import sys
print(sys.path)

# Add project path to Python path
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))
```

#### 2. Verify Virtual Environment
```bash
# Activate virtual environment
venv\Scripts\activate

# Check installed packages
pip list

# Install missing packages
pip install missing-package
```

#### 3. Check Python Version Compatibility
```python
import sys
print(f"Python version: {sys.version}")

# Ensure Python 3.8+ is used
if sys.version_info < (3, 8):
    print("Python 3.8+ required")
    sys.exit(1)
```

#### 4. Fix Import Issues
```python
# Use relative imports
from .capture import WindowsGraphicsCapture
from .tools import Controller

# Or use absolute imports
from undownunlock.capture import WindowsGraphicsCapture
from undownunlock.tools import Controller
```

### Issue: Shared Memory Communication Fails

**Symptoms:**
- Python can't connect to C++ process
- Frame data not received
- Communication timeouts

**Solutions:**

#### 1. Check Shared Memory Name
```python
# Ensure shared memory names match
SHARED_MEMORY_NAME = "UndownUnlock_FrameBuffer"

# Connect to shared memory
transport = SharedMemoryTransport()
if not transport.Connect(SHARED_MEMORY_NAME):
    print("Failed to connect to shared memory")
```

#### 2. Verify Process Permissions
```python
# Ensure both processes have same permissions
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("Administrator privileges required")
```

#### 3. Check Memory Buffer Size
```python
# Ensure buffer size is sufficient
BUFFER_SIZE = 1024 * 1024 * 10  # 10MB

transport = SharedMemoryTransport()
if not transport.Initialize(SHARED_MEMORY_NAME, BUFFER_SIZE):
    print("Failed to initialize shared memory")
```

#### 4. Implement Error Handling
```python
import time

def receive_frames_with_retry():
    transport = SharedMemoryTransport()
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            if transport.Connect(SHARED_MEMORY_NAME):
                while transport.IsConnected():
                    frame_data = transport.ReceiveFrame()
                    if frame_data:
                        process_frame(frame_data)
                    time.sleep(0.001)  # Small delay
                break
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            time.sleep(1)  # Wait before retry
```

## Diagnostic Tools

### Built-in Diagnostic Tools

#### 1. Error Handler
```cpp
#include "utils/error_handler.h"

// Enable comprehensive error logging
auto& errorHandler = ErrorHandler::GetInstance();
errorHandler.SetLogLevel(ErrorSeverity::LOW);
errorHandler.SetLogFile("diagnostic.log");
errorHandler.EnableConsoleOutput(true);

// Log specific errors
errorHandler.LogError(ErrorCategory::DIRECTX, ErrorSeverity::HIGH,
                     "Specific error message", "Context information");
```

#### 2. Performance Monitor
```cpp
#include "utils/performance_monitor.h"

// Monitor system performance
auto& perfMonitor = PerformanceMonitor::GetInstance();
perfMonitor.EnableMonitoring(true);
perfMonitor.SetSamplingInterval(1000);  // 1 second

// Get performance statistics
auto stats = perfMonitor.GetStats();
std::cout << "CPU Usage: " << stats.cpuUsage << "%" << std::endl;
std::cout << "Memory Usage: " << stats.memoryUsage << "MB" << std::endl;
std::cout << "Frame Rate: " << stats.averageFrameRate << " FPS" << std::endl;
```

#### 3. Memory Tracker
```cpp
#include "utils/memory_tracker.h"

// Track memory usage and leaks
auto& memoryTracker = MemoryTracker::GetInstance();
memoryTracker.EnableTracking(true);

// Generate memory report
memoryTracker.GenerateReport("memory_report.txt");

// Check for leaks
auto leaks = memoryTracker.GetLeaks();
if (!leaks.empty()) {
    std::cout << "Memory leaks detected:" << std::endl;
    for (const auto& leak : leaks) {
        std::cout << "  " << leak.context << ": " << leak.size << " bytes" << std::endl;
    }
}
```

### External Diagnostic Tools

#### 1. Process Monitor
```bash
# Use Process Monitor to track file and registry access
procmon.exe

# Filter for your application
# Look for access denied errors
# Check for missing files or registry keys
```

#### 2. Performance Monitor
```bash
# Use Windows Performance Monitor
perfmon.exe

# Monitor CPU, memory, and disk usage
# Create custom data collector sets
# Analyze performance bottlenecks
```

#### 3. DebugView
```bash
# Use DebugView to capture debug output
debugview.exe

# Capture debug messages from your application
# Filter for specific messages
# Save debug output to file
```

## Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide** for your specific issue
2. **Search existing issues** on GitHub
3. **Check the documentation** for usage examples
4. **Run diagnostic tools** to gather information
5. **Try the solutions** provided in this guide

### When Creating an Issue

Include the following information:

#### System Information
- Operating system version
- UndownUnlock version
- Python version
- Visual Studio version
- Graphics driver version

#### Error Details
- Complete error message
- Steps to reproduce
- Expected vs actual behavior
- Log files and diagnostic output

#### Environment
- Build configuration (Debug/Release)
- Target application details
- Capture method being used
- Any custom configuration

### Example Issue Report

```markdown
## Issue Description
Frame capture is not working - getting black frames

## System Information
- OS: Windows 11 22H2
- UndownUnlock: v1.2.0
- Python: 3.9.7
- Visual Studio: 2022 17.5
- Graphics: NVIDIA RTX 3080, Driver 531.41

## Steps to Reproduce
1. Build project in Debug mode
2. Run injector as administrator
3. Inject into target application
4. Start frame capture
5. Observe black frames

## Expected Behavior
Should capture actual frame content from target application

## Actual Behavior
Receiving black frames with correct dimensions

## Log Files
[Attach diagnostic.log, memory_report.txt, and any other relevant logs]

## Additional Information
- Target application: DirectX 11 game
- Capture method: Windows Graphics Capture
- No antivirus interference detected
```

### Support Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and help
- **Documentation**: For usage guides and API reference
- **Code Examples**: For implementation examples

### Contributing to Troubleshooting

If you find a solution not covered in this guide:

1. **Document your solution** with clear steps
2. **Test the solution** on different systems
3. **Submit a pull request** to update this guide
4. **Include code examples** where appropriate
5. **Add to the appropriate section** of this guide

## Conclusion

This troubleshooting guide covers the most common issues encountered with the UndownUnlock system. The solutions provided should resolve most problems you may encounter.

Remember to:
- Always run as administrator when required
- Check system requirements and dependencies
- Use diagnostic tools to gather information
- Test solutions in a controlled environment
- Document any new issues and solutions

If you continue to experience problems, please create a detailed issue report with all the information requested above. This will help the development team provide more targeted assistance. 