#include "../../include/dx_hook_core.h"
#include <Psapi.h>
#include <algorithm>
#include <unordered_map>
#include <iostream>

namespace UndownUnlock {
namespace DXHook {

MemoryScanner::MemoryScanner()
    : m_d3d11Module(nullptr), m_dxgiModule(nullptr) {
}

MemoryScanner::~MemoryScanner() {
    // No need to free the module handles as we're not loading them explicitly
}

bool MemoryScanner::FindDXModules() {
    // Find the D3D11 module
    m_d3d11Module = GetModuleHandleA("d3d11.dll");
    if (!m_d3d11Module) {
        std::cerr << "Failed to find D3D11.dll in process memory" << std::endl;
        return false;
    }

    // Find the DXGI module
    m_dxgiModule = GetModuleHandleA("dxgi.dll");
    if (!m_dxgiModule) {
        std::cerr << "Failed to find DXGI.dll in process memory" << std::endl;
        return false;
    }

    // Initialize memory regions for efficient scanning
    InitializeMemoryRegions();

    return true;
}

void MemoryScanner::InitializeMemoryRegions() {
    m_memoryRegions.clear();

    // Get system info for memory range
    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);

    // Scan the entire process memory range
    MEMORY_BASIC_INFORMATION memInfo;
    LPVOID address = sysInfo.lpMinimumApplicationAddress;

    while (address < sysInfo.lpMaximumApplicationAddress) {
        if (VirtualQuery(address, &memInfo, sizeof(memInfo))) {
            // Only add regions that are committed and have execute or read access
            if ((memInfo.State == MEM_COMMIT) && 
                (memInfo.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_READONLY | PAGE_READWRITE))) {
                
                MemoryRegion region;
                region.baseAddress = memInfo.BaseAddress;
                region.size = memInfo.RegionSize;
                region.protection = memInfo.Protect;
                
                m_memoryRegions.push_back(region);
            }
            
            // Move to the next memory region
            address = (LPBYTE)memInfo.BaseAddress + memInfo.RegionSize;
        } else {
            // If VirtualQuery fails, move to the next page
            address = (LPBYTE)address + sysInfo.dwPageSize;
        }
    }

    std::cout << "Initialized " << m_memoryRegions.size() << " memory regions for scanning" << std::endl;
}

std::vector<void*> MemoryScanner::ScanForPattern(const std::vector<uint8_t>& pattern, const std::string& mask) {
    std::vector<void*> results;
    
    if (pattern.empty() || mask.empty() || pattern.size() != mask.size()) {
        std::cerr << "Invalid pattern or mask" << std::endl;
        return results;
    }
    
    // Boyer-Moore-Horspool algorithm for faster scanning
    
    // Preprocessing: bad character table
    const int alphabetSize = 256;  // One byte can have 256 possible values
    std::vector<size_t> badChar(alphabetSize, mask.size());
    
    for (size_t i = 0; i < mask.size() - 1; i++) {
        if (mask[i] != '?') {
            badChar[pattern[i]] = mask.size() - 1 - i;
        }
    }
    
    // Scan each memory region
    for (const auto& region : m_memoryRegions) {
        // Skip regions that don't have read access
        if (!(region.protection & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE))) {
            continue;
        }
        
        const uint8_t* data = static_cast<const uint8_t*>(region.baseAddress);
        size_t regionSize = region.size;
        
        // Boyer-Moore-Horspool search
        size_t i = 0;
        while (i <= regionSize - pattern.size()) {
            size_t j = pattern.size() - 1;
            
            // Check pattern from right to left
            while (j != static_cast<size_t>(-1) && (mask[j] == '?' || pattern[j] == data[i + j])) {
                j--;
            }
            
            // Pattern found
            if (j == static_cast<size_t>(-1)) {
                results.push_back(const_cast<uint8_t*>(data + i));
            }
            
            // Shift pattern based on bad character rule
            i += badChar[data[i + pattern.size() - 1]];
        }
    }
    
    return results;
}

