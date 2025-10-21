#include "../../../include/hooks/new_hook_system.h"
#include "../../../include/hooks/dx_hook_core.h" // For DirectXHookManager to store the swapchain

#include <iostream>
#include <windows.h>
#include <vector>
#include <memory>
#include <algorithm>

// --- Static member definitions for hook classes ---
SetWindowPosHook::CallParams SetWindowPosHook::lastLegitimateCallParams_;
HWND BringWindowToTopHook::lastHwndCalled_ = NULL;
HWND SetFocusHook::lastHwndCalled_ = NULL;

// Definitions for static "global-like" state variables in WindowsApiHookManager
HWND WindowsApiHookManager::g_focusHWND = NULL;
HWND WindowsApiHookManager::g_bringWindowToTopHWND = NULL;
SetWindowPosHook::CallParams WindowsApiHookManager::g_setWindowPosParams;


// --- WindowsApiHookManager Method Implementations ---

WindowsApiHookManager& WindowsApiHookManager::GetInstance() {
    static WindowsApiHookManager instance;
    return instance;
}

WindowsApiHookManager::WindowsApiHookManager()
    : general_hooks_installed_(false), window_management_hooks_installed_(false) {
    std::cout << "WindowsApiHookManager: Constructor." << std::endl;
}

WindowsApiHookManager::~WindowsApiHookManager() {
    std::cout << "WindowsApiHookManager: Destructor." << std::endl;
    UninstallAllHooks();
}

void WindowsApiHookManager::RegisterHooks() {
    std::cout << "WindowsApiHookManager: Registering hooks..." << std::endl;
    if (!all_hooks_.empty()) {
        std::cout << "WindowsApiHookManager: Hooks already registered." << std::endl;
        return;
    }

    // Window Management Hooks
    all_hooks_.push_back(std::make_unique<GetForegroundWindowHook>());
    all_hooks_.push_back(std::make_unique<SetForegroundWindowHook>());
    all_hooks_.push_back(std::make_unique<SetWindowPosHook>());
    all_hooks_.push_back(std::make_unique<ShowWindowHook>());
    all_hooks_.push_back(std::make_unique<BringWindowToTopHook>());
    all_hooks_.push_back(std::make_unique<SetFocusHook>());

    // General / Process / Clipboard / DirectX Creation Hooks
    all_hooks_.push_back(std::make_unique<CreateProcessWHook>());
    all_hooks_.push_back(std::make_unique<TerminateProcessHook>());
    all_hooks_.push_back(std::make_unique<OpenProcessHook>());
    all_hooks_.push_back(std::make_unique<EmptyClipboardHook>());
    all_hooks_.push_back(std::make_unique<SetClipboardDataHook>());
    all_hooks_.push_back(std::make_unique<GetClipboardDataHook>());
    all_hooks_.push_back(std::make_unique<D3D11CreateDeviceAndSwapChainHook>()); // Added this hook

    std::cout << "WindowsApiHookManager: " << all_hooks_.size() << " hooks registered." << std::endl;
}

void WindowsApiHookManager::InitializeAndInstallHooks() {
    std::cout << "WindowsApiHookManager: Initializing and installing all hooks..." << std::endl;
    if (all_hooks_.empty()) {
        RegisterHooks();
    }

    for (const auto& hook : all_hooks_) {
        if (hook) {
            hook->Install();
        }
    }
    general_hooks_installed_ = true;
    window_management_hooks_installed_ = true;
    std::cout << "WindowsApiHookManager: All registered hooks processed for installation." << std::endl;
}

void WindowsApiHookManager::InstallGeneralHooks() {
    std::cout << "WindowsApiHookManager: Installing general hooks..." << std::endl;
    if (all_hooks_.empty()) RegisterHooks();
    if (general_hooks_installed_) {
        std::cout << "WindowsApiHookManager: General hooks already installed." << std::endl;
        return;
    }
    for (const auto& hook : all_hooks_) {
        if (dynamic_cast<CreateProcessWHook*>(hook.get()) ||
            dynamic_cast<TerminateProcessHook*>(hook.get()) ||
            dynamic_cast<OpenProcessHook*>(hook.get()) ||
            dynamic_cast<EmptyClipboardHook*>(hook.get()) ||
            dynamic_cast<SetClipboardDataHook*>(hook.get()) ||
            dynamic_cast<GetClipboardDataHook*>(hook.get()) ||
            dynamic_cast<D3D11CreateDeviceAndSwapChainHook*>(hook.get())) { // Added this hook
            hook->Install();
        }
    }
    general_hooks_installed_ = true;
}

