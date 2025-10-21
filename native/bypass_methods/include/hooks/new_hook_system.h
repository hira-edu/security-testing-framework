#pragma once

#include "hook_base.h"
#include <windows.h>
#include <string>
#include <vector>
#include <memory>
#include <iostream>
#include <Psapi.h>
#include <d3d11.h> // For D3D11CreateDeviceAndSwapChain signature
#include <dxgi.h>  // For IDXGISwapChain

// --- Specific Hook Class Declarations ---

// GetForegroundWindow Hook
class GetForegroundWindowHook : public Hook {
public:
    GetForegroundWindowHook();
    typedef HWND (WINAPI *OriginalFnType)();
    static HWND WINAPI DetourGetForegroundWindow();
};

// SetForegroundWindow Hook
class SetForegroundWindowHook : public Hook {
public:
    SetForegroundWindowHook();
    typedef BOOL (WINAPI *OriginalFnType)(HWND);
    static BOOL WINAPI DetourSetForegroundWindow(HWND hWnd);
};

// SetWindowPos Hook
class SetWindowPosHook : public Hook {
public:
    SetWindowPosHook();
    typedef BOOL (WINAPI *OriginalFnType)(HWND, HWND, int, int, int, int, UINT);
    static BOOL WINAPI DetourSetWindowPos(HWND hWnd, HWND hWndInsertAfter, int X, int Y, int cx, int cy, UINT uFlags);
    struct CallParams {
        HWND hWnd = NULL; HWND hWndInsertAfter = NULL; int X = 0; int Y = 0; int cx = 0; int cy = 0; UINT uFlags = 0;
        bool hasBeenCalled = false;
    };
    static CallParams lastLegitimateCallParams_;
};

// ShowWindow Hook
class ShowWindowHook : public Hook {
public:
    ShowWindowHook();
    typedef BOOL (WINAPI *OriginalFnType)(HWND, int);
    static BOOL WINAPI DetourShowWindow(HWND hWnd, int nCmdShow);
};

// CreateProcessW Hook
class CreateProcessWHook : public Hook {
public:
    CreateProcessWHook();
    typedef BOOL (WINAPI *OriginalFnType)(
        LPCWSTR, LPWSTR, LPSECURITY_ATTRIBUTES, LPSECURITY_ATTRIBUTES,
        BOOL, DWORD, LPVOID, LPCWSTR, LPSTARTUPINFOW, LPPROCESS_INFORMATION
    );
    static BOOL WINAPI DetourCreateProcessW(
        LPCWSTR lpApplicationName, LPWSTR lpCommandLine,
        LPSECURITY_ATTRIBUTES lpProcessAttributes, LPSECURITY_ATTRIBUTES lpThreadAttributes,
        BOOL bInheritHandles, DWORD dwCreationFlags,
        LPVOID lpEnvironment, LPCWSTR lpCurrentDirectory,
        LPSTARTUPINFOW lpStartupInfo, LPPROCESS_INFORMATION lpProcessInformation
    );
};

// TerminateProcess Hook
class TerminateProcessHook : public Hook {
public:
    TerminateProcessHook();
    typedef BOOL(WINAPI* OriginalFnType)(HANDLE, UINT);
    static BOOL WINAPI DetourTerminateProcess(HANDLE hProcess, UINT uExitCode);
};

// OpenProcess Hook
class OpenProcessHook : public Hook {
public:
    OpenProcessHook();
    typedef HANDLE (WINAPI *OriginalFnType)(DWORD, BOOL, DWORD);
    static HANDLE WINAPI DetourOpenProcess(DWORD dwDesiredAccess, BOOL bInheritHandle, DWORD dwProcessId);
};

// SetClipboardData Hook
class SetClipboardDataHook : public Hook {
public:
    SetClipboardDataHook();
    typedef HANDLE(WINAPI* OriginalFnType)(UINT, HANDLE);
    static HANDLE WINAPI DetourSetClipboardData(UINT uFormat, HANDLE hMem);
};

