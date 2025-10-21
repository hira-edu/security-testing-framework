#pragma once

#include "dx_common.h" // Includes hook_base.h, trampoline_utils.h, d3d11.h, dxgi.h

// Define PRESENT_VTABLE_INDEX for IDXGISwapChain
// For IDXGISwapChain, Present is the 8th function. (0-indexed)
// For IDXGISwapChain1/2/3/4, it might be different or inherited.
// We will target IDXGISwapChain::Present.
const int IDXGISWAPCHAIN_PRESENT_VTABLE_INDEX = 8;

class SwapChainHook {
public:
    SwapChainHook(IDXGISwapChain* swapChainInstance);
    ~SwapChainHook();

    bool Install();
    bool Uninstall();

    bool IsInstalled() const { return isInstalled_; }

    // Typedef for the original Present function signature
    typedef HRESULT (WINAPI *OriginalPresentFn)(IDXGISwapChain* pSwapChain, UINT SyncInterval, UINT Flags);

    // Static detour function that will be called instead of the original Present
    static HRESULT WINAPI DetourPresent(IDXGISwapChain* pSwapChain, UINT SyncInterval, UINT Flags);

    // Allows the detour to call the original Present function via the trampoline
    OriginalPresentFn GetOriginalPresent() const;

private:
    IDXGISwapChain* swapChainInstance_; // The specific swap chain instance we're hooking
    LPVOID originalPresentAddress_;     // Address of the original Present function in the vtable
    LPVOID detourPresentAddress_;       // Address of our DetourPresent function

    LPVOID trampolineFunction_;         // Address of the allocated trampoline for calling original Present
    SIZE_T prologueSize_;               // Size of the prologue copied to the trampoline
    PBYTE copiedPrologueBytes_;         // Buffer holding the copied prologue bytes

    PBYTE originalVTableEntryBytes_;    // Buffer holding the original content of the vtable entry (the original Present_ptr)
                                        // This is what WriteAbsoluteJump overwrites in the vtable itself.
                                        // For vtable hooking, we usually overwrite a pointer. So this is 4 or 8 bytes.

    bool isInstalled_;

    // Store a static pointer to the current hook instance to be accessible from the static detour.
    // This is a simplification assuming only one SwapChain is hooked at a time by this class.
    // A more robust solution for multiple instances would use a map or TLS.
    static SwapChainHook* currentInstance_;
};
