#include "../../../include/hooks/keyboard_hook.h"
#include "../../../include/hooks/windows_api_hooks.h"
#include "../../../include/utils/raii_wrappers.h"
#include "../../../include/error_handler.h"
#include "../../../include/memory_tracker.h"
#include "../../../include/performance_monitor.h"

namespace UndownUnlock {
namespace WindowsHook {

// Initialize static variables
HHOOK KeyboardHook::s_keyboardHook = NULL;

// Performance monitoring for keyboard hook operations
static PerformanceMonitor g_keyboardHookMonitor("KeyboardHook");

// Memory tracking for keyboard hook resources
static MemoryTracker g_keyboardHookMemory("KeyboardHook");

void KeyboardHook::Initialize() {
    auto timer = g_keyboardHookMonitor.StartTimer("Initialize");
    
    try {
        // Track memory allocation for hook
        g_keyboardHookMemory.TrackAllocation("HookHandle", sizeof(HHOOK));
        
        // Install a low-level keyboard hook that will monitor all keyboard input
        s_keyboardHook = SetWindowsHookEx(WH_KEYBOARD_LL, KeyboardHookProc, nullptr, 0);
        
        if (s_keyboardHook == NULL) {
            DWORD error = GetLastError();
            ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::WINDOWS_API, 
                                 "Failed to install keyboard hook", 
                                 {{"ErrorCode", std::to_string(error)},
                                  {"Operation", "SetWindowsHookEx"},
                                  {"HookType", "WH_KEYBOARD_LL"}});
        }
        else {
            ErrorHandler::LogInfo(ErrorCategory::WINDOWS_API, 
                                "Keyboard hook installed successfully",
                                {{"HookHandle", std::to_string(reinterpret_cast<uintptr_t>(s_keyboardHook))}});
        }
        
        timer.Stop();
        g_keyboardHookMonitor.RecordOperation("Initialize", timer.GetElapsedTime());
        
    } catch (const std::exception& e) {
        timer.Stop();
        ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::EXCEPTION,
                             "Exception during keyboard hook initialization",
                             {{"Exception", e.what()},
                              {"Operation", "Initialize"}});
        throw;
    }
}

void KeyboardHook::Shutdown() {
    auto timer = g_keyboardHookMonitor.StartTimer("Shutdown");
    
    try {
        if (s_keyboardHook != NULL) {
            // Remove the keyboard hook
            if (UnhookWindowsHookEx(s_keyboardHook)) {
                ErrorHandler::LogInfo(ErrorCategory::WINDOWS_API,
                                    "Keyboard hook removed successfully",
                                    {{"HookHandle", std::to_string(reinterpret_cast<uintptr_t>(s_keyboardHook))}});
            }
            else {
                DWORD error = GetLastError();
                ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::WINDOWS_API,
                                     "Failed to remove keyboard hook",
                                     {{"ErrorCode", std::to_string(error)},
                                      {"Operation", "UnhookWindowsHookEx"},
                                      {"HookHandle", std::to_string(reinterpret_cast<uintptr_t>(s_keyboardHook))}});
            }
            
            // Track memory deallocation
            g_keyboardHookMemory.TrackDeallocation("HookHandle");
            s_keyboardHook = NULL;
        }
        
        timer.Stop();
        g_keyboardHookMonitor.RecordOperation("Shutdown", timer.GetElapsedTime());
        
    } catch (const std::exception& e) {
        timer.Stop();
        ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::EXCEPTION,
                             "Exception during keyboard hook shutdown",
                             {{"Exception", e.what()},
                              {"Operation", "Shutdown"}});
        throw;
    }
}

void KeyboardHook::RunMessageLoop() {
    auto timer = g_keyboardHookMonitor.StartTimer("MessageLoop");
    
    try {
        // Message loop to keep the hook alive and process messages
        MSG msg;
        while (GetMessage(&msg, nullptr, 0, 0)) {
            auto msgTimer = g_keyboardHookMonitor.StartTimer("MessageProcessing");
            
            TranslateMessage(&msg);
            DispatchMessage(&msg);
            
            msgTimer.Stop();
            g_keyboardHookMonitor.RecordOperation("MessageProcessing", msgTimer.GetElapsedTime());
        }
        
        timer.Stop();
        g_keyboardHookMonitor.RecordOperation("MessageLoop", timer.GetElapsedTime());
        
    } catch (const std::exception& e) {
        timer.Stop();
        ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::EXCEPTION,
                             "Exception during message loop",
                             {{"Exception", e.what()},
                              {"Operation", "RunMessageLoop"}});
        throw;
    }
}