void WindowsApiHookManager::InstallWindowManagementHooks() {
    std::cout << "WindowsApiHookManager: Installing window management hooks..." << std::endl;
    if (all_hooks_.empty()) RegisterHooks();
    if (window_management_hooks_installed_) {
        std::cout << "WindowsApiHookManager: Window management hooks already installed." << std::endl;
        return;
    }
    for (const auto& hook : all_hooks_) {
        if (dynamic_cast<GetForegroundWindowHook*>(hook.get()) ||
            dynamic_cast<SetForegroundWindowHook*>(hook.get()) ||
            dynamic_cast<SetWindowPosHook*>(hook.get()) ||
            dynamic_cast<ShowWindowHook*>(hook.get()) ||
            dynamic_cast<BringWindowToTopHook*>(hook.get()) ||
            dynamic_cast<SetFocusHook*>(hook.get())) {
            hook->Install();
        }
    }
    window_management_hooks_installed_ = true;
}

void WindowsApiHookManager::UninstallGeneralHooks() {
    std::cout << "WindowsApiHookManager: Uninstalling general hooks..." << std::endl;
    if (!general_hooks_installed_) {
        std::cout << "WindowsApiHookManager: General hooks not installed." << std::endl;
        return;
    }
    for (const auto& hook : all_hooks_) {
        if (dynamic_cast<CreateProcessWHook*>(hook.get()) ||
            dynamic_cast<TerminateProcessHook*>(hook.get()) ||
            dynamic_cast<OpenProcessHook*>(hook.get()) ||
            dynamic_cast<EmptyClipboardHook*>(hook.get()) ||
            dynamic_cast<SetClipboardDataHook*>(hook.get()) ||
            dynamic_cast<GetClipboardDataHook*>(hook.get()) ||
            dynamic_cast<D3D11CreateDeviceAndSwapChainHook*>(hook.get())) { // Added this hook
            if (hook->IsInstalled()) hook->Uninstall();
        }
    }
    general_hooks_installed_ = false;
}

void WindowsApiHookManager::UninstallWindowManagementHooks() {
    std::cout << "WindowsApiHookManager: Uninstalling window management hooks..." << std::endl;
    if (!window_management_hooks_installed_) {
        std::cout << "WindowsApiHookManager: Window management hooks not installed." << std::endl;
        return;
    }
    for (const auto& hook : all_hooks_) {
        if (dynamic_cast<GetForegroundWindowHook*>(hook.get()) ||
            dynamic_cast<SetForegroundWindowHook*>(hook.get()) ||
            dynamic_cast<SetWindowPosHook*>(hook.get()) ||
            dynamic_cast<ShowWindowHook*>(hook.get()) ||
            dynamic_cast<BringWindowToTopHook*>(hook.get()) ||
            dynamic_cast<SetFocusHook*>(hook.get())) {
            if (hook->IsInstalled()) hook->Uninstall();
        }
    }
    window_management_hooks_installed_ = false;
}

void WindowsApiHookManager::UninstallAllHooks() {
    std::cout << "WindowsApiHookManager: Uninstalling all hooks..." << std::endl;
    for (const auto& hook : all_hooks_) {
        if (hook && hook->IsInstalled()) {
            hook->Uninstall();
        }
    }
    general_hooks_installed_ = false;
    window_management_hooks_installed_ = false;
    std::cout << "WindowsApiHookManager: All hooks processed for uninstallation." << std::endl;
}

BOOL WindowsApiHookManager::IsMainWindowHelper(HWND handle) {
    return GetWindow(handle, GW_OWNER) == (HWND)0 && IsWindowVisible(handle);
}

