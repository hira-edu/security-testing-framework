#include "../../include/hooks/dx_hook_core.h"
#include "../../include/hooks/com_interface_wrapper.h"
#include "../../include/raii_wrappers.h"
#include "../../include/error_handler.h"
#include "../../include/performance_monitor.h"
#include "../../include/memory_tracker.h"
#include <iostream>
#include <windows.h>

// --- DirectXHookManager Method Implementations ---

DirectXHookManager& DirectXHookManager::GetInstance() {
    static DirectXHookManager instance;
    return instance;
}

DirectXHookManager::DirectXHookManager()
    : dependenciesChecked_(false),
      presentHookInstalled_(false) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::Constructor");
    auto memTracker = MemoryTracker::GetInstance().TrackAllocation("DirectXHookManager", sizeof(DirectXHookManager));
    
    ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Constructor called");
    std::cout << "[DirectXHookManager] Constructor." << std::endl;
}

DirectXHookManager::~DirectXHookManager() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::Destructor");
    
    ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Destructor called");
    std::cout << "[DirectXHookManager] Destructor." << std::endl;
    Shutdown();
}

void DirectXHookManager::Initialize() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::Initialize");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("DirectXHookManager::Initialize");
    
    if (dependenciesChecked_ && presentHookInstalled_) {
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Already initialized and Present hook is active");
        std::cout << "[DirectXHookManager::Initialize] Already initialized and Present hook is active." << std::endl;
        return;
    }
    
    if (dependenciesChecked_ && !activeSwapChain_) {
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Initialized, but still waiting for SwapChain");
        std::cout << "[DirectXHookManager::Initialize] Initialized, but still waiting for SwapChain..." << std::endl;
        return;
    }

    ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Initializing DirectX hook manager");
    std::cout << "[DirectXHookManager::Initialize] Initializing..." << std::endl;

    // 1. Check if D3D11/DXGI are loaded in the process (only once)
    if (!dependenciesChecked_) {
        auto dllCheckTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::CheckDependencies");
        
        HMODULE hD3D11 = GetModuleHandleA("d3d11.dll");
        HMODULE hDXGI = GetModuleHandleA("dxgi.dll");

        if (!hD3D11 || !hDXGI) {
            ErrorHandler::GetInstance().LogError("DirectXHookManager", "D3D11/DXGI DLLs not found. DirectX hooking cannot proceed", 
                ErrorSeverity::CRITICAL, ErrorCategory::DEPENDENCY);
            std::cout << "[DirectXHookManager::Initialize] D3D11/DXGI DLLs not found. DirectX hooking cannot proceed." << std::endl;
            dependenciesChecked_ = true;
            return;
        }
        
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "D3D11.dll and DXGI.dll are loaded");
        std::cout << "[DirectXHookManager::Initialize] D3D11.dll and DXGI.dll are loaded." << std::endl;
        dependenciesChecked_ = true;
    }

    // The D3D11CreateDeviceAndSwapChainHook (installed by WindowsApiHookManager)
    // will call StoreSwapChainPointer when a swap chain is created.
    // Initialize() here ensures dependencies are checked and logs readiness.

    // Verify that WindowsApiHookManager has installed the D3D11CreateDeviceAndSwapChainHook.
    // This is crucial for DirectXHookManager to receive swap chain pointers.
    auto* apiManager = &WindowsApiHookManager::GetInstance();
    auto* createDeviceHook = apiManager->GetHook<D3D11CreateDeviceAndSwapChainHook>();

    if (createDeviceHook && createDeviceHook->IsInstalled()) {
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "D3D11CreateDeviceAndSwapChainHook is installed by WindowsApiHookManager");
        std::cout << "[DirectXHookManager::Initialize] D3D11CreateDeviceAndSwapChainHook is installed by WindowsApiHookManager." << std::endl;
    } else {
        ErrorHandler::GetInstance().LogError("DirectXHookManager", "D3D11CreateDeviceAndSwapChainHook is NOT installed by WindowsApiHookManager. DirectXHookManager will not receive SwapChain pointers", 
            ErrorSeverity::CRITICAL, ErrorCategory::HOOK);
        std::cerr << "[DirectXHookManager::Initialize] CRITICAL: D3D11CreateDeviceAndSwapChainHook is NOT installed by WindowsApiHookManager. DirectXHookManager will not receive SwapChain pointers." << std::endl;
        // No point in proceeding if the capture mechanism isn't there.
        // However, dependenciesChecked_ should still be true if DLLs are present.
        return;
    }

    // If activeSwapChain_ is already populated by a previous call to StoreSwapChainPointer,
    // and the hook isn't installed, StoreSwapChainPointer would have tried to install it.
    // So, just log current state.
    if (activeSwapChain_ && swapChainHook_ && swapChainHook_->IsInstalled()) {
        presentHookInstalled_ = true;
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Present hook is active on SwapChain: " + std::to_string(reinterpret_cast<uintptr_t>(activeSwapChain_.Get())));
        std::cout << "[DirectXHookManager::Initialize] Present hook is active on SwapChain: " << activeSwapChain_.Get() << std::endl;
    } else if (activeSwapChain_ && swapChainHook_ && !swapChainHook_->IsInstalled()) {
        ErrorHandler::GetInstance().LogError("DirectXHookManager", "SwapChain is stored but Present hook failed to install earlier. Check logs from StoreSwapChainPointer", 
            ErrorSeverity::WARNING, ErrorCategory::HOOK);
        std::cerr << "[DirectXHookManager::Initialize] SwapChain is stored (" << activeSwapChain_.Get() << ") but Present hook failed to install earlier. Check logs from StoreSwapChainPointer." << std::endl;
    } else {
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Waiting for D3D11CreateDeviceAndSwapChain detour to provide a SwapChain pointer");
        std::cout << "[DirectXHookManager::Initialize] Waiting for D3D11CreateDeviceAndSwapChain detour to provide a SwapChain pointer..." << std::endl;
    }
}

