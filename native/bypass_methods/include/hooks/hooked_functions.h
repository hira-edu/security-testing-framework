#pragma once

#include <Windows.h>

namespace UndownUnlock {
namespace WindowsHook {

// Declaration of hooked Windows API functions
HWND WINAPI HookedGetForegroundWindow();
BOOL WINAPI HookedShowWindow(HWND hWnd);
BOOL WINAPI HookedSetWindowPos(HWND hWnd, HWND hWndInsertAfter, int X, int Y, int cx, int cy, UINT uFlags);
HWND WINAPI HookedSetFocus(HWND hWnd);
HWND WINAPI HookedGetWindow(HWND hWnd, UINT uCmd);
int WINAPI HookedGetWindowTextW(HWND hWnd, LPWSTR lpString, int nMaxCount);
BOOL WINAPI HookedK32EnumProcesses(DWORD* pProcessIds, DWORD cb, DWORD* pBytesReturned);
HANDLE WINAPI HookedOpenProcess(DWORD dwDesiredAccess, BOOL bInheritHandle, DWORD dwProcessId);
BOOL WINAPI HookedTerminateProcess(HANDLE hProcess, UINT uExitCode);
VOID WINAPI HookedExitProcess(UINT uExitCode);
BOOL WINAPI HookedEmptyClipboard();
HANDLE WINAPI HookedSetClipboardData(UINT uFormat, HANDLE hMem);

} // namespace WindowsHook
} // namespace UndownUnlock 