BOOL CALLBACK WindowsApiHookManager::EnumWindowsCallbackHelper(HWND handle, LPARAM lParam) {
    DWORD processID = 0;
    GetWindowThreadProcessId(handle, &processID);
    if (GetCurrentProcessId() == processID && IsMainWindowHelper(handle)) {
        *reinterpret_cast<HWND*>(lParam) = handle;
        return FALSE;
    }
    return TRUE;
}

HWND WindowsApiHookManager::FindMainWindowOfCurrentProcess() const {
    HWND mainWindow = NULL;
    EnumWindows(EnumWindowsCallbackHelper, reinterpret_cast<LPARAM>(&mainWindow));
    return mainWindow;
}

// --- Specific Hook Class Constructor Implementations ---
GetForegroundWindowHook::GetForegroundWindowHook()
    : Hook("user32.dll", "GetForegroundWindow", (void*)DetourGetForegroundWindow) {}

SetForegroundWindowHook::SetForegroundWindowHook()
    : Hook("user32.dll", "SetForegroundWindow", (void*)DetourSetForegroundWindow) {}

SetWindowPosHook::SetWindowPosHook()
    : Hook("user32.dll", "SetWindowPos", (void*)DetourSetWindowPos) {}

ShowWindowHook::ShowWindowHook()
    : Hook("user32.dll", "ShowWindow", (void*)DetourShowWindow) {}

CreateProcessWHook::CreateProcessWHook()
    : Hook("kernel32.dll", "CreateProcessW", (void*)DetourCreateProcessW) {}

TerminateProcessHook::TerminateProcessHook()
    : Hook("kernel32.dll", "TerminateProcess", (void*)DetourTerminateProcess) {}

OpenProcessHook::OpenProcessHook()
    : Hook("kernel32.dll", "OpenProcess", (void*)DetourOpenProcess) {}

SetClipboardDataHook::SetClipboardDataHook()
    : Hook("user32.dll", "SetClipboardData", (void*)DetourSetClipboardData) {}

GetClipboardDataHook::GetClipboardDataHook()
    : Hook("user32.dll", "GetClipboardData", (void*)DetourGetClipboardData) {}

EmptyClipboardHook::EmptyClipboardHook()
    : Hook("user32.dll", "EmptyClipboard", (void*)DetourEmptyClipboard) {}

BringWindowToTopHook::BringWindowToTopHook()
    : Hook("user32.dll", "BringWindowToTop", (void*)DetourBringWindowToTop) {}

SetFocusHook::SetFocusHook()
    : Hook("user32.dll", "SetFocus", (void*)DetourSetFocus) {}

D3D11CreateDeviceAndSwapChainHook::D3D11CreateDeviceAndSwapChainHook() // Added
    : Hook("d3d11.dll", "D3D11CreateDeviceAndSwapChain", (void*)DetourD3D11CreateDeviceAndSwapChain) {}


// --- Static Detour Function Implementations ---
#define GET_ORIGINAL_FUNC(HookClass, FunctionType) \
    auto* hook = WindowsApiHookManager::GetInstance().GetHook<HookClass>(); \
    if (hook && hook->IsInstalled()) { \
        /*std::cout << "[Detour] Getting trampoline for " #HookClass << std::endl;*/ \
        return hook->GetOriginalFunctionTrampoline<FunctionType>(); \
    } \
    std::cerr << "[Detour] Failed to get hook or trampoline for " #HookClass << std::endl; \
    return nullptr;


HWND WINAPI GetForegroundWindowHook::DetourGetForegroundWindow() {
    std::cout << "[Detour] GetForegroundWindow called." << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(GetForegroundWindowHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original GetForegroundWindow..." << std::endl;
        return originalFunc();
    }
    std::cout << "  Original GetForegroundWindow not callable." << std::endl;
    return NULL;
}

BOOL WINAPI SetForegroundWindowHook::DetourSetForegroundWindow(HWND hWnd) {
    std::cout << "[Detour] SetForegroundWindow called for HWND: " << hWnd << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(SetForegroundWindowHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original SetForegroundWindow..." << std::endl;
        return originalFunc(hWnd);
    }
    std::cout << "  Original SetForegroundWindow not callable." << std::endl;
    return FALSE;
}