LRESULT CALLBACK KeyboardHook::KeyboardHookProc(int nCode, WPARAM wParam, LPARAM lParam) {
    auto timer = g_keyboardHookMonitor.StartTimer("HookCallback");
    
    try {
        // Check if we need to process this message
        if (nCode == HC_ACTION) {
            PKBDLLHOOKSTRUCT p = (PKBDLLHOOKSTRUCT)lParam;
            
            // Only process key down events
            if (wParam == WM_KEYDOWN) {
                auto keyTimer = g_keyboardHookMonitor.StartTimer("KeyProcessing");
                
                switch (p->vkCode) {
                    // VK_UP is the virtual key code for the Up arrow key
                    case VK_UP:
                        try {
                            WindowsAPIHooks::InstallFocusHooks();
                            ErrorHandler::LogInfo(ErrorCategory::WINDOWS_API,
                                                "Up arrow key pressed, installing focus hooks",
                                                {{"VirtualKeyCode", std::to_string(p->vkCode)},
                                                 {"ScanCode", std::to_string(p->scanCode)}});
                        } catch (const std::exception& e) {
                            ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::WINDOWS_API,
                                                 "Failed to install focus hooks on up arrow",
                                                 {{"Exception", e.what()},
                                                  {"VirtualKeyCode", std::to_string(p->vkCode)}});
                        }
                        break;
                        
                    // VK_DOWN is the virtual key code for the Down arrow key
                    case VK_DOWN:
                        try {
                            WindowsAPIHooks::UninstallFocusHooks();
                            
                            // Apply the original functions to restore normal behavior
                            if (WindowsAPIHooks::s_focusHWND != NULL) {
                                SetFocus(WindowsAPIHooks::s_focusHWND);
                            }
                            
                            if (WindowsAPIHooks::s_bringWindowToTopHWND != NULL) {
                                BringWindowToTop(WindowsAPIHooks::s_bringWindowToTopHWND);
                            }
                            
                            if (WindowsAPIHooks::s_setWindowFocusHWND != NULL) {
                                SetWindowPos(
                                    WindowsAPIHooks::s_setWindowFocusHWND, 
                                    WindowsAPIHooks::s_setWindowFocushWndInsertAfter, 
                                    WindowsAPIHooks::s_setWindowFocusX, 
                                    WindowsAPIHooks::s_setWindowFocusY, 
                                    WindowsAPIHooks::s_setWindowFocuscx, 
                                    WindowsAPIHooks::s_setWindowFocuscy, 
                                    WindowsAPIHooks::s_setWindowFocusuFlags
                                );
                            }
                            
                            ErrorHandler::LogInfo(ErrorCategory::WINDOWS_API,
                                                "Down arrow key pressed, uninstalling focus hooks",
                                                {{"VirtualKeyCode", std::to_string(p->vkCode)},
                                                 {"ScanCode", std::to_string(p->scanCode)}});
                        } catch (const std::exception& e) {
                            ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::WINDOWS_API,
                                                 "Failed to uninstall focus hooks on down arrow",
                                                 {{"Exception", e.what()},
                                                  {"VirtualKeyCode", std::to_string(p->vkCode)}});
                        }
                        break;
                }
                
                keyTimer.Stop();
                g_keyboardHookMonitor.RecordOperation("KeyProcessing", keyTimer.GetElapsedTime());
            }
        }
        
        timer.Stop();
        g_keyboardHookMonitor.RecordOperation("HookCallback", timer.GetElapsedTime());
        
        // Call the next hook in the chain
        return CallNextHookEx(s_keyboardHook, nCode, wParam, lParam);
        
    } catch (const std::exception& e) {
        timer.Stop();
        ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::EXCEPTION,
                             "Exception in keyboard hook callback",
                             {{"Exception", e.what()},
                              {"Operation", "KeyboardHookProc"},
                              {"nCode", std::to_string(nCode)},
                              {"wParam", std::to_string(wParam)}});
        
        // Still call the next hook even if we had an exception
        return CallNextHookEx(s_keyboardHook, nCode, wParam, lParam);
    }
}

} // namespace WindowsHook
} // namespace UndownUnlock 