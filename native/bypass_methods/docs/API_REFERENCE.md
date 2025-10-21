# UndownUnlock API Reference

## Table of Contents
1. [Core Hooking APIs](#core-hooking-apis)
2. [DirectX Hook APIs](#directx-hook-apis)
3. [Windows API Hook APIs](#windows-api-hook-apis)
4. [Shared Memory Transport APIs](#shared-memory-transport-apis)
5. [Pattern Scanning APIs](#pattern-scanning-apis)
6. [Utility Framework APIs](#utility-framework-apis)
7. [Python Consumer APIs](#python-consumer-apis)
8. [Error Handling APIs](#error-handling-apis)
9. [Performance Monitoring APIs](#performance-monitoring-apis)
10. [Memory Management APIs](#memory-management-apis)

## Core Hooking APIs

### DXHookCore

The main DirectX hook management class that handles initialization, hook installation, and cleanup.

#### Class Definition
```cpp
class DXHookCore {
public:
    static bool Initialize();
    static void Shutdown();
    static DXHookCore& GetInstance();
    bool IsInitialized() const;
    bool InstallHooks();
    bool UninstallHooks();
    void SetFrameCallback(FrameCallback callback);
    void SetErrorCallback(ErrorCallback callback);
};
```

#### Methods

##### `Initialize()`
Initializes the DirectX hook core system.

**Returns**: `bool` - `true` if initialization successful, `false` otherwise

**Example**:
```cpp
#include "hooks/dx_hook_core.h"

if (!DXHookCore::Initialize()) {
    std::cerr << "Failed to initialize DirectX hook core" << std::endl;
    return -1;
}
```

##### `Shutdown()`
Shuts down the DirectX hook core system and cleans up resources.

**Example**:
```cpp
DXHookCore::Shutdown();
```

##### `GetInstance()`
Gets the singleton instance of the DXHookCore.

**Returns**: `DXHookCore&` - Reference to the singleton instance

**Example**:
```cpp
auto& hookCore = DXHookCore::GetInstance();
if (hookCore.IsInitialized()) {
    // Hook core is ready
}
```

##### `InstallHooks()`
Installs DirectX hooks on detected devices and swap chains.

**Returns**: `bool` - `true` if hooks installed successfully, `false` otherwise

**Example**:
```cpp
if (!hookCore.InstallHooks()) {
    std::cerr << "Failed to install DirectX hooks" << std::endl;
    return -1;
}
```

##### `SetFrameCallback()`
Sets a callback function to be called when frames are captured.

**Parameters**:
- `callback` - Function pointer to frame callback

**Example**:
```cpp
void OnFrameCaptured(const FrameData& frame) {
    // Process captured frame
    std::cout << "Frame captured: " << frame.width << "x" << frame.height << std::endl;
}

hookCore.SetFrameCallback(OnFrameCaptured);
```

### WindowsApiHookManager

Manages Windows API hooks for process and window control.

#### Class Definition
```cpp
class WindowsApiHookManager {
public:
    static bool Initialize();
    static void Shutdown();
    static WindowsApiHookManager& GetInstance();
    bool InstallProcessHooks();
    bool InstallWindowHooks();
    bool InstallKeyboardHooks();
    bool UninstallAllHooks();
    void SetProcessCallback(ProcessCallback callback);
    void SetWindowCallback(WindowCallback callback);
    void SetKeyboardCallback(KeyboardCallback callback);
};
```

#### Methods

##### `Initialize()`
Initializes the Windows API hook manager.

**Returns**: `bool` - `true` if initialization successful, `false` otherwise

**Example**:
```cpp
#include "hooks/windows_api_hooks.h"

if (!WindowsApiHookManager::Initialize()) {
    std::cerr << "Failed to initialize Windows API hook manager" << std::endl;
    return -1;
}
```

##### `InstallProcessHooks()`
Installs hooks for process creation and termination APIs.

**Returns**: `bool` - `true` if hooks installed successfully, `false` otherwise

**Example**:
```cpp
auto& hookManager = WindowsApiHookManager::GetInstance();
if (!hookManager.InstallProcessHooks()) {
    std::cerr << "Failed to install process hooks" << std::endl;
    return -1;
}
```

## DirectX Hook APIs

### SwapChainHook

Handles IDXGISwapChain::Present interception and frame extraction.

#### Class Definition
```cpp
class SwapChainHook {
public:
    static bool Install(IDXGISwapChain* swapChain);
    static bool Uninstall();
    static SwapChainHook* GetInstance();
    void SetFrameExtractor(std::unique_ptr<FrameExtractor> extractor);
    void EnableFrameCapture(bool enable);
    bool IsFrameCaptureEnabled() const;
};
```

#### Methods

##### `Install()`
Installs hooks on the specified swap chain.

**Parameters**:
- `swapChain` - Pointer to IDXGISwapChain interface

**Returns**: `bool` - `true` if hook installed successfully, `false` otherwise

**Example**:
```cpp
#include "hooks/swap_chain_hook.h"

IDXGISwapChain* swapChain = /* get swap chain */;
if (!SwapChainHook::Install(swapChain)) {
    std::cerr << "Failed to install swap chain hook" << std::endl;
    return -1;
}
```

### FrameExtractor

Extracts frame data from DirectX resources.

#### Class Definition
```cpp
class FrameExtractor {
public:
    FrameExtractor();
    ~FrameExtractor();
    
    bool Initialize(ID3D11Device* device);
    bool ExtractFrame(ID3D11Texture2D* source, FrameData& frameData);
    void SetTargetFormat(DXGI_FORMAT format);
    void SetCompressionEnabled(bool enabled);
    void SetQualityLevel(QualityLevel level);
};
```

#### Methods

##### `Initialize()`
Initializes the frame extractor with the specified device.

**Parameters**:
- `device` - Pointer to D3D11 device

**Returns**: `bool` - `true` if initialization successful, `false` otherwise

**Example**:
```cpp
#include "frame_extractor.h"

FrameExtractor extractor;
if (!extractor.Initialize(d3d11Device)) {
    std::cerr << "Failed to initialize frame extractor" << std::endl;
    return -1;
}

extractor.SetTargetFormat(DXGI_FORMAT_R8G8B8A8_UNORM);
extractor.SetCompressionEnabled(true);
extractor.SetQualityLevel(QualityLevel::HIGH);
```

##### `ExtractFrame()`
Extracts frame data from the source texture.

**Parameters**:
- `source` - Source texture to extract from
- `frameData` - Output frame data structure

**Returns**: `bool` - `true` if extraction successful, `false` otherwise

**Example**:
```cpp
FrameData frameData;
if (extractor.ExtractFrame(sourceTexture, frameData)) {
    // Process extracted frame data
    std::cout << "Frame extracted: " << frameData.width << "x" << frameData.height << std::endl;
}
```

## Windows API Hook APIs

### KeyboardHook

Handles keyboard input interception and filtering.

#### Class Definition
```cpp
class KeyboardHook {
public:
    static bool Install();
    static bool Uninstall();
    static KeyboardHook* GetInstance();
    
    void SetKeyCallback(KeyCallback callback);
    void AddHotkey(int keyCode, int modifiers, HotkeyCallback callback);
    void RemoveHotkey(int keyCode, int modifiers);
    void EnableKeyFiltering(bool enable);
    void SetBlockedKeys(const std::vector<int>& keys);
};
```

#### Methods

##### `Install()`
Installs the keyboard hook.

**Returns**: `bool` - `true` if hook installed successfully, `false` otherwise

**Example**:
```cpp
#include "hooks/keyboard_hook.h"

if (!KeyboardHook::Install()) {
    std::cerr << "Failed to install keyboard hook" << std::endl;
    return -1;
}

auto& keyboardHook = KeyboardHook::GetInstance();
keyboardHook.EnableKeyFiltering(true);
keyboardHook.SetBlockedKeys({VK_F12, VK_SNAPSHOT}); // Block F12 and Print Screen
```

##### `AddHotkey()`
Adds a hotkey combination with callback.

**Parameters**:
- `keyCode` - Virtual key code
- `modifiers` - Modifier keys (CTRL, ALT, SHIFT)
- `callback` - Function to call when hotkey is pressed

**Example**:
```cpp
void OnScreenshotHotkey() {
    std::cout << "Screenshot hotkey pressed!" << std::endl;
    // Trigger screenshot capture
}

keyboardHook.AddHotkey('S', MOD_CONTROL | MOD_ALT, OnScreenshotHotkey);
```

### ProcessHooks

Manages process creation and termination hooks.

#### Class Definition
```cpp
class ProcessHooks {
public:
    static bool Install();
    static bool Uninstall();
    static ProcessHooks* GetInstance();
    
    void SetProcessCreateCallback(ProcessCreateCallback callback);
    void SetProcessTerminateCallback(ProcessTerminateCallback callback);
    void EnableProcessBlocking(bool enable);
    void SetBlockedProcesses(const std::vector<std::wstring>& processes);
};
```

#### Methods

##### `Install()`
Installs process creation and termination hooks.

**Returns**: `bool` - `true` if hooks installed successfully, `false` otherwise

**Example**:
```cpp
#include "hooks/process_hooks.h"

if (!ProcessHooks::Install()) {
    std::cerr << "Failed to install process hooks" << std::endl;
    return -1;
}

auto& processHooks = ProcessHooks::GetInstance();
processHooks.EnableProcessBlocking(true);
processHooks.SetBlockedProcesses({L"malware.exe", L"spyware.exe"});
```

## Shared Memory Transport APIs

### SharedMemoryTransport

High-performance inter-process communication for frame data.

#### Class Definition
```cpp
class SharedMemoryTransport {
public:
    SharedMemoryTransport();
    ~SharedMemoryTransport();
    
    bool Initialize(const std::wstring& name, size_t bufferSize);
    bool Connect(const std::wstring& name);
    void Shutdown();
    
    bool SendFrame(const FrameData& frameData);
    bool ReceiveFrame(FrameData& frameData);
    bool IsConnected() const;
    
    void SetCompressionEnabled(bool enabled);
    void SetCompressionLevel(int level);
    void SetTimeout(DWORD timeout);
};
```

#### Methods

##### `Initialize()`
Initializes the shared memory transport as a producer.

**Parameters**:
- `name` - Shared memory object name
- `bufferSize` - Size of the shared memory buffer

**Returns**: `bool` - `true` if initialization successful, `false` otherwise

**Example**:
```cpp
#include "shared_memory_transport.h"

SharedMemoryTransport transport;
if (!transport.Initialize(L"UndownUnlock_FrameBuffer", 1024 * 1024 * 10)) {
    std::cerr << "Failed to initialize shared memory transport" << std::endl;
    return -1;
}

transport.SetCompressionEnabled(true);
transport.SetCompressionLevel(6);
transport.SetTimeout(5000); // 5 second timeout
```

##### `Connect()`
Connects to an existing shared memory transport as a consumer.

**Parameters**:
- `name` - Shared memory object name to connect to

**Returns**: `bool` - `true` if connection successful, `false` otherwise

**Example**:
```cpp
SharedMemoryTransport consumer;
if (!consumer.Connect(L"UndownUnlock_FrameBuffer")) {
    std::cerr << "Failed to connect to shared memory transport" << std::endl;
    return -1;
}

FrameData frameData;
while (consumer.IsConnected()) {
    if (consumer.ReceiveFrame(frameData)) {
        // Process received frame
        ProcessFrame(frameData);
    }
}
```

##### `SendFrame()`
Sends frame data through the shared memory transport.

**Parameters**:
- `frameData` - Frame data to send

**Returns**: `bool` - `true` if send successful, `false` otherwise

**Example**:
```cpp
FrameData frameData;
// ... populate frameData ...

if (!transport.SendFrame(frameData)) {
    std::cerr << "Failed to send frame data" << std::endl;
}
```

## Pattern Scanning APIs

### PatternScanner

Memory signature detection for anti-tampering mechanisms.

#### Class Definition
```cpp
class PatternScanner {
public:
    PatternScanner();
    ~PatternScanner();
    
    bool Initialize();
    void AddSignature(const Signature& signature);
    void AddSignatureSet(const SignatureSet& signatureSet);
    bool ScanMemory(HANDLE processHandle, const MemoryRegion& region);
    bool ScanProcess(HANDLE processHandle);
    std::vector<ScanResult> GetScanResults() const;
    void ClearResults();
    
    void SetScanMode(ScanMode mode);
    void SetParallelScanning(bool enabled);
    void SetFuzzyMatching(bool enabled, float threshold = 0.8f);
};
```

#### Methods

##### `Initialize()`
Initializes the pattern scanner.

**Returns**: `bool` - `true` if initialization successful, `false` otherwise

**Example**:
```cpp
#include "memory/pattern_scanner.h"

PatternScanner scanner;
if (!scanner.Initialize()) {
    std::cerr << "Failed to initialize pattern scanner" << std::endl;
    return -1;
}

scanner.SetScanMode(ScanMode::AGGRESSIVE);
scanner.SetParallelScanning(true);
scanner.SetFuzzyMatching(true, 0.85f);
```

##### `AddSignature()`
Adds a signature pattern to scan for.

**Parameters**:
- `signature` - Signature pattern to add

**Example**:
```cpp
Signature signature;
signature.name = "DirectX Present Hook";
signature.pattern = {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10};
signature.mask = "xxxxxxxxxx";
signature.offset = 0x1000;

scanner.AddSignature(signature);
```

##### `ScanProcess()`
Scans a process for signature matches.

**Parameters**:
- `processHandle` - Handle to the process to scan

**Returns**: `bool` - `true` if scan completed successfully, `false` otherwise

**Example**:
```cpp
HANDLE processHandle = OpenProcess(PROCESS_ALL_ACCESS, FALSE, processId);
if (processHandle) {
    if (scanner.ScanProcess(processHandle)) {
        auto results = scanner.GetScanResults();
        for (const auto& result : results) {
            std::cout << "Found signature: " << result.signatureName 
                      << " at address: 0x" << std::hex << result.address << std::endl;
        }
    }
    CloseHandle(processHandle);
}
```

## Utility Framework APIs

### ErrorHandler

Centralized error handling and logging system.

#### Class Definition
```cpp
class ErrorHandler {
public:
    static ErrorHandler& GetInstance();
    
    void LogError(ErrorCategory category, ErrorSeverity severity, 
                  const std::string& message, const std::string& context = "");
    void LogWarning(ErrorCategory category, const std::string& message, 
                   const std::string& context = "");
    void LogInfo(ErrorCategory category, const std::string& message, 
                const std::string& context = "");
    
    void SetLogLevel(ErrorSeverity level);
    void SetLogFile(const std::string& filename);
    void EnableConsoleOutput(bool enable);
    
    std::vector<ErrorEntry> GetRecentErrors(size_t count = 10) const;
    void ClearErrorLog();
};
```

#### Methods

##### `LogError()`
Logs an error with category, severity, and context.

**Parameters**:
- `category` - Error category (DIRECTX, WINDOWS_API, MEMORY, etc.)
- `severity` - Error severity (LOW, MEDIUM, HIGH, CRITICAL)
- `message` - Error message
- `context` - Additional context information

**Example**:
```cpp
#include "utils/error_handler.h"

auto& errorHandler = ErrorHandler::GetInstance();
errorHandler.SetLogLevel(ErrorSeverity::MEDIUM);
errorHandler.SetLogFile("undownunlock.log");
errorHandler.EnableConsoleOutput(true);

errorHandler.LogError(ErrorCategory::DIRECTX, ErrorSeverity::HIGH,
                     "Failed to create staging texture",
                     "FrameExtractor::ExtractFrame");
```

##### `GetRecentErrors()`
Gets recent error entries from the log.

**Parameters**:
- `count` - Number of recent errors to retrieve

**Returns**: `std::vector<ErrorEntry>` - Vector of recent error entries

**Example**:
```cpp
auto recentErrors = errorHandler.GetRecentErrors(5);
for (const auto& error : recentErrors) {
    std::cout << "[" << error.timestamp << "] " 
              << error.category << " - " << error.message << std::endl;
}
```

### PerformanceMonitor

Real-time performance monitoring and metrics collection.

#### Class Definition
```cpp
class PerformanceMonitor {
public:
    static PerformanceMonitor& GetInstance();
    
    void StartTimer(const std::string& name);
    void EndTimer(const std::string& name);
    double GetTimerValue(const std::string& name) const;
    
    void RecordMetric(const std::string& name, double value);
    void IncrementCounter(const std::string& name);
    
    PerformanceStats GetStats() const;
    void ResetStats();
    
    void EnableMonitoring(bool enable);
    void SetSamplingInterval(DWORD interval);
};
```

#### Methods

##### `StartTimer()`
Starts a performance timer.

**Parameters**:
- `name` - Timer name

**Example**:
```cpp
#include "utils/performance_monitor.h"

auto& perfMonitor = PerformanceMonitor::GetInstance();
perfMonitor.EnableMonitoring(true);
perfMonitor.SetSamplingInterval(1000); // 1 second

perfMonitor.StartTimer("FrameCapture");
// ... perform frame capture ...
perfMonitor.EndTimer("FrameCapture");

double captureTime = perfMonitor.GetTimerValue("FrameCapture");
std::cout << "Frame capture took: " << captureTime << "ms" << std::endl;
```

##### `RecordMetric()`
Records a performance metric.

**Parameters**:
- `name` - Metric name
- `value` - Metric value

**Example**:
```cpp
perfMonitor.RecordMetric("FrameRate", 60.0);
perfMonitor.RecordMetric("MemoryUsage", 1024.0);
perfMonitor.IncrementCounter("FramesCaptured");

auto stats = perfMonitor.GetStats();
std::cout << "Average frame rate: " << stats.averageFrameRate << std::endl;
std::cout << "Total frames captured: " << stats.totalFrames << std::endl;
```

### MemoryTracker

Memory leak detection and tracking system.

#### Class Definition
```cpp
class MemoryTracker {
public:
    static MemoryTracker& GetInstance();
    
    void TrackAllocation(void* ptr, size_t size, const std::string& context = "");
    void TrackDeallocation(void* ptr);
    
    MemoryStats GetStats() const;
    std::vector<MemoryLeak> GetLeaks() const;
    
    void EnableTracking(bool enable);
    void SetLeakThreshold(size_t threshold);
    void GenerateReport(const std::string& filename);
};
```

#### Methods

##### `TrackAllocation()`
Tracks a memory allocation.

**Parameters**:
- `ptr` - Pointer to allocated memory
- `size` - Size of allocation
- `context` - Context information for the allocation

**Example**:
```cpp
#include "utils/memory_tracker.h"

auto& memoryTracker = MemoryTracker::GetInstance();
memoryTracker.EnableTracking(true);
memoryTracker.SetLeakThreshold(1024 * 1024); // 1MB threshold

void* ptr = malloc(1024);
memoryTracker.TrackAllocation(ptr, 1024, "FrameBuffer::Allocate");

// ... use memory ...

free(ptr);
memoryTracker.TrackDeallocation(ptr);
```

##### `GetLeaks()`
Gets detected memory leaks.

**Returns**: `std::vector<MemoryLeak>` - Vector of detected memory leaks

**Example**:
```cpp
auto leaks = memoryTracker.GetLeaks();
if (!leaks.empty()) {
    std::cout << "Detected " << leaks.size() << " memory leaks:" << std::endl;
    for (const auto& leak : leaks) {
        std::cout << "  " << leak.context << ": " << leak.size << " bytes" << std::endl;
    }
    memoryTracker.GenerateReport("memory_leaks.txt");
}
```

## Python Consumer APIs

### WindowsGraphicsCapture

Modern Windows Graphics Capture API interface.

#### Class Definition
```python
class WindowsGraphicsCapture:
    def __init__(self):
        self.capture_item = None
        self.frame_pool = None
        self.session = None
        
    def start_capture(self, hwnd=None, monitor=None):
        """Start capturing from window or monitor"""
        
    def stop_capture(self):
        """Stop capturing"""
        
    def get_frame(self):
        """Get the latest captured frame"""
        
    def set_frame_arrived_callback(self, callback):
        """Set callback for when new frames arrive"""
```

#### Methods

##### `start_capture()`
Starts capturing from a window or monitor.

**Parameters**:
- `hwnd` - Window handle to capture (optional)
- `monitor` - Monitor to capture (optional)

**Returns**: `bool` - `True` if capture started successfully

**Example**:
```python
from capture.windows_graphics_capture import WindowsGraphicsCapture

capture = WindowsGraphicsCapture()

# Capture specific window
hwnd = win32gui.FindWindow(None, "Target Application")
if capture.start_capture(hwnd=hwnd):
    print("Started capturing window")
    
    # Set frame callback
    def on_frame_arrived(sender, args):
        frame = capture.get_frame()
        if frame:
            # Process frame
            process_frame(frame)
    
    capture.set_frame_arrived_callback(on_frame_arrived)
```

### EnhancedCapture

Multi-method capture system with fallback chain.

#### Class Definition
```python
class EnhancedCapture:
    def __init__(self):
        self.capture_methods = []
        self.current_method = None
        
    def add_capture_method(self, method):
        """Add a capture method to the fallback chain"""
        
    def start_capture(self, target=None):
        """Start capturing using the best available method"""
        
    def stop_capture(self):
        """Stop capturing"""
        
    def get_frame(self):
        """Get the latest captured frame"""
        
    def get_capture_info(self):
        """Get information about the current capture method"""
```

#### Methods

##### `add_capture_method()`
Adds a capture method to the fallback chain.

**Parameters**:
- `method` - Capture method instance

**Example**:
```python
from capture.enhanced_capture import EnhancedCapture
from capture.windows_graphics_capture import WindowsGraphicsCapture
from capture.dxgi_desktop_duplication import DXGIDesktopDuplication

capture = EnhancedCapture()

# Add capture methods in order of preference
capture.add_capture_method(WindowsGraphicsCapture())
capture.add_capture_method(DXGIDesktopDuplication())

# Start capture with automatic method selection
if capture.start_capture():
    print("Started enhanced capture")
    
    info = capture.get_capture_info()
    print(f"Using capture method: {info['method_name']}")
    print(f"Frame rate: {info['frame_rate']} FPS")
```

### Controller

System control and management interface.

#### Class Definition
```python
class Controller:
    def __init__(self):
        self.hook_manager = None
        self.capture_system = None
        
    def initialize(self):
        """Initialize the controller"""
        
    def inject_dll(self, process_name):
        """Inject DLL into target process"""
        
    def start_capture(self, target=None):
        """Start frame capture"""
        
    def stop_capture(self):
        """Stop frame capture"""
        
    def get_system_status(self):
        """Get current system status"""
        
    def set_configuration(self, config):
        """Set system configuration"""
```

#### Methods

##### `initialize()`
Initializes the controller system.

**Returns**: `bool` - `True` if initialization successful

**Example**:
```python
from tools.controller import Controller

controller = Controller()
if controller.initialize():
    print("Controller initialized successfully")
    
    # Get system status
    status = controller.get_system_status()
    print(f"Hook status: {status['hook_status']}")
    print(f"Capture status: {status['capture_status']}")
    
    # Set configuration
    config = {
        'capture_method': 'windows_graphics_capture',
        'frame_rate': 60,
        'compression': True,
        'quality': 'high'
    }
    controller.set_configuration(config)
```

##### `inject_dll()`
Injects the hooking DLL into a target process.

**Parameters**:
- `process_name` - Name of the target process

**Returns**: `bool` - `True` if injection successful

**Example**:
```python
# Inject into target application
if controller.inject_dll("target_app.exe"):
    print("DLL injected successfully")
    
    # Start capture
    if controller.start_capture():
        print("Capture started")
        
        # ... perform operations ...
        
        controller.stop_capture()
        print("Capture stopped")
```

## Error Handling APIs

### Error Categories

```cpp
enum class ErrorCategory {
    DIRECTX,           // DirectX-related errors
    WINDOWS_API,       // Windows API errors
    MEMORY,           // Memory management errors
    NETWORK,          // Network communication errors
    FILE_IO,          // File I/O errors
    SECURITY,         // Security-related errors
    PERFORMANCE,      // Performance-related errors
    CONFIGURATION,    // Configuration errors
    UNKNOWN           // Unknown error category
};
```

### Error Severity Levels

```cpp
enum class ErrorSeverity {
    LOW,        // Informational messages
    MEDIUM,     // Warnings
    HIGH,       // Errors that may affect functionality
    CRITICAL    // Critical errors that require immediate attention
};
```

### Error Entry Structure

```cpp
struct ErrorEntry {
    std::string timestamp;
    ErrorCategory category;
    ErrorSeverity severity;
    std::string message;
    std::string context;
    std::string stackTrace;
    DWORD threadId;
    DWORD processId;
};
```

## Performance Monitoring APIs

### Performance Stats Structure

```cpp
struct PerformanceStats {
    double averageFrameRate;
    double averageFrameTime;
    double peakFrameRate;
    double minimumFrameRate;
    size_t totalFrames;
    size_t droppedFrames;
    double cpuUsage;
    double memoryUsage;
    std::map<std::string, double> customMetrics;
    std::map<std::string, size_t> counters;
};
```

### Timer Usage Example

```cpp
#include "utils/performance_monitor.h"

auto& perfMonitor = PerformanceMonitor::GetInstance();

// Time a critical operation
perfMonitor.StartTimer("CriticalOperation");
// ... perform operation ...
perfMonitor.EndTimer("CriticalOperation");

// Record custom metrics
perfMonitor.RecordMetric("HookOverhead", 2.5);
perfMonitor.IncrementCounter("HooksInstalled");

// Get performance statistics
auto stats = perfMonitor.GetStats();
std::cout << "Average frame rate: " << stats.averageFrameRate << " FPS" << std::endl;
std::cout << "CPU usage: " << stats.cpuUsage << "%" << std::endl;
```

## Memory Management APIs

### Memory Stats Structure

```cpp
struct MemoryStats {
    size_t totalAllocated;
    size_t totalDeallocated;
    size_t currentUsage;
    size_t peakUsage;
    size_t allocationCount;
    size_t deallocationCount;
    size_t leakCount;
    std::map<std::string, size_t> allocationsByContext;
};
```

### Memory Leak Structure

```cpp
struct MemoryLeak {
    void* address;
    size_t size;
    std::string context;
    std::string stackTrace;
    DWORD threadId;
    DWORD processId;
    std::string timestamp;
};
```

### RAII Wrapper Examples

```cpp
#include "utils/raii_wrappers.h"

// Windows handle wrapper
{
    ScopedHandle handle(CreateFile(L"test.txt", GENERIC_READ, 0, nullptr, 
                                  OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr));
    if (handle.get() != INVALID_HANDLE_VALUE) {
        // Use handle
        // Automatically closed when scope ends
    }
}

// COM interface wrapper
{
    ComPtr<ID3D11Device> device;
    // ... create device ...
    // Automatically released when scope ends
}

// Smart pointer usage
{
    std::unique_ptr<FrameExtractor> extractor = std::make_unique<FrameExtractor>();
    extractor->Initialize(device);
    // Automatically deleted when scope ends
}
```

## Conclusion

This API reference provides comprehensive documentation for all public interfaces in the UndownUnlock system. Each API includes detailed parameter descriptions, return values, usage examples, and best practices.

For additional information about specific components, see the [Architecture Documentation](ARCHITECTURE.md) and [Troubleshooting Guide](TROUBLESHOOTING.md).

The APIs are designed to be intuitive, consistent, and well-documented to facilitate easy integration and development with the UndownUnlock framework. 