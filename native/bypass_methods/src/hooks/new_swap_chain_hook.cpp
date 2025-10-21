#include "../../include/hooks/swap_chain_hook.h" // The new header we created
#include <iostream> // For std::cout, std::cerr

// Initialize static member
SwapChainHook* SwapChainHook::currentInstance_ = nullptr;

// Helper to get the VTable address for the instance
inline void** GetVTable(IDXGISwapChain* instance) {
    if (!instance) return nullptr;
    return *reinterpret_cast<void***>(instance);
}

SwapChainHook::SwapChainHook(IDXGISwapChain* swapChainInstance)
    : swapChainInstance_(swapChainInstance),
      originalPresentAddress_(nullptr),
      detourPresentAddress_((void*)DetourPresent), // Address of our static detour
      trampolineFunction_(nullptr),
      prologueSize_(0),
      copiedPrologueBytes_(nullptr),
      originalVTableEntryBytes_(nullptr), // Will store the original pointer from the vtable entry
      isInstalled_(false) {

    if (!swapChainInstance_) {
        std::cerr << "[SwapChainHook] Error: swapChainInstance_ is null." << std::endl;
        throw std::invalid_argument("swapChainInstance cannot be null.");
    }

    // currentInstance_ should be managed carefully if multiple swapchains/hooks are expected.
    // For this initial implementation, a single static instance is simpler.
    if (currentInstance_ != nullptr && currentInstance_ != this) {
        // This indicates an attempt to create a second hook when the static pointer is already in use.
        // A more robust system would use a map or list of instances.
        std::cerr << "[SwapChainHook] Warning: Another SwapChainHook instance might already exist. Static currentInstance_ will be overwritten." << std::endl;
    }
    currentInstance_ = this;

    void** vtable = GetVTable(swapChainInstance_);
    if (vtable && vtable[IDXGISWAPCHAIN_PRESENT_VTABLE_INDEX]) {
        originalPresentAddress_ = vtable[IDXGISWAPCHAIN_PRESENT_VTABLE_INDEX];
        std::cout << "[SwapChainHook] Original IDXGISwapChain::Present address: " << originalPresentAddress_ << std::endl;
    } else {
        std::cerr << "[SwapChainHook] Error: Could not get vtable or Present entry from swapChainInstance_." << std::endl;
        throw std::runtime_error("Failed to get vtable or Present entry for swap chain.");
    }

    // Allocate buffer for the original VTable entry (which is a function pointer)
    originalVTableEntryBytes_ = new BYTE[sizeof(void*)];
    std::fill_n(originalVTableEntryBytes_, sizeof(void*), 0x00); // Initialize
}

SwapChainHook::~SwapChainHook() {
    if (isInstalled_) {
        Uninstall(); // This will also free trampolineFunction_ and copiedPrologueBytes_
    }
    delete[] originalVTableEntryBytes_;
    // Ensure copiedPrologueBytes_ is deleted if Uninstall wasn't called or failed early
    if (copiedPrologueBytes_){
        delete[] copiedPrologueBytes_;
        copiedPrologueBytes_ = nullptr;
    }


    if (currentInstance_ == this) {
        currentInstance_ = nullptr;
    }
}

bool SwapChainHook::Install() {
    if (isInstalled_) {
        std::cout << "[SwapChainHook::Install] Hook for Present already installed." << std::endl;
        return true;
    }
    if (!originalPresentAddress_) {
        std::cerr << "[SwapChainHook::Install] Original Present address is not set. Cannot install." << std::endl;
        return false;
    }

    // 1. Determine prologue size for the trampoline (for the *code* of the original Present function)
    //    Using a fixed size due to CalculateMinimumPrologueSize simplification.
    prologueSize_ = UndownUnlock::TrampolineUtils::CalculateMinimumPrologueSize(originalPresentAddress_, 6); // e.g., 6 bytes
    if (prologueSize_ == 0) {
         std::cerr << "[SwapChainHook::Install] Failed to calculate prologue size for Present." << std::endl;
         return false;
    }
    delete[] copiedPrologueBytes_; // Clean up if any from previous attempt
    copiedPrologueBytes_ = new BYTE[prologueSize_];
    std::fill_n(copiedPrologueBytes_, prologueSize_, 0xCC); // Init with INT3

    // 2. Allocate the trampoline for the original Present function's code.
    //    copiedPrologueBytes_ will be filled by AllocateTrampoline.
    if (!UndownUnlock::TrampolineUtils::AllocateTrampoline(originalPresentAddress_, prologueSize_, copiedPrologueBytes_, trampolineFunction_)) {
        std::cerr << "[SwapChainHook::Install] Failed to allocate trampoline for Present code." << std::endl;
        delete[] copiedPrologueBytes_;
        copiedPrologueBytes_ = nullptr;
        return false;
    }

    // 3. Overwrite the VTable entry to point to our DetourPresent.
    void** vtable = GetVTable(swapChainInstance_);
    void** vtableEntryAddress = &vtable[IDXGISWAPCHAIN_PRESENT_VTABLE_INDEX];

    DWORD oldProtect;
    if (!VirtualProtect(vtableEntryAddress, sizeof(void*), PAGE_READWRITE, &oldProtect)) {
        std::cerr << "[SwapChainHook::Install] VirtualProtect (VTable to RW) failed. Error: " << GetLastError() << std::endl;
        UndownUnlock::TrampolineUtils::FreeTrampoline(trampolineFunction_);
        trampolineFunction_ = nullptr;
        delete[] copiedPrologueBytes_;
        copiedPrologueBytes_ = nullptr;
        return false;
    }

    // Save the original pointer from the VTable entry
    memcpy(originalVTableEntryBytes_, vtableEntryAddress, sizeof(void*));

    // Write the address of our detour into the VTable entry
    memcpy(vtableEntryAddress, &detourPresentAddress_, sizeof(void*));

    if (!VirtualProtect(vtableEntryAddress, sizeof(void*), oldProtect, &oldProtect)) {
        std::cerr << "[SwapChainHook::Install] VirtualProtect (VTable to original protection) failed. Error: " << GetLastError() << std::endl;
        memcpy(vtableEntryAddress, originalVTableEntryBytes_, sizeof(void*)); // Attempt to restore

        UndownUnlock::TrampolineUtils::FreeTrampoline(trampolineFunction_);
        trampolineFunction_ = nullptr;
        delete[] copiedPrologueBytes_;
        copiedPrologueBytes_ = nullptr;
        return false;
    }

    isInstalled_ = true;
    std::cout << "[SwapChainHook::Install] IDXGISwapChain::Present hook installed. VTable entry at "
              << vtableEntryAddress << " now points to " << detourPresentAddress_
              << ". Trampoline for original Present code at " << trampolineFunction_ << std::endl;
    return true;
}

