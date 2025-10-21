# UndownUnlock Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Core Architecture](#core-architecture)
3. [Component Details](#component-details)
4. [Data Flow Patterns](#data-flow-patterns)
5. [Integration Patterns](#integration-patterns)
6. [Security Architecture](#security-architecture)
7. [Performance Architecture](#performance-architecture)
8. [Deployment Architecture](#deployment-architecture)

## System Overview

UndownUnlock is a sophisticated DirectX and Windows API hooking framework designed for educational purposes. It intercepts graphics API calls and Windows system functions to enable frame extraction, window management control, and other system-level monitoring capabilities.

### Key Design Principles
- **Modularity**: Each component is self-contained with clear interfaces
- **Extensibility**: Plugin-based architecture for new hook types
- **Reliability**: Comprehensive error handling and resource management
- **Performance**: Optimized for minimal overhead and maximum throughput
- **Security**: Anti-detection mechanisms and integrity protection

### System Capabilities
- DirectX 11/12 frame capture and extraction
- Windows API hooking for process and window control
- Pattern-based memory scanning and signature detection
- Inter-process communication via shared memory
- Real-time performance monitoring and optimization
- Comprehensive error handling and recovery

## Core Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    UndownUnlock System                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Python    │  │     C++     │  │   Windows   │        │
│  │  Consumer   │  │   Hooking   │  │     API     │        │
│  │   Layer     │  │   Engine    │  │   Layer     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Shared    │  │   Pattern   │  │   Utility   │        │
│  │  Memory     │  │  Scanning   │  │  Framework  │        │
│  │ Transport   │  │   Engine    │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Target Application                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  DirectX    │  │   Windows   │  │   Process   │        │
│  │   Hooks     │  │    API      │  │  Control    │        │
│  │             │  │   Hooks     │  │   Hooks     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Frame     │  │   Shared    │  │   Pattern   │        │
│  │ Extractor   │  │  Memory     │  │  Scanner    │        │
│  │             │  │ Transport   │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Error     │  │  Memory     │  │ Performance │        │
│  │  Handler    │  │  Tracker    │  │  Monitor    │        │
│  │             │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. DirectX Hooking Engine

**Purpose**: Intercepts DirectX API calls to capture frame data
**Location**: `src/hooks/dx_hook_core.cpp`, `src/hooks/swap_chain_hook.cpp`

**Key Components**:
- **DXHookCore**: Main hook management and initialization
- **SwapChainHook**: IDXGISwapChain::Present interception
- **FrameExtractor**: Frame data extraction and processing
- **ComInterfaceWrapper**: RAII-based COM interface management

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                    DirectX Hooking Engine                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ DXHookCore  │  │SwapChainHook│  │FrameExtractor│        │
│  │             │  │             │  │             │        │
│  │ • Initialize│  │ • VTable    │  │ • Staging   │        │
│  │ • Hook      │  │   Hooks     │  │   Textures  │        │
│  │ • Manage    │  │ • Present   │  │ • Format    │        │
│  │   State     │  │   Intercept │  │   Convert   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   COM       │  │   Factory   │  │   Device    │        │
│  │ Interface   │  │   Hooks     │  │   Hooks     │        │
│  │ Wrapper     │  │             │  │             │        │
│  │             │  │ • Device    │  │ • Context   │        │
│  │ • RAII      │  │   Creation  │  │   Hooks     │        │
│  │ • Auto      │  │ • SwapChain │  │ • Resource  │        │
│  │   Cleanup   │  │   Creation  │  │   Hooks     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 2. Windows API Hooking System

**Purpose**: Intercepts Windows API calls for process and window control
**Location**: `src/hooks/windows_api/`

**Key Components**:
- **WindowsApiHookManager**: Central hook management
- **KeyboardHook**: Keyboard input interception
- **ProcessHooks**: Process creation and termination hooks
- **WindowHooks**: Window management and focus control

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                Windows API Hooking System                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ WindowsApi  │  │  Keyboard   │  │   Process   │        │
│  │ HookManager │  │    Hook     │  │   Hooks     │        │
│  │             │  │             │  │             │        │
│  │ • Hook      │  │ • Key       │  │ • Create    │        │
│  │   Registry  │  │   Intercept │  │   Process   │        │
│  │ • Hook      │  │ • Input     │  │ • Terminate │        │
│  │   Dispatch  │  │   Filtering │  │   Process   │        │
│  │ • Hook      │  │ • Hotkey    │  │ • Process   │        │
│  │   Cleanup   │  │   Support   │  │   Control   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Window    │  │   Clipboard │  │   Focus     │        │
│  │   Hooks     │  │    Hooks    │  │   Hooks     │        │
│  │             │  │             │  │             │        │
│  │ • SetWindow │  │ • Get/Set   │  │ • Get/Set   │        │
│  │   Pos       │  │   Clipboard │  │   Focus     │        │
│  │ • Show      │  │ • Clipboard │  │ • Window    │        │
│  │   Window    │  │   Protection│  │   Activation│        │
│  │ • Window    │  │ • Clipboard │  │ • Focus     │        │
│  │   Styles    │  │   Encryption│  │   Tracking  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 3. Shared Memory Transport System

**Purpose**: High-performance inter-process communication for frame data
**Location**: `src/shared/shared_memory_transport.cpp`

**Key Components**:
- **SharedMemoryTransport**: Main transport implementation
- **RingBuffer**: Lock-free circular buffer for frame data
- **Synchronization**: SRW locks and atomic operations
- **Compression**: Optional frame compression

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                Shared Memory Transport System               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ SharedMemory│  │   Ring      │  │ Synchroniz- │        │
│  │ Transport   │  │  Buffer     │  │   ation     │        │
│  │             │  │             │  │             │        │
│  │ • Memory    │  │ • Circular  │  │ • SRW       │        │
│  │   Mapping   │  │   Buffer    │  │   Locks     │        │
│  │ • Producer  │  │ • Lock-free │  │ • Atomic    │        │
│  │   Interface │  │   Access    │  │   Operations│        │
│  │ • Consumer  │  │ • Overflow  │  │ • Wait-free │        │
│  │   Interface │  │   Handling  │  │   Queues    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Compression │  │   Metadata  │  │   Error     │        │
│  │   Engine    │  │   Channel   │  │  Handling   │        │
│  │             │  │             │  │             │        │
│  │ • Frame     │  │ • Frame     │  │ • Timeout   │        │
│  │   Compress  │  │   Metadata  │  │   Detection │        │
│  │ • Adaptive  │  │ • Timestamp │  │ • Recovery  │        │
│  │   Quality   │  │ • Format    │  │   Mechanisms│        │
│  │ • Hardware  │  │ • Size      │  │ • Diagnostic│        │
│  │   Accel     │  │   Info      │  │   Logging   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 4. Pattern Scanning Engine

**Purpose**: Memory signature detection for anti-tampering mechanisms
**Location**: `src/memory/pattern_scanner.cpp`, `src/signatures/`

**Key Components**:
- **PatternScanner**: Core scanning engine
- **DXSignatures**: DirectX-specific signatures
- **LockdownSignatures**: Anti-detection signatures
- **MemoryScanner**: Memory region analysis

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                Pattern Scanning Engine                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Pattern     │  │   Memory    │  │   Signature │        │
│  │ Scanner     │  │  Scanner    │  │   Database  │        │
│  │             │  │             │  │             │        │
│  │ • Boyer-    │  │ • Memory    │  │ • DX        │        │
│  │   Moore     │  │   Regions   │  │   Signatures│        │
│  │ • Fuzzy     │  │ • PE        │  │ • Lockdown  │        │
│  │   Matching  │  │   Sections  │  │   Signatures│        │
│  │ • Multi-    │  │ • JIT       │  │ • Version   │        │
│  │   Pattern   │  │   Regions   │  │   Specific  │        │
│  │ • Parallel  │  │ • Permissions│  │ • Auto-gen  │        │
│  │   Scanning  │  │ • Boundaries │  │   Signatures│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Patch     │  │   Verify    │  │   Rollback  │        │
│  │  Engine     │  │   Engine    │  │   Engine    │        │
│  │             │  │             │  │             │        │
│  │ • Signature │  │ • Patch     │  │ • Failed    │        │
│  │   Patching  │  │   Validation│  │   Patch     │        │
│  │ • Hot       │  │ • Integrity │  │   Rollback  │        │
│  │   Patching  │  │   Checking  │  │ • State     │        │
│  │ • Safe      │  │ • Runtime   │  │   Recovery  │        │
│  │   Patching  │  │   Monitoring│  │ • Auto-     │        │
│  │ • Rollback  │  │ • Detection │  │   Recovery  │        │
│  │   Support   │  │   Avoidance │  │   Support   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 5. Utility Framework

**Purpose**: Common utilities for error handling, memory management, and performance monitoring
**Location**: `src/utils/`, `include/utils/`

**Key Components**:
- **ErrorHandler**: Centralized error handling and logging
- **MemoryTracker**: Memory leak detection and tracking
- **PerformanceMonitor**: Performance metrics and monitoring
- **RAIIWrappers**: Resource management wrappers

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Utility Framework                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Error     │  │   Memory    │  │ Performance │        │
│  │  Handler    │  │  Tracker    │  │  Monitor    │        │
│  │             │  │             │  │             │        │
│  │ • Error     │  │ • Memory    │  │ • Timing    │        │
│  │   Categories│  │   Allocation│  │   Metrics   │        │
│  │ • Severity  │  │ • Leak      │  │ • CPU       │        │
│  │   Levels    │  │   Detection │  │   Usage     │        │
│  │ • Error     │  │ • Memory    │  │ • Memory    │        │
│  │   Recovery  │  │   Statistics│  │   Usage     │        │
│  │ • Logging   │  │ • Auto-     │  │ • Frame     │        │
│  │   System    │  │   Cleanup   │  │   Rates     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   RAII      │  │   Smart     │  │   Crash     │        │
│  │ Wrappers    │  │  Pointers   │  │  Reporter   │        │
│  │             │  │             │  │             │        │
│  │ • Windows   │  │ • Unique    │  │ • Crash     │        │
│  │   Handles   │  │   Ptr       │  │   Detection │        │
│  │ • COM       │  │ • Shared    │  │ • Stack     │        │
│  │   Interfaces│  │   Ptr       │  │   Traces    │        │
│  │ • File      │  │ • Weak      │  │ • Memory    │        │
│  │   Handles   │  │   Ptr       │  │   Dumps     │        │
│  │ • Thread    │  │ • Custom    │  │ • Error     │        │
│  │   Handles   │  │   Allocators│  │ • Reports   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 6. Python Consumer Layer

**Purpose**: High-level interface for frame capture and system control
**Location**: `python/capture/`, `python/tools/`

**Key Components**:
- **WindowsGraphicsCapture**: Modern capture API
- **DXGIDesktopDuplication**: DXGI-based capture
- **EnhancedCapture**: Multi-method capture system
- **Controller**: System control interface

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                Python Consumer Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Windows     │  │   DXGI      │  │ Enhanced    │        │
│  │ Graphics    │  │  Desktop    │  │  Capture    │        │
│  │  Capture    │  │ Duplication │  │             │        │
│  │             │  │             │  │             │        │
│  │ • Modern    │  │ • DXGI      │  │ • Multi-    │        │
│  │   API       │  │   Desktop   │  │   Method    │        │
│  │ • Hardware  │  │   Dupl.     │  │   Capture   │        │
│  │   Accel     │  │ • Fallback  │  │ • Fallback  │        │
│  │ • Low       │  │   Method    │  │   Chain     │        │
│  │   Overhead  │  │ • Direct3D  │  │ • Adaptive  │        │
│  │ • Security  │  │   Capture   │  │   Quality   │        │
│  │   Compliant │  │ • GDI       │  │ • Error     │        │
│  │             │  │   Fallback  │  │   Recovery  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Controller  │  │ Named Pipe  │  │   Remote    │        │
│  │             │  │  Manager    │  │   Client    │        │
│  │             │  │             │  │             │        │
│  │ • System    │  │ • IPC       │  │ • Remote    │        │
│  │   Control   │  │   Protocol  │  │   Control   │        │
│  │ • Hook      │  │ • Security  │  │ • Network   │        │
│  │   Management│  │   Features  │  │   Protocol  │        │
│  │ • Config    │  │ • Async     │  │ • Encryption│        │
│  │   Management│  │   I/O       │  │ • Auth      │        │
│  │ • Monitor   │  │ • Error     │  │ • Session   │        │
│  │   Interface │  │   Handling  │  │   Management│        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Patterns

### 1. Frame Capture Flow
```
Target Application
       │
       ▼
DirectX API Call (Present)
       │
       ▼
SwapChain Hook (Intercept)
       │
       ▼
Frame Extractor (Process)
       │
       ▼
Shared Memory Transport
       │
       ▼
Python Consumer
       │
       ▼
Frame Processing/Display
```

### 2. Hook Installation Flow
```
DLL Injection
       │
       ▼
Hook Manager Initialization
       │
       ▼
Target Function Detection
       │
       ▼
VTable Hook Installation
       │
       ▼
Hook Verification
       │
       ▼
Hook Activation
```

### 3. Error Handling Flow
```
Error Detection
       │
       ▼
Error Classification
       │
       ▼
Error Context Collection
       │
       ▼
Error Recovery Attempt
       │
       ▼
Error Logging
       │
       ▼
Error Reporting
```

### 4. Pattern Scanning Flow
```
Memory Region Analysis
       │
       ▼
Signature Database Query
       │
       ▼
Pattern Matching
       │
       ▼
Match Verification
       │
       ▼
Patch Application
       │
       ▼
Patch Validation
```

## Integration Patterns

### 1. Component Communication
- **Synchronous**: Direct function calls for critical operations
- **Asynchronous**: Event-driven communication for non-critical operations
- **Shared Memory**: High-performance data transfer between processes
- **Named Pipes**: Control and configuration communication

### 2. Error Propagation
- **Exception-based**: C++ exceptions for recoverable errors
- **Error Codes**: Return codes for non-exceptional conditions
- **Error Categories**: Classification for different error types
- **Error Recovery**: Automatic recovery mechanisms

### 3. Resource Management
- **RAII**: Automatic resource cleanup
- **Smart Pointers**: Automatic memory management
- **Reference Counting**: COM interface management
- **Resource Pools**: Efficient resource reuse

### 4. Performance Optimization
- **Object Pooling**: Reduce allocation overhead
- **Lock-free Algorithms**: Minimize synchronization overhead
- **Hardware Acceleration**: GPU-accelerated operations
- **Adaptive Quality**: Dynamic quality adjustment

## Security Architecture

### 1. Anti-Detection Mechanisms
- **Hook Concealment**: Hide hook presence from detection tools
- **Timing Normalization**: Prevent timing-based detection
- **Call Stack Spoofing**: Mask hook call stacks
- **Code Integrity**: Protect against tampering

### 2. Access Control
- **Process Isolation**: Separate hook processes from target
- **Memory Protection**: Protect hook memory regions
- **API Filtering**: Control API access patterns
- **Integrity Checking**: Verify code integrity

### 3. Communication Security
- **Encrypted IPC**: Secure inter-process communication
- **Authentication**: Verify communication endpoints
- **Session Management**: Secure session handling
- **Audit Logging**: Security event logging

## Performance Architecture

### 1. Optimization Strategies
- **Minimal Overhead**: Optimize hook execution paths
- **Efficient Memory**: Reduce memory allocation overhead
- **Parallel Processing**: Utilize multiple CPU cores
- **Hardware Acceleration**: Leverage GPU capabilities

### 2. Monitoring and Metrics
- **Performance Counters**: Real-time performance monitoring
- **Resource Usage**: Memory and CPU usage tracking
- **Latency Measurement**: Hook overhead measurement
- **Throughput Analysis**: Frame processing rates

### 3. Adaptive Systems
- **Quality Scaling**: Dynamic quality adjustment
- **Resource Management**: Adaptive resource allocation
- **Load Balancing**: Distribute processing load
- **Failure Recovery**: Automatic performance recovery

## Deployment Architecture

### 1. Build System
- **CMake**: Cross-platform build configuration
- **Dependency Management**: Automated dependency resolution
- **CI/CD Pipeline**: Automated build and testing
- **Artifact Management**: Build artifact versioning

### 2. Testing Framework
- **Unit Testing**: Component-level testing
- **Integration Testing**: System-level testing
- **Performance Testing**: Performance regression testing
- **Security Testing**: Security vulnerability testing

### 3. Deployment Models
- **DLL Injection**: Runtime hook injection
- **Static Linking**: Compile-time integration
- **Service Model**: Windows service deployment
- **Container Model**: Isolated deployment

### 4. Monitoring and Maintenance
- **Health Monitoring**: System health tracking
- **Error Reporting**: Automated error reporting
- **Performance Monitoring**: Real-time performance tracking
- **Update Management**: Automated update deployment

## Conclusion

The UndownUnlock architecture provides a robust, scalable, and maintainable foundation for DirectX and Windows API hooking. The modular design enables easy extension and modification while maintaining high performance and reliability. The comprehensive error handling, resource management, and security features ensure production-ready operation in demanding environments.

The architecture follows modern software engineering principles including separation of concerns, dependency injection, and comprehensive testing. The performance optimization strategies ensure minimal overhead while the security features provide protection against detection and tampering.

This architecture serves as the foundation for all future development and provides a clear roadmap for system evolution and enhancement. 