#pragma once

#include <Windows.h>

namespace UndownUnlock {
namespace WindowsHook {

/**
 * @brief Utility functions for hooking Windows API functions
 */
class HookUtils {
public:
    /**
     * @brief Install a hook by modifying the target function with a JMP instruction
     * @param targetFunction Pointer to the function to hook
     * @param hookFunction Pointer to the replacement function
     * @param originalBytes Buffer to store the original bytes for later restoration
     * @return True if the hook was successfully installed
     */
    static bool InstallHook(void* targetFunction, void* hookFunction, BYTE* originalBytes);

    /**
     * @brief Remove a hook and restore the original function
     * @param targetFunction Pointer to the hooked function
     * @param originalBytes Buffer containing the original bytes
     * @return True if the hook was successfully removed
     */
    static bool RemoveHook(void* targetFunction, BYTE* originalBytes);

    /**
     * @brief Find the main window of the current process
     * @return Handle to the main window, or NULL if not found
     */
    static HWND FindMainWindow();

    // Test comment for writability
};

// Helper function for window enumeration
BOOL CALLBACK EnumWindowsCallback(HWND handle, LPARAM lParam);
BOOL IsMainWindow(HWND handle);

} // namespace WindowsHook
} // namespace UndownUnlock 