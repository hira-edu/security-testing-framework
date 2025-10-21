#pragma once

// Standard Windows headers
#include <windows.h>

// DirectX 11 headers
#include <d3d11.h>
#include <dxgi.h>
#include <dxgidebug.h> // For debugging, if needed

// Link necessary DirectX libraries
#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "dxgi.lib")

// Common includes for logging or utilities if any
#include <iostream>
#include <string>
#include <vector>
#include <memory> // For std::unique_ptr

// Placeholder for any common typedefs or constants related to DirectX hooking
// For example:
// typedef HRESULT (WINAPI *PresentFn)(IDXGISwapChain*, UINT, UINT);
// const int PRESENT_VTABLE_INDEX = 8; // For IDXGISwapChain

// Ensure our base hook and trampoline utils are available for DX hooks
#include "hook_base.h"
#include "trampoline_utils.h"
