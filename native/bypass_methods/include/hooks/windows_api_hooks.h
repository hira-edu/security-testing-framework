#pragma once

#include <Windows.h>
#include <iostream>
#include <vector>

namespace UndownUnlock {
namespace WindowsHook {

/**
 * @brief Class for hooking Windows API functions to prevent security measures
 */
class WindowsAPIHooks {
public:
    /**
     * @brief Initialize and install the Windows API hooks
     * @return True if successful
     */
    static bool Initialize();

    /**
     * @brief Shutdown and remove all Windows API hooks
     */
    static void Shutdown();

    /**
     * @brief Install hooks for focus/window-related functions
     */
    static void InstallFocusHooks();

    /**
     * @brief Uninstall hooks for focus/window-related functions
     */
    static void UninstallFocusHooks();

    /**
     * @brief Find the main window of the current process
     * @return Handle to the main window, or NULL if not found
     */
    static HWND FindMainWindow();

    /**
     * @brief Install keyboard hook to control hooking behavior
     */
    static void SetupKeyboardHook();

    /**
     * @brief Uninstall the keyboard hook
     */
    static void UninstallKeyboardHook();

    // Original bytes storage for hook restoration
    static BYTE s_originalBytesForGetForeground[5];
    static BYTE s_originalBytesForShowWindow[5];
    static BYTE s_originalBytesForSetWindowPos[5];
    static BYTE s_originalBytesForSetFocus[5];
    static BYTE s_originalBytesForEmptyClipboard[5];
    static BYTE s_originalBytesForSetClipboardData[5];
    static BYTE s_originalBytesForTerminateProcess[5];
    static BYTE s_originalBytesForExitProcess[5];

    // State tracking - public to allow access from the keyboard hook
    static bool s_isFocusInstalled;
    static HWND s_focusHWND;
    static HWND s_bringWindowToTopHWND;
    static HWND s_setWindowFocusHWND;
    static HWND s_setWindowFocushWndInsertAfter;
    static int s_setWindowFocusX;
    static int s_setWindowFocusY;
    static int s_setWindowFocuscx;
    static int s_setWindowFocuscy;
    static UINT s_setWindowFocusuFlags;

private:
    // Helper methods for hooking and unhooking
    static bool HookFunction(void* targetFunction, void* hookFunction, BYTE* originalBytes);
    static bool UnhookFunction(void* targetFunction, BYTE* originalBytes);

    // Keyboard hook callback
    static LRESULT CALLBACK KeyboardHookProc(int nCode, WPARAM wParam, LPARAM lParam);
};

// Helper function for window enumeration
BOOL CALLBACK EnumWindowsCallback(HWND handle, LPARAM lParam);
BOOL IsMainWindow(HWND handle);

} // namespace WindowsHook
} // namespace UndownUnlock 