// GetClipboardData Hook
class GetClipboardDataHook : public Hook {
public:
    GetClipboardDataHook();
    typedef HANDLE (WINAPI *OriginalFnType)(UINT);
    static HANDLE WINAPI DetourGetClipboardData(UINT uFormat);
};

// EmptyClipboard Hook
class EmptyClipboardHook : public Hook {
public:
    EmptyClipboardHook();
    typedef BOOL(WINAPI* OriginalFnType)();
    static BOOL WINAPI DetourEmptyClipboard();
};

// BringWindowToTop Hook
class BringWindowToTopHook : public Hook {
public:
    BringWindowToTopHook();
    typedef BOOL (WINAPI* OriginalFnType)(HWND);
    static BOOL WINAPI DetourBringWindowToTop(HWND hWnd);
    static HWND lastHwndCalled_;
};

// SetFocus Hook
class SetFocusHook : public Hook {
public:
    SetFocusHook();
    typedef HWND (WINAPI* OriginalFnType)(HWND);
    static HWND WINAPI DetourSetFocus(HWND hWnd);
    static HWND lastHwndCalled_;
};

// D3D11CreateDeviceAndSwapChain Hook (NEW for this task)
class D3D11CreateDeviceAndSwapChainHook : public Hook {
public:
    D3D11CreateDeviceAndSwapChainHook();
    typedef HRESULT (WINAPI *OriginalFnType)(
        IDXGIAdapter*, D3D_DRIVER_TYPE, HMODULE, UINT,
        const D3D_FEATURE_LEVEL*, UINT, UINT,
        const DXGI_SWAP_CHAIN_DESC*, IDXGISwapChain**, ID3D11Device**,
        D3D_FEATURE_LEVEL*, ID3D11DeviceContext**
    );
    static HRESULT WINAPI DetourD3D11CreateDeviceAndSwapChain(
        IDXGIAdapter* pAdapter,
        D3D_DRIVER_TYPE DriverType,
        HMODULE Software,
        UINT Flags,
        const D3D_FEATURE_LEVEL* pFeatureLevels,
        UINT FeatureLevels,
        UINT SDKVersion,
        const DXGI_SWAP_CHAIN_DESC* pSwapChainDesc,
        IDXGISwapChain** ppSwapChain,
        ID3D11Device** ppDevice,
        D3D_FEATURE_LEVEL* pFeatureLevel,
        ID3D11DeviceContext** ppImmediateContext
    );
};


// --- Windows API Hook Manager ---
class WindowsApiHookManager {
public:
    static WindowsApiHookManager& GetInstance();

    WindowsApiHookManager(const WindowsApiHookManager&) = delete;
    WindowsApiHookManager& operator=(const WindowsApiHookManager&) = delete;

    void InitializeAndInstallHooks();
    void InstallGeneralHooks();
    void UninstallGeneralHooks();
    void InstallWindowManagementHooks();
    void UninstallWindowManagementHooks();
    void UninstallAllHooks();

    HWND FindMainWindowOfCurrentProcess() const;

    template<typename T>
    T* GetHook() const {
        for (const auto& hook_ptr : all_hooks_) {
            T* specific_hook = dynamic_cast<T*>(hook_ptr.get());
            if (specific_hook) {
                return specific_hook;
            }
        }
        return nullptr;
    }

    static HWND g_focusHWND;
    static HWND g_bringWindowToTopHWND;
    static SetWindowPosHook::CallParams g_setWindowPosParams;


private:
    WindowsApiHookManager();
    ~WindowsApiHookManager();

    void RegisterHooks();

    std::vector<std::unique_ptr<Hook>> all_hooks_;
    bool general_hooks_installed_ = false;
    bool window_management_hooks_installed_ = false;

    static BOOL CALLBACK EnumWindowsCallbackHelper(HWND handle, LPARAM lParam);
    static BOOL IsMainWindowHelper(HWND handle);
};
