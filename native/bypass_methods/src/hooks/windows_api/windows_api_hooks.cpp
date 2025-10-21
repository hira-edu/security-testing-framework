#include "../../../include/hooks/windows_api_hooks.h"
#include "../../../include/hooks/hooked_functions.h"
#include "../../../include/hooks/hook_utils.h"
#include "../../../include/hooks/keyboard_hook.h"
#include "../../../include/raii_wrappers.h"
#include "../../../include/error_handler.h"
#include "../../../include/performance_monitor.h"
#include "../../../include/memory_tracker.h"

namespace UndownUnlock {
namespace WindowsHook {

// Initialize static variables
BYTE WindowsAPIHooks::s_originalBytesForGetForeground[5] = { 0 };
BYTE WindowsAPIHooks::s_originalBytesForShowWindow[5] = { 0 };
BYTE WindowsAPIHooks::s_originalBytesForSetWindowPos[5] = { 0 };
BYTE WindowsAPIHooks::s_originalBytesForSetFocus[5] = { 0 };
BYTE WindowsAPIHooks::s_originalBytesForEmptyClipboard[5] = { 0 };
BYTE WindowsAPIHooks::s_originalBytesForSetClipboardData[5] = { 0 };
BYTE WindowsAPIHooks::s_originalBytesForTerminateProcess[5] = { 0 };
BYTE WindowsAPIHooks::s_originalBytesForExitProcess[5] = { 0 };

bool WindowsAPIHooks::s_isFocusInstalled = false;
HWND WindowsAPIHooks::s_focusHWND = NULL;
HWND WindowsAPIHooks::s_bringWindowToTopHWND = NULL;
HWND WindowsAPIHooks::s_setWindowFocusHWND = NULL;
HWND WindowsAPIHooks::s_setWindowFocushWndInsertAfter = NULL;
int WindowsAPIHooks::s_setWindowFocusX = 0;
int WindowsAPIHooks::s_setWindowFocusY = 0;
int WindowsAPIHooks::s_setWindowFocuscx = 0;
int WindowsAPIHooks::s_setWindowFocuscy = 0;
UINT WindowsAPIHooks::s_setWindowFocusuFlags = 0;

bool WindowsAPIHooks::Initialize() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::Initialize");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("WindowsAPIHooks::Initialize");
    
    ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Installing Windows API hooks");
    std::cout << "Installing Windows API hooks..." << std::endl;

    // Hook EmptyClipboard
    auto user32Timer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::HookEmptyClipboard");
    HMODULE hUser32 = GetModuleHandle(L"user32.dll");
    if (hUser32) {
        void* targetEmptyClipboard = GetProcAddress(hUser32, "EmptyClipboard");
        if (targetEmptyClipboard) {
            bool success = HookUtils::InstallHook(targetEmptyClipboard, (void*)HookedEmptyClipboard, s_originalBytesForEmptyClipboard);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully hooked EmptyClipboard");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to hook EmptyClipboard", 
                    ErrorSeverity::ERROR, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get EmptyClipboard address", 
                ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
        }
    } else {
        ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get user32.dll handle", 
            ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
    }

    // Hook GetForegroundWindow
    auto foregroundTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::HookGetForegroundWindow");
    if (hUser32) {
        void* targetGetForegroundWindow = GetProcAddress(hUser32, "GetForegroundWindow");
        if (targetGetForegroundWindow) {
            bool success = HookUtils::InstallHook(targetGetForegroundWindow, (void*)HookedGetForegroundWindow, s_originalBytesForGetForeground);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully hooked GetForegroundWindow");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to hook GetForegroundWindow", 
                    ErrorSeverity::ERROR, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get GetForegroundWindow address", 
                ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
        }
    }

    // Hook TerminateProcess
    auto terminateTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::HookTerminateProcess");
    HMODULE hKernel32 = GetModuleHandle(L"kernel32.dll");
    if (hKernel32) {
        void* targetTerminateProcess = GetProcAddress(hKernel32, "TerminateProcess");
        if (targetTerminateProcess) {
            bool success = HookUtils::InstallHook(targetTerminateProcess, (void*)HookedTerminateProcess, s_originalBytesForTerminateProcess);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully hooked TerminateProcess");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to hook TerminateProcess", 
                    ErrorSeverity::ERROR, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get TerminateProcess address", 
                ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
        }
    } else {
        ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get kernel32.dll handle", 
            ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
    }