void DirectXHookManager::StoreSwapChainPointer(IDXGISwapChain* pSwapChain) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::StoreSwapChainPointer");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("DirectXHookManager::StoreSwapChainPointer");
    
    ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "StoreSwapChainPointer called with pSwapChain: " + std::to_string(reinterpret_cast<uintptr_t>(pSwapChain)));
    std::cout << "[DirectXHookManager::StoreSwapChainPointer] Called with pSwapChain: " << pSwapChain << std::endl;

    if (!pSwapChain) {
        ErrorHandler::GetInstance().LogError("DirectXHookManager", "Received null SwapChain pointer", 
            ErrorSeverity::ERROR, ErrorCategory::INVALID_PARAMETER);
        std::cerr << "[DirectXHookManager::StoreSwapChainPointer] Received null SwapChain pointer." << std::endl;
        return;
    }

    if (activeSwapChain_.Get() == pSwapChain && swapChainHook_ && swapChainHook_->IsInstalled()) {
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Same SwapChain instance received, Present hook already installed");
        std::cout << "[DirectXHookManager::StoreSwapChainPointer] Same SwapChain instance received, Present hook already installed." << std::endl;
        presentHookInstalled_ = true; // Ensure flag is correct
        return;
    }

    // If there's an existing (different) swap chain hook, uninstall and release it.
    if (swapChainHook_ && swapChainHook_->IsInstalled()) {
        auto uninstallTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::UninstallOldHook");
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Uninstalling hook from old SwapChain: " + std::to_string(reinterpret_cast<uintptr_t>(activeSwapChain_.Get())));
        std::cout << "[DirectXHookManager::StoreSwapChainPointer] Uninstalling hook from old SwapChain: " << activeSwapChain_.Get() << std::endl;
        swapChainHook_->Uninstall();
        presentHookInstalled_ = false;
    }
    swapChainHook_.reset(); // Important to reset before releasing activeSwapChain_ if it's the same object
                            // that pSwapChain might point to after a Release/AddRef cycle elsewhere.

    // Clear the previous swap chain (RAII wrapper automatically releases it)
    if (activeSwapChain_) {
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Releasing previously stored SwapChain: " + std::to_string(reinterpret_cast<uintptr_t>(activeSwapChain_.Get())));
        std::cout << "[DirectXHookManager::StoreSwapChainPointer] Releasing previously stored SwapChain: " << activeSwapChain_.Get() << std::endl;
        activeSwapChain_.Release();
    }

    // Store the new swap chain using RAII wrapper
    auto storeTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::StoreNewSwapChain");
    activeSwapChain_.Reset(pSwapChain, true);
    activeSwapChain_->AddRef(); // AddRef since we're taking ownership
    ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Stored new SwapChain: " + std::to_string(reinterpret_cast<uintptr_t>(activeSwapChain_.Get())) + ". Ref count should be at least 2 (one from app, one from us)");
    std::cout << "[DirectXHookManager::StoreSwapChainPointer] Stored new SwapChain: " << activeSwapChain_.Get()
              << ". Ref count should be at least 2 (one from app, one from us)." << std::endl;

    // Create and install the hook for the new swap chain's Present method
    try {
        auto hookCreationTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::CreateSwapChainHook");
        swapChainHook_ = std::make_unique<SwapChainHook>(activeSwapChain_.Get());
        
        if (swapChainHook_->Install()) {
            ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "SwapChainHook for Present() installed successfully on new SwapChain");
            std::cout << "[DirectXHookManager::StoreSwapChainPointer] SwapChainHook for Present() installed successfully on new SwapChain." << std::endl;
            presentHookInstalled_ = true;
        } else {
            ErrorHandler::GetInstance().LogError("DirectXHookManager", "Failed to install SwapChainHook on new SwapChain", 
                ErrorSeverity::ERROR, ErrorCategory::HOOK);
            std::cerr << "[DirectXHookManager::StoreSwapChainPointer] Failed to install SwapChainHook on new SwapChain." << std::endl;
            // Release the swap chain using RAII wrapper
            activeSwapChain_.Release();
            swapChainHook_.reset();
            presentHookInstalled_ = false;
        }
    } catch (const std::exception& e) {
        ErrorHandler::GetInstance().LogError("DirectXHookManager", "Exception during SwapChainHook creation/installation: " + std::string(e.what()), 
            ErrorSeverity::ERROR, ErrorCategory::EXCEPTION);
        std::cerr << "[DirectXHookManager::StoreSwapChainPointer] Exception during SwapChainHook creation/installation: " << e.what() << std::endl;
        if (activeSwapChain_) { // activeSwapChain_ would have been set before the try block
             // Release the swap chain using RAII wrapper
             activeSwapChain_.Release();
        }
        swapChainHook_.reset();
        presentHookInstalled_ = false;
    }
}