BOOL WINAPI SetWindowPosHook::DetourSetWindowPos(HWND hWnd, HWND hWndInsertAfter, int X, int Y, int cx, int cy, UINT uFlags) {
    std::cout << "[Detour] SetWindowPos called for HWND: " << hWnd << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(SetWindowPosHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original SetWindowPos..." << std::endl;
        return originalFunc(hWnd, hWndInsertAfter, X, Y, cx, cy, uFlags);
    }
    std::cout << "  Original SetWindowPos not callable." << std::endl;
    return FALSE;
}

BOOL WINAPI ShowWindowHook::DetourShowWindow(HWND hWnd, int nCmdShow) {
    std::cout << "[Detour] ShowWindow called for HWND: " << hWnd << " with nCmdShow: " << nCmdShow << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(ShowWindowHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original ShowWindow..." << std::endl;
        return originalFunc(hWnd, nCmdShow);
    }
    std::cout << "  Original ShowWindow not callable." << std::endl;
    return FALSE;
}

BOOL WINAPI CreateProcessWHook::DetourCreateProcessW(
    LPCWSTR lpApplicationName, LPWSTR lpCommandLine,
    LPSECURITY_ATTRIBUTES lpProcessAttributes, LPSECURITY_ATTRIBUTES lpThreadAttributes,
    BOOL bInheritHandles, DWORD dwCreationFlags,
    LPVOID lpEnvironment, LPCWSTR lpCurrentDirectory,
    LPSTARTUPINFOW lpStartupInfo, LPPROCESS_INFORMATION lpProcessInformation) {
    std::cout << "[Detour] CreateProcessW called for: " << (lpApplicationName ? lpApplicationName : L"N/A") << " Cmd: " << (lpCommandLine ? lpCommandLine : L"N/A") << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(CreateProcessWHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original CreateProcessW..." << std::endl;
        return originalFunc(lpApplicationName, lpCommandLine, lpProcessAttributes, lpThreadAttributes, bInheritHandles, dwCreationFlags, lpEnvironment, lpCurrentDirectory, lpStartupInfo, lpProcessInformation);
    }
    std::cout << "  Original CreateProcessW not callable." << std::endl;
    if (lpProcessInformation) ZeroMemory(lpProcessInformation, sizeof(PROCESS_INFORMATION));
    SetLastError(ERROR_FUNCTION_FAILED);
    return FALSE;
}

BOOL WINAPI TerminateProcessHook::DetourTerminateProcess(HANDLE hProcess, UINT uExitCode) {
    std::cout << "[Detour] TerminateProcess called for Process: " << hProcess << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(TerminateProcessHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original TerminateProcess..." << std::endl;
        return originalFunc(hProcess, uExitCode);
    }
    std::cout << "  Original TerminateProcess not callable." << std::endl;
    return FALSE;
}

HANDLE WINAPI OpenProcessHook::DetourOpenProcess(DWORD dwDesiredAccess, BOOL bInheritHandle, DWORD dwProcessId) {
    std::cout << "[Detour] OpenProcess called for PID: " << dwProcessId << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(OpenProcessHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original OpenProcess..." << std::endl;
        return originalFunc(dwDesiredAccess, bInheritHandle, dwProcessId);
    }
    std::cout << "  Original OpenProcess not callable." << std::endl;
    return NULL;
}

HANDLE WINAPI SetClipboardDataHook::DetourSetClipboardData(UINT uFormat, HANDLE hMem) {
    std::cout << "[Detour] SetClipboardData called." << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(SetClipboardDataHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original SetClipboardData..." << std::endl;
        return originalFunc(uFormat, hMem);
    }
    std::cout << "  Original SetClipboardData not callable." << std::endl;
    return NULL;
}