    // Hook ExitProcess
    auto exitTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::HookExitProcess");
    if (hKernel32) {
        void* targetExitProcess = GetProcAddress(hKernel32, "ExitProcess");
        if (targetExitProcess) {
            bool success = HookUtils::InstallHook(targetExitProcess, (void*)HookedExitProcess, s_originalBytesForExitProcess);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully hooked ExitProcess");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to hook ExitProcess", 
                    ErrorSeverity::ERROR, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get ExitProcess address", 
                ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
        }
    }

    // Show a message box to indicate successful injection
    ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Windows API hooks installation complete");
    MessageBox(NULL, L"UndownUnlock Windows API Hooks Injected", L"UndownUnlock", MB_OK);
    return true;
}

void WindowsAPIHooks::Shutdown() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::Shutdown");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("WindowsAPIHooks::Shutdown");
    
    ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Removing Windows API hooks");
    std::cout << "Removing Windows API hooks..." << std::endl;
    
    // Unhook SetClipboardData
    auto clipboardTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::UnhookSetClipboardData");
    HMODULE hUser32 = GetModuleHandle(L"user32.dll");
    if (hUser32) {
        void* targetSetClipboardData = GetProcAddress(hUser32, "SetClipboardData");
        if (targetSetClipboardData) {
            bool success = HookUtils::RemoveHook(targetSetClipboardData, s_originalBytesForSetClipboardData);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully unhooked SetClipboardData");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to unhook SetClipboardData", 
                    ErrorSeverity::WARNING, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get SetClipboardData address for unhooking", 
                ErrorSeverity::WARNING, ErrorCategory::SYSTEM);
        }
    }

    // Unhook EmptyClipboard
    auto emptyClipboardTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::UnhookEmptyClipboard");
    if (hUser32) {
        void* targetEmptyClipboard = GetProcAddress(hUser32, "EmptyClipboard");
        if (targetEmptyClipboard) {
            bool success = HookUtils::RemoveHook(targetEmptyClipboard, s_originalBytesForEmptyClipboard);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully unhooked EmptyClipboard");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to unhook EmptyClipboard", 
                    ErrorSeverity::WARNING, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get EmptyClipboard address for unhooking", 
                ErrorSeverity::WARNING, ErrorCategory::SYSTEM);
        }
    }

    // Unhook GetForegroundWindow
    auto foregroundTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::UnhookGetForegroundWindow");
    if (hUser32) {
        void* targetGetForegroundWindow = GetProcAddress(hUser32, "GetForegroundWindow");
        if (targetGetForegroundWindow) {
            bool success = HookUtils::RemoveHook(targetGetForegroundWindow, s_originalBytesForGetForeground);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully unhooked GetForegroundWindow");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to unhook GetForegroundWindow", 
                    ErrorSeverity::WARNING, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get GetForegroundWindow address for unhooking", 
                ErrorSeverity::WARNING, ErrorCategory::SYSTEM);
        }
    }

    // Unhook focus-related functions if they are installed
    if (s_isFocusInstalled) {
        UninstallFocusHooks();
    }
    
    ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Windows API hooks removal complete");
}

void WindowsAPIHooks::InstallFocusHooks() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::InstallFocusHooks");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("WindowsAPIHooks::InstallFocusHooks");
    
    if (s_isFocusInstalled) {
        ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Focus hooks already installed");
        return;
    }
    
    s_isFocusInstalled = true;
    ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Installing focus-related hooks");
    std::cout << "Installing focus-related hooks..." << std::endl;

    // Hook BringWindowToTop
    auto bringWindowTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::HookBringWindowToTop");
    HMODULE hUser32 = GetModuleHandle(L"user32.dll");
    if (hUser32) {
        void* targetShowWindow = GetProcAddress(hUser32, "BringWindowToTop");
        if (targetShowWindow) {
            bool success = HookUtils::InstallHook(targetShowWindow, (void*)HookedShowWindow, s_originalBytesForShowWindow);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully hooked BringWindowToTop");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to hook BringWindowToTop", 
                    ErrorSeverity::ERROR, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get BringWindowToTop address", 
                ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
        }
    } else {
        ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get user32.dll handle for focus hooks", 
            ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
    }

    // Hook SetWindowPos
    auto setWindowPosTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::HookSetWindowPos");
    if (hUser32) {
        void* targetSetWindowPos = GetProcAddress(hUser32, "SetWindowPos");
        if (targetSetWindowPos) {
            bool success = HookUtils::InstallHook(targetSetWindowPos, (void*)HookedSetWindowPos, s_originalBytesForSetWindowPos);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully hooked SetWindowPos");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to hook SetWindowPos", 
                    ErrorSeverity::ERROR, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get SetWindowPos address", 
                ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
        }
    }

    // Hook SetFocus
    auto setFocusTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::HookSetFocus");
    if (hUser32) {
        void* targetSetFocus = GetProcAddress(hUser32, "SetFocus");
        if (targetSetFocus) {
            bool success = HookUtils::InstallHook(targetSetFocus, (void*)HookedSetFocus, s_originalBytesForSetFocus);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully hooked SetFocus");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to hook SetFocus", 
                    ErrorSeverity::ERROR, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get SetFocus address", 
                ErrorSeverity::ERROR, ErrorCategory::SYSTEM);
        }
    }
}