void DirectXHookManager::Shutdown() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::Shutdown");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("DirectXHookManager::Shutdown");
    
    ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Shutting down DirectX hook manager");
    std::cout << "[DirectXHookManager::Shutdown] Shutting down..." << std::endl;

    if (swapChainHook_) {
        if (swapChainHook_->IsInstalled()) {
            auto uninstallTimer = PerformanceMonitor::GetInstance().StartTimer("DirectXHookManager::UninstallHook");
            if (swapChainHook_->Uninstall()) {
                ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "SwapChainHook uninstalled successfully");
                std::cout << "[DirectXHookManager::Shutdown] SwapChainHook uninstalled successfully." << std::endl;
            } else {
                ErrorHandler::GetInstance().LogError("DirectXHookManager", "Failed to uninstall SwapChainHook", 
                    ErrorSeverity::WARNING, ErrorCategory::HOOK);
                std::cerr << "[DirectXHookManager::Shutdown] Failed to uninstall SwapChainHook." << std::endl;
            }
        }
        swapChainHook_.reset();
    }

    if (activeSwapChain_) {
        ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Releasing stored SwapChain: " + std::to_string(reinterpret_cast<uintptr_t>(activeSwapChain_.Get())));
        std::cout << "[DirectXHookManager::Shutdown] Releasing stored SwapChain: " << activeSwapChain_.Get() << std::endl;
        // Release the swap chain using RAII wrapper
        activeSwapChain_.Release();
    }

    dependenciesChecked_ = false;
    presentHookInstalled_ = false;
    ErrorHandler::GetInstance().LogInfo("DirectXHookManager", "Shutdown complete");
    std::cout << "[DirectXHookManager::Shutdown] Shutdown complete." << std::endl;
}
