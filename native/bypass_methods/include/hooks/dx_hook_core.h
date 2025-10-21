#pragma once

#include "dx_common.h"
#include "swap_chain_hook.h"
#include "com_interface_wrapper.h"

#include <memory>

class DirectXHookManager {
public:
    static DirectXHookManager& GetInstance();

    DirectXHookManager(const DirectXHookManager&) = delete;
    DirectXHookManager& operator=(const DirectXHookManager&) = delete;

    // Initializes DirectX hook prerequisites (e.g., ensures D3D11CreateDeviceAndSwapChain hook is set by WindowsApiHookManager)
    // The actual SwapChainHook is installed when StoreSwapChainPointer is called.
    void Initialize();

    // Shuts down and uninstalls all DirectX hooks (specifically the SwapChainHook)
    // and releases captured resources.
    void Shutdown();

    // Called by the D3D11CreateDeviceAndSwapChain detour to provide the swap chain.
    // This method will then manage the SwapChainHook lifecycle.
    void StoreSwapChainPointer(IDXGISwapChain* pSwapChain);

private:
    DirectXHookManager();
    ~DirectXHookManager();

    std::unique_ptr<SwapChainHook> swapChainHook_; // Hook for IDXGISwapChain::Present
    DXGISwapChainWrapper activeSwapChain_;         // The currently hooked IDXGISwapChain instance with RAII

    bool dependenciesChecked_; // Flag to ensure DLLs are checked once
    bool presentHookInstalled_; // Flag to track if Present hook is active on activeSwapChain_
};