std::unordered_map<std::string, std::vector<int>> MemoryScanner::CalculateVTableOffsets() {
    std::unordered_map<std::string, std::vector<int>> offsets;
    
    // D3D11 interface offsets
    offsets["ID3D11Device"] = {
        // Common methods
        0,  // QueryInterface
        1,  // AddRef
        2,  // Release
        
        // D3D11Device specific methods
        3,  // CreateBuffer
        4,  // CreateTexture1D
        5,  // CreateTexture2D
        6,  // CreateTexture3D
        // ... more methods as needed
    };
    
    // DXGI interfaces
    offsets["IDXGISwapChain"] = {
        // Common methods
        0,  // QueryInterface
        1,  // AddRef
        2,  // Release
        
        // IDXGISwapChain specific methods
        3,  // SetPrivateData
        4,  // SetPrivateDataInterface
        5,  // GetPrivateData
        6,  // GetParent
        7,  // GetDevice
        8,  // Present
        9,  // GetBuffer
        10, // SetFullscreenState
        11, // GetFullscreenState
        // ... more methods as needed
    };
    
    offsets["IDXGISwapChain1"] = {
        // Includes all IDXGISwapChain methods (0-11) plus:
        12, // GetDesc1
        13, // GetFullscreenDesc
        14, // GetHwnd
        15, // GetCoreWindow
        16, // Present1
        17, // IsTemporaryMonoSupported
        18, // GetRestrictToOutput
        19, // SetBackgroundColor
        20, // GetBackgroundColor
        21, // SetRotation
        22  // GetRotation
    };
    
    return offsets;
}

std::unordered_map<std::string, void*> MemoryScanner::ParseExportTable(const std::string& moduleName) {
    std::unordered_map<std::string, void*> exports;
    
    HMODULE module = GetModuleHandleA(moduleName.c_str());
    if (!module) {
        std::cerr << "Failed to get handle to module: " << moduleName << std::endl;
        return exports;
    }
    
    // Get the DOS header
    PIMAGE_DOS_HEADER dosHeader = (PIMAGE_DOS_HEADER)module;
    if (dosHeader->e_magic != IMAGE_DOS_SIGNATURE) {
        std::cerr << "Invalid DOS header signature" << std::endl;
        return exports;
    }
    
    // Get the NT headers
    PIMAGE_NT_HEADERS ntHeaders = (PIMAGE_NT_HEADERS)((BYTE*)module + dosHeader->e_lfanew);
    if (ntHeaders->Signature != IMAGE_NT_SIGNATURE) {
        std::cerr << "Invalid NT header signature" << std::endl;
        return exports;
    }
    
    // Get the export directory
    DWORD exportDirRVA = ntHeaders->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress;
    if (exportDirRVA == 0) {
        std::cerr << "No export directory found" << std::endl;
        return exports;
    }
    
    PIMAGE_EXPORT_DIRECTORY exportDir = (PIMAGE_EXPORT_DIRECTORY)((BYTE*)module + exportDirRVA);
    
    // Get the export tables
    PDWORD functions = (PDWORD)((BYTE*)module + exportDir->AddressOfFunctions);
    PDWORD names = (PDWORD)((BYTE*)module + exportDir->AddressOfNames);
    PWORD ordinals = (PWORD)((BYTE*)module + exportDir->AddressOfNameOrdinals);
    
    // Iterate through all exported functions
    for (DWORD i = 0; i < exportDir->NumberOfNames; i++) {
        const char* name = (const char*)((BYTE*)module + names[i]);
        DWORD functionRVA = functions[ordinals[i]];
        void* functionAddr = (BYTE*)module + functionRVA;
        
        exports[name] = functionAddr;
    }
    
    return exports;
}

} // namespace DXHook
} // namespace UndownUnlock 