bool SwapChainHook::Uninstall() {
    if (!isInstalled_) {
        // std::cout << "[SwapChainHook::Uninstall] Hook for Present not installed or already uninstalled." << std::endl;
        return true;
    }
    // originalPresentAddress_ check is implicitly handled by isInstalled_ being true.
    // originalVTableEntryBytes_ must be valid if installed.

    // 1. Restore the original pointer in the VTable entry
    void** vtable = GetVTable(swapChainInstance_);
    void** vtableEntryAddress = &vtable[IDXGISWAPCHAIN_PRESENT_VTABLE_INDEX];

    DWORD oldProtect;
    if (!VirtualProtect(vtableEntryAddress, sizeof(void*), PAGE_READWRITE, &oldProtect)) {
        std::cerr << "[SwapChainHook::Uninstall] VirtualProtect (VTable to RW) failed. Error: " << GetLastError() << std::endl;
    } else {
        memcpy(vtableEntryAddress, originalVTableEntryBytes_, sizeof(void*)); // Restore original pointer
        if (!VirtualProtect(vtableEntryAddress, sizeof(void*), oldProtect, &oldProtect)) {
            std::cerr << "[SwapChainHook::Uninstall] VirtualProtect (VTable to original protection) failed. Error: " << GetLastError() << std::endl;
        } else {
             std::cout << "[SwapChainHook::Uninstall] Original Present pointer restored in VTable." << std::endl;
        }
    }

    // 2. Free the trampoline memory (for the original Present function's code)
    if (trampolineFunction_) {
        UndownUnlock::TrampolineUtils::FreeTrampoline(trampolineFunction_);
        trampolineFunction_ = nullptr;
    }

    delete[] copiedPrologueBytes_;
    copiedPrologueBytes_ = nullptr;

    isInstalled_ = false;
    // std::cout << "[SwapChainHook::Uninstall] Present hook uninstalled." << std::endl;
    return true;
}

SwapChainHook::OriginalPresentFn SwapChainHook::GetOriginalPresent() const {
    if (!isInstalled_ || !trampolineFunction_) {
        return nullptr;
    }
    return reinterpret_cast<OriginalPresentFn>(trampolineFunction_);
}

// Static Detour Function Implementation
HRESULT WINAPI SwapChainHook::DetourPresent(IDXGISwapChain* pSwapChain, UINT SyncInterval, UINT Flags) {
    // Use currentInstance_ to access member functions and data of the specific hook object.
    if (currentInstance_ && currentInstance_->swapChainInstance_ == pSwapChain) {
        std::cout << "[DetourPresent] Called. SwapChain: " << pSwapChain
                  << ", SyncInterval: " << SyncInterval << ", Flags: " << Flags << std::endl;

        OriginalPresentFn originalFunc = currentInstance_->GetOriginalPresent();
        if (originalFunc) {
            // Call the original Present function via the trampoline
            return originalFunc(pSwapChain, SyncInterval, Flags);
        } else {
            std::cerr << "[DetourPresent] Error: Could not get original Present function from trampoline." << std::endl;
            return DXGI_ERROR_INVALID_CALL;
        }
    } else if (currentInstance_) {
         // This means the detour is called for a pSwapChain that doesn't match our hooked instance.
         // This could happen if there are multiple swapchains and the static currentInstance_ is ambiguous.
         // For now, we try to call its own original function if we can somehow get it, but that's complex.
         // Safest is to just log and return an error or try to find the *actual* original.
         // This points to the limitation of a single static currentInstance_.
        std::cerr << "[DetourPresent] Called for an unexpected SwapChain: " << pSwapChain
                  << ", hooked instance is: " << currentInstance_->swapChainInstance_ << std::endl;

        // Attempt to find the original function pointer directly from this pSwapChain's vtable
        // This is a fallback if the currentInstance_ doesn't match.
        void** vtable = GetVTable(pSwapChain);
        if (vtable && vtable[IDXGISWAPCHAIN_PRESENT_VTABLE_INDEX]) {
            OriginalPresentFn actualOriginal = reinterpret_cast<OriginalPresentFn>(vtable[IDXGISWAPCHAIN_PRESENT_VTABLE_INDEX]);
             std::cout << "[DetourPresent] Fallback: Calling Present directly from unexpected SwapChain's VTable." << std::endl;
            return actualOriginal(pSwapChain, SyncInterval, Flags);
        }
        return DXGI_ERROR_INVALID_CALL;
    } else {
        // No currentInstance_ set, this is a critical error.
        std::cerr << "[DetourPresent] Error: currentInstance_ is null. Cannot call original." << std::endl;
        return DXGI_ERROR_INVALID_CALL;
    }
}