HANDLE WINAPI GetClipboardDataHook::DetourGetClipboardData(UINT uFormat) {
    std::cout << "[Detour] GetClipboardData called for format: " << uFormat << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(GetClipboardDataHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original GetClipboardData..." << std::endl;
        return originalFunc(uFormat);
    }
    std::cout << "  Original GetClipboardData not callable." << std::endl;
    return NULL;
}

BOOL WINAPI EmptyClipboardHook::DetourEmptyClipboard() {
    std::cout << "[Detour] EmptyClipboard called." << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(EmptyClipboardHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original EmptyClipboard..." << std::endl;
        return originalFunc();
    }
    std::cout << "  Original EmptyClipboard not callable." << std::endl;
    return FALSE;
}

BOOL WINAPI BringWindowToTopHook::DetourBringWindowToTop(HWND hWnd) {
    std::cout << "[Detour] BringWindowToTop called for HWND: " << hWnd << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(BringWindowToTopHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original BringWindowToTop..." << std::endl;
        return originalFunc(hWnd);
    }
    std::cout << "  Original BringWindowToTop not callable." << std::endl;
    return FALSE;
}

HWND WINAPI SetFocusHook::DetourSetFocus(HWND hWnd) {
    std::cout << "[Detour] SetFocus called for HWND: " << hWnd << std::endl;
    auto originalFunc = GET_ORIGINAL_FUNC(SetFocusHook, OriginalFnType);
    if (originalFunc) {
        std::cout << "  Calling original SetFocus..." << std::endl;
        return originalFunc(hWnd);
    }
    std::cout << "  Original SetFocus not callable." << std::endl;
    return NULL;
}

// Detour for D3D11CreateDeviceAndSwapChain
HRESULT WINAPI D3D11CreateDeviceAndSwapChainHook::DetourD3D11CreateDeviceAndSwapChain(
    IDXGIAdapter* pAdapter,
    D3D_DRIVER_TYPE DriverType,
    HMODULE Software,
    UINT Flags,
    const D3D_FEATURE_LEVEL* pFeatureLevels,
    UINT FeatureLevels,
    UINT SDKVersion,
    const DXGI_SWAP_CHAIN_DESC* pSwapChainDesc,
    IDXGISwapChain** ppSwapChain, // Output parameter for the SwapChain
    ID3D11Device** ppDevice,
    D3D_FEATURE_LEVEL* pFeatureLevel,
    ID3D11DeviceContext** ppImmediateContext) {

    std::cout << "[Detour] D3D11CreateDeviceAndSwapChain called." << std::endl;

    auto originalFunc = GET_ORIGINAL_FUNC(D3D11CreateDeviceAndSwapChainHook, OriginalFnType);
    if (!originalFunc) {
        std::cerr << "  Original D3D11CreateDeviceAndSwapChain not callable. Cannot proceed." << std::endl;
        // Set output parameters to null or error state if possible
        if (ppSwapChain) *ppSwapChain = nullptr;
        if (ppDevice) *ppDevice = nullptr;
        if (ppImmediateContext) *ppImmediateContext = nullptr;
        // What error code to return? E_FAIL is generic.
        return E_FAIL;
    }

    std::cout << "  Calling original D3D11CreateDeviceAndSwapChain..." << std::endl;
    HRESULT hr = originalFunc(
        pAdapter, DriverType, Software, Flags, pFeatureLevels, FeatureLevels, SDKVersion,
        pSwapChainDesc, ppSwapChain, ppDevice, pFeatureLevel, ppImmediateContext
    );

    std::cout << "  Original D3D11CreateDeviceAndSwapChain returned: " << std::hex << hr << std::dec << std::endl;

    if (SUCCEEDED(hr) && ppSwapChain && *ppSwapChain) {
        IDXGISwapChain* capturedSwapChain = *ppSwapChain;
        std::cout << "  Successfully captured IDXGISwapChain: " << capturedSwapChain << std::endl;
        // Pass the captured swap chain to DirectXHookManager
        DirectXHookManager::GetInstance().StoreSwapChainPointer(capturedSwapChain);
    } else {
        std::cout << "  Failed to create device/swapchain or ppSwapChain is null." << std::endl;
    }

    return hr;
}