void WindowsAPIHooks::UninstallFocusHooks() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::UninstallFocusHooks");
    auto errorContext = ErrorHandler::GetInstance().CreateContext("WindowsAPIHooks::UninstallFocusHooks");
    
    if (!s_isFocusInstalled) {
        ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Focus hooks not installed");
        return;
    }
    
    s_isFocusInstalled = false;
    ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Uninstalling focus-related hooks");
    std::cout << "Uninstalling focus-related hooks..." << std::endl;

    // Unhook BringWindowToTop
    auto bringWindowTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::UnhookBringWindowToTop");
    HMODULE hUser32 = GetModuleHandle(L"user32.dll");
    if (hUser32) {
        void* targetShowWindow = GetProcAddress(hUser32, "BringWindowToTop");
        if (targetShowWindow) {
            bool success = HookUtils::RemoveHook(targetShowWindow, s_originalBytesForShowWindow);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully unhooked BringWindowToTop");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to unhook BringWindowToTop", 
                    ErrorSeverity::WARNING, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get BringWindowToTop address for unhooking", 
                ErrorSeverity::WARNING, ErrorCategory::SYSTEM);
        }
    }

    // Unhook SetWindowPos
    auto setWindowPosTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::UnhookSetWindowPos");
    if (hUser32) {
        void* targetSetWindowPos = GetProcAddress(hUser32, "SetWindowPos");
        if (targetSetWindowPos) {
            bool success = HookUtils::RemoveHook(targetSetWindowPos, s_originalBytesForSetWindowPos);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully unhooked SetWindowPos");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to unhook SetWindowPos", 
                    ErrorSeverity::WARNING, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get SetWindowPos address for unhooking", 
                ErrorSeverity::WARNING, ErrorCategory::SYSTEM);
        }
    }

    // Unhook SetFocus
    auto setFocusTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::UnhookSetFocus");
    if (hUser32) {
        void* targetSetFocus = GetProcAddress(hUser32, "SetFocus");
        if (targetSetFocus) {
            bool success = HookUtils::RemoveHook(targetSetFocus, s_originalBytesForSetFocus);
            if (success) {
                ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Successfully unhooked SetFocus");
            } else {
                ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to unhook SetFocus", 
                    ErrorSeverity::WARNING, ErrorCategory::HOOK);
            }
        } else {
            ErrorHandler::GetInstance().LogError("WindowsAPIHooks", "Failed to get SetFocus address for unhooking", 
                ErrorSeverity::WARNING, ErrorCategory::SYSTEM);
        }
    }
}

HWND WindowsAPIHooks::FindMainWindow() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::FindMainWindow");
    
    HWND result = HookUtils::FindMainWindow();
    if (result) {
        ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Found main window: " + std::to_string(reinterpret_cast<uintptr_t>(result)));
    } else {
        ErrorHandler::GetInstance().LogWarning("WindowsAPIHooks", "Failed to find main window");
    }
    return result;
}

void WindowsAPIHooks::SetupKeyboardHook() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::SetupKeyboardHook");
    
    ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Setting up keyboard hook");
    KeyboardHook::Initialize();
    KeyboardHook::RunMessageLoop();
}

void WindowsAPIHooks::UninstallKeyboardHook() {
    auto perfTimer = PerformanceMonitor::GetInstance().StartTimer("WindowsAPIHooks::UninstallKeyboardHook");
    
    ErrorHandler::GetInstance().LogInfo("WindowsAPIHooks", "Uninstalling keyboard hook");
    KeyboardHook::Shutdown();
}

} // namespace WindowsHook
} // namespace UndownUnlock 