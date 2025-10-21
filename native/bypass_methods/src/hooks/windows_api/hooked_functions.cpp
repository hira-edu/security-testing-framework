#include "../../../include/hooks/hooked_functions.h"
#include "../../../include/hooks/windows_api_hooks.h"
#include "../../../include/utils/raii_wrappers.h"
#include "../../../include/error_handler.h"
#include "../../../include/performance_monitor.h"
#include "../../../include/memory_tracker.h"
#include <iostream>

namespace UndownUnlock {
namespace WindowsHook {

// Implementation of hooked clipboard functions
HANDLE WINAPI HookedSetClipboardData(UINT uFormat, HANDLE hMem) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedSetClipboardData");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedSetClipboardData");
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "SetClipboardData hook called, but not setting clipboard data");
    std::cout << "SetClipboardData hook called, but not setting clipboard data." << std::endl;
    return NULL; // Indicate failure or that the data was not set
}

BOOL WINAPI HookedEmptyClipboard() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedEmptyClipboard");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedEmptyClipboard");
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "EmptyClipboard hook called, but not clearing the clipboard");
    std::cout << "EmptyClipboard hook called, but not clearing the clipboard." << std::endl;
    return TRUE; // Pretend success
}

// Implementation of hooked process management functions
HANDLE WINAPI HookedOpenProcess(DWORD dwDesiredAccess, BOOL bInheritHandle, DWORD dwProcessId) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedOpenProcess");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedOpenProcess");
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "OpenProcess hook called, but not opening process. ProcessId: " + std::to_string(dwProcessId));
    std::cout << "OpenProcess hook called, but not opening process." << std::endl;
    return NULL;
}

BOOL WINAPI HookedTerminateProcess(HANDLE hProcess, UINT uExitCode) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedTerminateProcess");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedTerminateProcess");
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "TerminateProcess hook called, but not terminating process. ExitCode: " + std::to_string(uExitCode));
    std::cout << "TerminateProcess hook called, but not terminating process." << std::endl;
    return TRUE; // Simulate success
}

VOID WINAPI HookedExitProcess(UINT uExitCode) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedExitProcess");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedExitProcess");
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "ExitProcess hook called, but not exiting process. ExitCode: " + std::to_string(uExitCode));
    std::cout << "ExitProcess hook called, but not exiting process." << std::endl;
}

BOOL WINAPI HookedK32EnumProcesses(DWORD* pProcessIds, DWORD cb, DWORD* pBytesReturned) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedK32EnumProcesses");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedK32EnumProcesses");
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "K32EnumProcesses hook called, but pretending no processes exist");
    std::cout << "K32EnumProcesses hook called, but pretending no processes exist." << std::endl;
    if (pBytesReturned != NULL) {
        *pBytesReturned = 0; // Indicate no processes were written to the buffer
    }
    return TRUE; // Indicate the function succeeded
}

// Implementation of hooked window management functions
int WINAPI HookedGetWindowTextW(HWND hWnd, LPWSTR lpString, int nMaxCount) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedGetWindowTextW");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedGetWindowTextW");
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "GetWindowTextW hook called, but not returning actual window text. MaxCount: " + std::to_string(nMaxCount));
    std::cout << "GetWindowTextW hook called, but not returning actual window text." << std::endl;
    if (nMaxCount > 0) {
        lpString[0] = L'\0'; // Return an empty string
    }
    return 0; // Indicate that no characters were copied to the buffer
}

BOOL WINAPI HookedSetWindowPos(HWND hWnd, HWND hWndInsertAfter, int X, int Y, int cx, int cy, UINT uFlags) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedSetWindowPos");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedSetWindowPos");
    
    // Update the static tracking variables in WindowsAPIHooks
    WindowsAPIHooks::s_setWindowFocusHWND = hWnd;
    WindowsAPIHooks::s_setWindowFocushWndInsertAfter = hWndInsertAfter;
    WindowsAPIHooks::s_setWindowFocusX = X;
    WindowsAPIHooks::s_setWindowFocusY = Y;
    WindowsAPIHooks::s_setWindowFocuscx = cx;
    WindowsAPIHooks::s_setWindowFocuscy = cy;
    WindowsAPIHooks::s_setWindowFocusuFlags = uFlags;
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "SetWindowPos hook called, but not changing window position. X: " + std::to_string(X) + ", Y: " + std::to_string(Y));
    std::cout << "SetWindowPos hook called, but not changing window position." << std::endl;
    return TRUE; // Pretend success
}

BOOL WINAPI HookedShowWindow(HWND hWnd) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedShowWindow");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedShowWindow");
    
    WindowsAPIHooks::s_bringWindowToTopHWND = hWnd;
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "ShowWindow hook called, but not bringing window to top");
    std::cout << "ShowWindow hook called, but not bringing window to top." << std::endl;
    return TRUE; // Pretend success
}

HWND WINAPI HookedGetWindow(HWND hWnd, UINT uCmd) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedGetWindow");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedGetWindow");
    
    ErrorHandler::GetInstance().LogInfo("HookedFunctions", "GetWindow hook called, but pretending no related window. Command: " + std::to_string(uCmd));
    std::cout << "GetWindow hook called, but pretending no related window." << std::endl;
    return NULL; // Indicate no window found
}

// Implementation of the GetForegroundWindow hook
HWND WINAPI HookedGetForegroundWindow() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedGetForegroundWindow");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedGetForegroundWindow");
    
    HWND hWnd = WindowsAPIHooks::FindMainWindow();
    if (hWnd != NULL) {
        ErrorHandler::GetInstance().LogInfo("HookedFunctions", "Returning the main window of the current application: " + std::to_string(reinterpret_cast<uintptr_t>(hWnd)));
        std::cout << "Returning the main window of the current application." << std::endl;
        return hWnd;
    }
    ErrorHandler::GetInstance().LogWarning("HookedFunctions", "Main window not found, returning NULL");
    std::cout << "Main window not found, returning NULL." << std::endl;
    return NULL;
}

// Implementation of the SetFocus hook
HWND WINAPI HookedSetFocus(HWND hWnd) {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("HookedSetFocus");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("HookedSetFocus");
    
    WindowsAPIHooks::s_focusHWND = hWnd;
    HWND mainWindow = WindowsAPIHooks::FindMainWindow();
    if (mainWindow != NULL) {
        ErrorHandler::GetInstance().LogInfo("HookedFunctions", "Returning the main window of the current application due to hook: " + std::to_string(reinterpret_cast<uintptr_t>(mainWindow)));
        std::cout << "Returning the main window of the current application due to hook." << std::endl;
        return mainWindow;
    }
    else {
        ErrorHandler::GetInstance().LogWarning("HookedFunctions", "Main window not found, returning NULL");
        std::cout << "Main window not found, returning NULL." << std::endl;
        return NULL;
    }
}

} // namespace WindowsHook
} // namespace UndownUnlock 