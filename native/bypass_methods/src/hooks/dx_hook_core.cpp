#include "../../include/dx_hook_core.h"
#include "../../include/frame_extractor.h"
#include "../../include/shared_memory_transport.h"
#include "../../include/com_hooks/factory_hooks.h"
#include "../../include/hooks/com_interface_wrapper.h"
#include "../../include/raii_wrappers.h"
#include "../../include/error_handler.h"
#include "../../include/performance_monitor.h"
#include "../../include/memory_tracker.h"
#include <iostream>

namespace UndownUnlock {
namespace DXHook {

// Initialize the singleton instance
DXHookCore* DXHookCore::s_instance = nullptr;

DXHookCore::DXHookCore()
    : m_initialized(false) {
    // Initialize utility components
    ErrorHandler::Initialize();
    PerformanceMonitor::Initialize();
    MemoryTracker::Initialize();
}

DXHookCore::~DXHookCore() {
    Shutdown();
    
    // Shutdown utility components
    MemoryTracker::Shutdown();
    PerformanceMonitor::Shutdown();
    ErrorHandler::Shutdown();
}

DXHookCore& DXHookCore::GetInstance() {
    if (!s_instance) {
        s_instance = new DXHookCore();
    }
    return *s_instance;
}

bool DXHookCore::Initialize() {
    // Avoid double initialization
    if (GetInstance().m_initialized) {
        return true;
    }
    
    DXHookCore& instance = GetInstance();
    
    // Start performance monitoring for initialization
    auto init_operation = PerformanceMonitor::GetInstance().start_operation("dx_hook_core_initialization");
    
    // Set error context for initialization
    ErrorContext context;
    context.set("operation", "dx_hook_core_initialization");
    context.set("component", "DXHookCore");
    ErrorHandler::GetInstance().set_error_context(context);
    
    try {
        ErrorHandler::GetInstance().info(
            "Initializing DirectX Hook Core...",
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // Create the components with memory tracking
        auto& memory_tracker = MemoryTracker::GetInstance();
        
        auto scanner_allocation = memory_tracker.TrackAllocation(
            "memory_scanner", sizeof(MemoryScanner), MemoryCategory::SYSTEM
        );
        instance.m_memoryScanner = std::make_unique<MemoryScanner>();
        memory_tracker.ReleaseAllocation(scanner_allocation);
        
        auto hook_allocation = memory_tracker.TrackAllocation(
            "swap_chain_hook", sizeof(SwapChainHook), MemoryCategory::SYSTEM
        );
        instance.m_swapChainHook = std::make_unique<SwapChainHook>();
        memory_tracker.ReleaseAllocation(hook_allocation);
        
        auto extractor_allocation = memory_tracker.TrackAllocation(
            "frame_extractor", sizeof(FrameExtractor), MemoryCategory::GRAPHICS
        );
        instance.m_frameExtractor = std::make_unique<FrameExtractor>();
        memory_tracker.ReleaseAllocation(extractor_allocation);
        
        auto transport_allocation = memory_tracker.TrackAllocation(
            "shared_memory_transport", sizeof(SharedMemoryTransport), MemoryCategory::SYSTEM
        );
        instance.m_sharedMemory = std::make_unique<SharedMemoryTransport>("UndownUnlockFrameData");
        memory_tracker.ReleaseAllocation(transport_allocation);
        
        // Initialize the memory scanner
        auto scanner_operation = PerformanceMonitor::GetInstance().start_operation("memory_scanner_initialization");
        if (!instance.m_memoryScanner->FindDXModules()) {
            PerformanceMonitor::GetInstance().end_operation(scanner_operation);
            ErrorHandler::GetInstance().error(
                "Failed to find DirectX modules",
                ErrorCategory::GRAPHICS,
                __FUNCTION__, __FILE__, __LINE__
            );
            return false;
        }
        PerformanceMonitor::GetInstance().end_operation(scanner_operation);
        
        // Initialize the shared memory transport
        auto transport_operation = PerformanceMonitor::GetInstance().start_operation("shared_memory_initialization");
        if (!instance.m_sharedMemory->Initialize()) {
            PerformanceMonitor::GetInstance().end_operation(transport_operation);
            ErrorHandler::GetInstance().error(
                "Failed to initialize shared memory transport",
                ErrorCategory::SYSTEM,
                __FUNCTION__, __FILE__, __LINE__
            );
            return false;
        }
        PerformanceMonitor::GetInstance().end_operation(transport_operation);
        
        // Set up callback for when a SwapChain is hooked
        instance.m_swapChainHook->SetPresentCallback([&instance](IDXGISwapChain* pSwapChain) {
            // Start performance monitoring for frame extraction
            auto frame_operation = PerformanceMonitor::GetInstance().start_operation("frame_extraction");
            
            // Set error context for frame extraction
            ErrorContext frame_context;
            frame_context.set("operation", "frame_extraction");
            frame_context.set("component", "SwapChainCallback");
            ErrorHandler::GetInstance().set_error_context(frame_context);
            
            // Hook fired - extract a frame
            try {
                // Use RAII wrapper to safely get the device from the swap chain
                auto deviceWrapper = Hooks::GetInterfaceChecked<ID3D11Device>(pSwapChain, __uuidof(ID3D11Device), "GetDevice");
                
                if (deviceWrapper) {
                    // Get the immediate context using RAII wrapper
                    ID3D11DeviceContext* context = nullptr;
                    deviceWrapper->GetImmediateContext(&context);
                    
                    if (context) {
                        // Wrap the context for automatic cleanup
                        Hooks::D3D11DeviceContextWrapper contextWrapper(context, true);
                        
                        // Initialize the frame extractor if not already
                        static bool extractorInitialized = false;
                        if (!extractorInitialized) {
                            auto init_operation = PerformanceMonitor::GetInstance().start_operation("frame_extractor_initialization");
                            instance.m_frameExtractor->Initialize(deviceWrapper.Get(), contextWrapper.Get());
                            instance.m_frameExtractor->SetSharedMemoryTransport(instance.m_sharedMemory.get());
                            PerformanceMonitor::GetInstance().end_operation(init_operation);
                            extractorInitialized = true;
                        }
                        
                        // Extract the frame
                        instance.m_frameExtractor->ExtractFrame(pSwapChain);
                        
                        // RAII wrappers automatically release interfaces when they go out of scope
                    } else {
                        ErrorHandler::GetInstance().error(
                        "Failed to get immediate context from device",
                        ErrorCategory::GRAPHICS,
                        __FUNCTION__, __FILE__, __LINE__
                    );
                    }
                }
            }
            catch (const std::exception& e) {
                ErrorHandler::GetInstance().error(
                    "Exception in Present callback: " + std::string(e.what()),
                    ErrorCategory::GRAPHICS,
                    __FUNCTION__, __FILE__, __LINE__
                );
            }
            
            // End performance monitoring
            PerformanceMonitor::GetInstance().end_operation(frame_operation);
            
            // Clear error context
            ErrorHandler::GetInstance().clear_error_context();
        });
        
        // Try to find and hook a SwapChain
        auto hook_operation = PerformanceMonitor::GetInstance().start_operation("swap_chain_hook_installation");
        bool hookResult = instance.m_swapChainHook->FindAndHookSwapChain();
        PerformanceMonitor::GetInstance().end_operation(hook_operation);
        
        if (!hookResult) {
            ErrorHandler::GetInstance().info(
                "Initial SwapChain hook not found, waiting for application to create one...",
                ErrorCategory::GRAPHICS,
                __FUNCTION__, __FILE__, __LINE__
            );
            // This is not a fatal error - we'll hook when the app creates a SwapChain
        }
        
        // Initialize the factory hooks for COM interface runtime detection
        auto factory_operation = PerformanceMonitor::GetInstance().start_operation("factory_hooks_initialization");
        bool factoryHookResult = FactoryHooks::GetInstance().Initialize();
        PerformanceMonitor::GetInstance().end_operation(factory_operation);
        
        if (!factoryHookResult) {
            ErrorHandler::GetInstance().warning(
                "Failed to initialize factory hooks",
                ErrorCategory::GRAPHICS,
                __FUNCTION__, __FILE__, __LINE__
            );
            // Continue anyway, as we might still hook through other methods
        } else {
            ErrorHandler::GetInstance().info(
                "COM Interface runtime detection initialized",
                ErrorCategory::GRAPHICS,
                __FUNCTION__, __FILE__, __LINE__
            );
        }
        
        // Set flag indicating initialization succeeded
        instance.m_initialized = true;
        ErrorHandler::GetInstance().info(
            "DirectX Hook Core initialized successfully",
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring for initialization
        PerformanceMonitor::GetInstance().end_operation(init_operation);
        
        // Clear error context
        ErrorHandler::GetInstance().clear_error_context();
        
        return true;
    }
    catch (const std::exception& e) {
        // End performance monitoring on error
        PerformanceMonitor::GetInstance().end_operation(init_operation);
        
        ErrorHandler::GetInstance().error(
            "Exception in DXHookCore::Initialize: " + std::string(e.what()),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // Clear error context
        ErrorHandler::GetInstance().clear_error_context();
        
        return false;
    }
}

void DXHookCore::Shutdown() {
    if (!GetInstance().m_initialized) {
        return;
    }
    
    DXHookCore& instance = GetInstance();
    
    // Start performance monitoring for shutdown
    auto shutdown_operation = PerformanceMonitor::GetInstance().start_operation("dx_hook_core_shutdown");
    
    // Set error context for shutdown
    ErrorContext context;
    context.set("operation", "dx_hook_core_shutdown");
    context.set("component", "DXHookCore");
    ErrorHandler::GetInstance().set_error_context(context);
    
    ErrorHandler::GetInstance().info(
        "Shutting down DirectX Hook Core...",
        ErrorCategory::GRAPHICS,
        __FUNCTION__, __FILE__, __LINE__
    );
    
    try {
        // Shut down factory hooks
        FactoryHooks::GetInstance().Shutdown();
        
        // Clear any callbacks
        instance.m_frameCallbacks.clear();
        
        // Release components in reverse order with memory tracking
        auto& memory_tracker = MemoryTracker::GetInstance();
        
        if (instance.m_sharedMemory) {
            memory_tracker.TrackAllocation("shared_memory_cleanup", 0, MemoryCategory::SYSTEM);
            instance.m_sharedMemory.reset();
        }
        
        if (instance.m_frameExtractor) {
            memory_tracker.TrackAllocation("frame_extractor_cleanup", 0, MemoryCategory::GRAPHICS);
            instance.m_frameExtractor.reset();
        }
        
        if (instance.m_swapChainHook) {
            memory_tracker.TrackAllocation("swap_chain_hook_cleanup", 0, MemoryCategory::SYSTEM);
            instance.m_swapChainHook.reset();
        }
        
        if (instance.m_memoryScanner) {
            memory_tracker.TrackAllocation("memory_scanner_cleanup", 0, MemoryCategory::SYSTEM);
            instance.m_memoryScanner.reset();
        }
        
        instance.m_initialized = false;
        
        ErrorHandler::GetInstance().info(
            "DirectX Hook Core shutdown complete",
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring
        PerformanceMonitor::GetInstance().end_operation(shutdown_operation);
        
        // Clear error context
        ErrorHandler::GetInstance().clear_error_context();
        
    } catch (const std::exception& e) {
        // End performance monitoring on error
        PerformanceMonitor::GetInstance().end_operation(shutdown_operation);
        
        ErrorHandler::GetInstance().error(
            "Exception in DXHookCore::Shutdown: " + std::string(e.what()),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // Clear error context
        ErrorHandler::GetInstance().clear_error_context();
    }
}

size_t DXHookCore::RegisterFrameCallback(std::function<void(const void*, size_t, uint32_t, uint32_t)> callback) {
    if (!callback) {
        ErrorHandler::GetInstance().warning(
            "Attempted to register null callback",
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        return 0;
    }
    
    DXHookCore& instance = GetInstance();
    
    std::lock_guard<std::mutex> lock(instance.m_callbackMutex);
    instance.m_frameCallbacks.push_back(callback);
    
    size_t handle = instance.m_frameCallbacks.size() - 1;
    
    ErrorHandler::GetInstance().debug(
        "Frame callback registered with handle: " + std::to_string(handle),
        ErrorCategory::GRAPHICS,
        __FUNCTION__, __FILE__, __LINE__
    );
    
    // Return the index as a handle
    return handle;
}

void DXHookCore::UnregisterFrameCallback(size_t handle) {
    DXHookCore& instance = GetInstance();
    
    std::lock_guard<std::mutex> lock(instance.m_callbackMutex);
    if (handle < instance.m_frameCallbacks.size()) {
        // Replace with an empty function instead of resizing the vector
        // to avoid invalidating other handles
        instance.m_frameCallbacks[handle] = [](const void*, size_t, uint32_t, uint32_t) {};
        
        ErrorHandler::GetInstance().debug(
            "Frame callback unregistered with handle: " + std::to_string(handle),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
    } else {
        ErrorHandler::GetInstance().warning(
            "Attempted to unregister invalid callback handle: " + std::to_string(handle),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
    }
}

bool DXHookCore::IsInitialized() const {
    return m_initialized.load();
}

} // namespace DXHook
} // namespace UndownUnlock 








