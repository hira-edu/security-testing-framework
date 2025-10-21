#include "../../include/memory/pattern_scanner.h"
#include "../../include/utils/raii_wrappers.h"
#include "../../include/utils/error_handler.h"
#include "../../include/utils/performance_monitor.h"
#include "../../include/utils/memory_tracker.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <Psapi.h>

namespace UndownUnlock {
namespace DXHook {

PatternScanner::PatternScanner()
    : m_progressCallback(nullptr) {
    
    // Set error context for this pattern scanner instance
    utils::ErrorContext context;
    context.set("component", "PatternScanner");
    context.set("operation", "construction");
    utils::ErrorHandler::GetInstance()->set_error_context(context);
    
    utils::ErrorHandler::GetInstance()->info(
        "PatternScanner created",
        utils::ErrorCategory::SYSTEM,
        __FUNCTION__, __FILE__, __LINE__
    );
}

PatternScanner::~PatternScanner() {
    // Start performance monitoring for cleanup
    auto cleanup_operation = utils::PerformanceMonitor::GetInstance()->start_operation("pattern_scanner_cleanup");
    
    utils::ErrorHandler::GetInstance()->info(
        "Cleaning up PatternScanner",
        utils::ErrorCategory::SYSTEM,
        __FUNCTION__, __FILE__, __LINE__
    );
    
    try {
        // Clear memory regions
        m_memoryRegions.clear();
        
        utils::ErrorHandler::GetInstance()->info(
            "PatternScanner cleanup complete",
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
        
    } catch (const std::exception& e) {
        utils::ErrorHandler::GetInstance()->error(
            "Exception during PatternScanner cleanup: " + std::string(e.what()),
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
    }
    
    // End performance monitoring
    utils::PerformanceMonitor::GetInstance()->end_operation(cleanup_operation);
    
    // Clear error context
    utils::ErrorHandler::GetInstance()->clear_error_context();
}

bool PatternScanner::Initialize() {
    // Start performance monitoring for initialization
    auto init_operation = utils::PerformanceMonitor::GetInstance()->start_operation("pattern_scanner_initialization");
    
    utils::ErrorHandler::GetInstance()->info(
        "Initializing PatternScanner",
        utils::ErrorCategory::SYSTEM,
        __FUNCTION__, __FILE__, __LINE__
    );
    
    try {
        // Initialize memory regions for scanning
        InitializeMemoryRegions();
        
        bool success = !m_memoryRegions.empty();
        
        if (success) {
            utils::ErrorHandler::GetInstance()->info(
                "PatternScanner initialized successfully with " + std::to_string(m_memoryRegions.size()) + " memory regions",
                utils::ErrorCategory::SYSTEM,
                __FUNCTION__, __FILE__, __LINE__
            );
        } else {
            utils::ErrorHandler::GetInstance()->warning(
                "PatternScanner initialized but no memory regions found",
                utils::ErrorCategory::SYSTEM,
                __FUNCTION__, __FILE__, __LINE__
            );
        }
        
        // End performance monitoring
        utils::PerformanceMonitor::GetInstance()->end_operation(init_operation);
        
        return success;
        
    } catch (const std::exception& e) {
        utils::ErrorHandler::GetInstance()->error(
            "Exception in PatternScanner::Initialize: " + std::string(e.what()),
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring on error
        utils::PerformanceMonitor::GetInstance()->end_operation(init_operation);
        
        return false;
    }
}

void PatternScanner::InitializeMemoryRegions() {
    // Start performance monitoring for memory region initialization
    auto region_operation = utils::PerformanceMonitor::GetInstance()->start_operation("memory_region_initialization");
    
    // Track memory allocation for regions
    auto memory_tracker = utils::MemoryTracker::GetInstance();
    
    try {
        // Clear existing regions
        m_memoryRegions.clear();
        
        // Get system info for memory range
        SYSTEM_INFO sysInfo;
        GetSystemInfo(&sysInfo);
        
        // Scan the entire process memory range
        MEMORY_BASIC_INFORMATION memInfo;
        LPVOID address = sysInfo.lpMinimumApplicationAddress;
        
        // Get modules to name memory regions
        std::vector<std::tuple<void*, size_t, std::string>> modules = GetModules();
        
        int regionCount = 0;
        while (address < sysInfo.lpMaximumApplicationAddress) {
            if (VirtualQuery(address, &memInfo, sizeof(memInfo))) {
                // Only add regions that are committed and have execute or read access
                if ((memInfo.State == MEM_COMMIT) && 
                    (memInfo.Protect & (PAGE_EXECUTE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_READONLY | PAGE_READWRITE))) {
                    
                    MemoryRegion region;
                    region.baseAddress = memInfo.BaseAddress;
                    region.size = memInfo.RegionSize;
                    region.protection = memInfo.Protect;
                    
                    // Try to find a module that contains this address
                    for (const auto& module : modules) {
                        void* moduleBase = std::get<0>(module);
                        size_t moduleSize = std::get<1>(module);
                        
                        if (memInfo.BaseAddress >= moduleBase && 
                            reinterpret_cast<uint8_t*>(memInfo.BaseAddress) < reinterpret_cast<uint8_t*>(moduleBase) + moduleSize) {
                            region.name = std::get<2>(module);
                            break;
                        }
                    }
                    
                    m_memoryRegions.push_back(region);
                    regionCount++;
                }
                
                // Move to the next memory region
                address = reinterpret_cast<LPBYTE>(memInfo.BaseAddress) + memInfo.RegionSize;
            } else {
                // If VirtualQuery fails, move to the next page
                address = reinterpret_cast<LPBYTE>(address) + sysInfo.dwPageSize;
            }
        }
        
        utils::ErrorHandler::GetInstance()->info(
            "Initialized " + std::to_string(m_memoryRegions.size()) + " memory regions for scanning",
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring
        utils::PerformanceMonitor::GetInstance()->end_operation(region_operation);
        
    } catch (const std::exception& e) {
        utils::ErrorHandler::GetInstance()->error(
            "Exception during memory region initialization: " + std::string(e.what()),
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring on error
        utils::PerformanceMonitor::GetInstance()->end_operation(region_operation);
    }
}

std::vector<std::tuple<void*, size_t, std::string>> PatternScanner::GetModules() {
    std::vector<std::tuple<void*, size_t, std::string>> modules;
    
    try {
        // Enumerate all modules in the process
        HMODULE moduleHandles[1024];
        DWORD cbNeeded;
        
        if (EnumProcessModules(GetCurrentProcess(), moduleHandles, sizeof(moduleHandles), &cbNeeded)) {
            int moduleCount = cbNeeded / sizeof(HMODULE);
            
            utils::ErrorHandler::GetInstance()->debug(
                "Found " + std::to_string(moduleCount) + " modules in process",
                utils::ErrorCategory::SYSTEM,
                __FUNCTION__, __FILE__, __LINE__
            );
            
            for (int i = 0; i < moduleCount; i++) {
                MODULEINFO moduleInfo;
                if (GetModuleInformation(GetCurrentProcess(), moduleHandles[i], &moduleInfo, sizeof(moduleInfo))) {
                    char moduleName[MAX_PATH];
                    if (GetModuleFileNameExA(GetCurrentProcess(), moduleHandles[i], moduleName, MAX_PATH)) {
                        // Extract just the filename
                        std::string fullPath(moduleName);
                        size_t lastSlash = fullPath.find_last_of("/\\");
                        std::string fileName = (lastSlash != std::string::npos) ? 
                            fullPath.substr(lastSlash + 1) : fullPath;
                        
                        modules.emplace_back(moduleInfo.lpBaseOfDll, moduleInfo.SizeOfImage, fileName);
                    }
                }
            }
        } else {
            utils::ErrorHandler::GetInstance()->warning(
                "Failed to enumerate process modules",
                utils::ErrorCategory::SYSTEM,
                __FUNCTION__, __FILE__, __LINE__, GetLastError()
            );
        }
        
        utils::ErrorHandler::GetInstance()->debug(
            "Retrieved " + std::to_string(modules.size()) + " module information entries",
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
        
    } catch (const std::exception& e) {
        utils::ErrorHandler::GetInstance()->error(
            "Exception during module enumeration: " + std::string(e.what()),
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
    }
    
    return modules;
}

void PatternScanner::AddMemoryRegion(const MemoryRegion& region) {
    m_memoryRegions.push_back(region);
}

const std::vector<MemoryRegion>& PatternScanner::GetMemoryRegions() const {
    return m_memoryRegions;
}

void PatternScanner::SetProgressCallback(std::function<void(int)> callback) {
    m_progressCallback = callback;
    
    utils::ErrorHandler::GetInstance()->debug(
        "Progress callback set",
        utils::ErrorCategory::SYSTEM,
        __FUNCTION__, __FILE__, __LINE__
    );
}

std::pair<std::vector<uint8_t>, std::string> PatternScanner::ParsePatternString(const std::string& patternString) {
    std::vector<uint8_t> pattern;
    std::string mask;
    
    try {
        std::istringstream stream(patternString);
        std::string token;
        
        while (stream >> token) {
            if (token == "?" || token == "??") {
                pattern.push_back(0);
                mask.push_back('?');
            } else {
                // Convert hex string to byte
                try {
                    uint8_t byte = static_cast<uint8_t>(std::stoi(token, nullptr, 16));
                    pattern.push_back(byte);
                    mask.push_back('x');
                } catch (const std::exception& e) {
                    utils::ErrorHandler::GetInstance()->warning(
                        "Error parsing pattern token: " + token + " - " + e.what() + ", using wildcard",
                        utils::ErrorCategory::SYSTEM,
                        __FUNCTION__, __FILE__, __LINE__
                    );
                    // Use wildcard for invalid tokens
                    pattern.push_back(0);
                    mask.push_back('?');
                }
            }
        }
        
        utils::ErrorHandler::GetInstance()->debug(
            "Parsed pattern string: " + patternString + " -> " + std::to_string(pattern.size()) + " bytes",
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
        
    } catch (const std::exception& e) {
        utils::ErrorHandler::GetInstance()->error(
            "Exception during pattern string parsing: " + std::string(e.what()),
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
    }
    
    return {pattern, mask};
}

std::vector<PatternScanResult> PatternScanner::ScanForPattern(
    const std::vector<uint8_t>& pattern,
    const std::string& mask,
    const std::string& name,
    const std::string& moduleName) {
    
    // Start performance monitoring for pattern scanning
    auto scan_operation = utils::PerformanceMonitor::GetInstance()->start_operation("pattern_scanning");
    
    // Set error context for pattern scanning
    utils::ErrorContext context;
    context.set("operation", "pattern_scanning");
    context.set("component", "PatternScanner");
    context.set("pattern_name", name);
    context.set("module_name", moduleName);
    utils::ErrorHandler::GetInstance()->set_error_context(context);
    
    std::vector<PatternScanResult> results;
    
    if (pattern.empty() || mask.empty() || pattern.size() != mask.size()) {
        utils::ErrorHandler::GetInstance()->error(
            "Invalid pattern or mask",
            utils::ErrorCategory::SYSTEM,
            __FUNCTION__, __FILE__, __LINE__
        );
        utils::PerformanceMonitor::GetInstance()->end_operation(scan_operation);
        return results;
    }
    
    int totalRegions = static_cast<int>(m_memoryRegions.size());
    int processedRegions = 0;
    
    utils::ErrorHandler::GetInstance()->info(
        "Starting pattern scan for '" + name + "' in " + std::to_string(totalRegions) + " memory regions",
        utils::ErrorCategory::SYSTEM,
        __FUNCTION__, __FILE__, __LINE__
    );
    
    // Scan each memory region
    for (const auto& region : m_memoryRegions) {
        // Skip regions that don't belong to the specified module if a module name is provided
        if (!moduleName.empty() && region.name != moduleName) {
            continue;
        }
        
        // Skip regions that don't have read access
        if (!(region.protection & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE))) {
            continue;
        }
        
        // Report progress
        if (m_progressCallback) {
            int progress = static_cast<int>((static_cast<float>(processedRegions++) / totalRegions) * 100);
            m_progressCallback(progress);
        }
        
        try {
            // Perform Boyer-Moore-Horspool search
            std::vector<void*> addresses = BoyerMooreHorspoolSearch(
                static_cast<const uint8_t*>(region.baseAddress),
                region.size,
                pattern,
                mask
            );
            
            // Convert to scan results
            for (void* address : addresses) {
                PatternScanResult result;
                result.address = address;
                result.patternName = name;
                result.confidence = 100; // Exact match
                results.push_back(result);
            }
            
            if (!addresses.empty()) {
                utils::ErrorHandler::GetInstance()->debug(
                    "Found " + std::to_string(addresses.size()) + " matches in region " + region.name,
                    utils::ErrorCategory::SYSTEM,
                    __FUNCTION__, __FILE__, __LINE__
                );
            }
            
        } catch (const std::exception& e) {
            utils::ErrorHandler::GetInstance()->error(
                "Exception scanning region at " + std::to_string(reinterpret_cast<uintptr_t>(region.baseAddress)) +
                ": " + e.what(),
                utils::ErrorCategory::SYSTEM,
                __FUNCTION__, __FILE__, __LINE__
            );
            // Continue with the next region
        }
    }
    
    // Final progress update
    if (m_progressCallback) {
        m_progressCallback(100);
    }
    
    utils::ErrorHandler::GetInstance()->info(
        "Pattern scan completed for '" + name + "': " + std::to_string(results.size()) + " matches found",
        utils::ErrorCategory::SYSTEM,
        __FUNCTION__, __FILE__, __LINE__
    );
    
    // End performance monitoring
    utils::PerformanceMonitor::GetInstance()->end_operation(scan_operation);
    
    // Clear error context
    utils::ErrorHandler::GetInstance()->clear_error_context();
    
    return results;
}

std::vector<PatternScanResult> PatternScanner::ScanForPatternString(
    const std::string& patternString,
    const std::string& name,
    const std::string& moduleName) {
    
    auto [pattern, mask] = ParsePatternString(patternString);
    return ScanForPattern(pattern, mask, name, moduleName);
}

std::unordered_map<std::string, std::vector<PatternScanResult>> PatternScanner::ScanForPatterns(
    const std::vector<std::tuple<std::vector<uint8_t>, std::string, std::string>>& patterns,
    const std::string& moduleName) {
    
    std::unordered_map<std::string, std::vector<PatternScanResult>> results;
    
    int totalRegions = static_cast<int>(m_memoryRegions.size());
    int processedRegions = 0;
    
    // Scan each memory region
    for (const auto& region : m_memoryRegions) {
        // Skip regions that don't belong to the specified module if a module name is provided
        if (!moduleName.empty() && region.name != moduleName) {
            continue;
        }
        
        // Skip regions that don't have read access
        if (!(region.protection & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE))) {
            continue;
        }
        
        // Report progress
        if (m_progressCallback) {
            int progress = static_cast<int>((static_cast<float>(processedRegions++) / totalRegions) * 100);
            m_progressCallback(progress);
        }
        
        // Get pointer to memory data
        const uint8_t* data = static_cast<const uint8_t*>(region.baseAddress);
        size_t dataSize = region.size;
        
        // Search for each pattern in this region
        for (const auto& [pattern, mask, name] : patterns) {
            if (pattern.empty() || mask.empty() || pattern.size() != mask.size()) {
                continue;
            }
            
            try {
                // Perform Boyer-Moore-Horspool search
                std::vector<void*> addresses = BoyerMooreHorspoolSearch(
                    data,
                    dataSize,
                    pattern,
                    mask
                );
                
                // Convert to scan results and add to results map
                for (void* address : addresses) {
                    PatternScanResult result;
                    result.address = address;
                    result.patternName = name;
                    result.confidence = 100; // Exact match
                    results[name].push_back(result);
                }
            } catch (const std::exception& e) {
                utils::ErrorHandler::GetInstance()->error(
                    "Exception scanning region at " + std::to_string(reinterpret_cast<uintptr_t>(region.baseAddress)) +
                    " for pattern " + name + ": " + e.what(),
                    utils::ErrorCategory::SYSTEM,
                    __FUNCTION__, __FILE__, __LINE__
                );
                // Continue with the next pattern
            }
        }
    }
    
    // Final progress update
    if (m_progressCallback) {
        m_progressCallback(100);
    }
    
    return results;
}

std::vector<void*> PatternScanner::BoyerMooreHorspoolSearch(
    const uint8_t* data,
    size_t dataSize,
    const std::vector<uint8_t>& pattern,
    const std::string& mask) {
    
    std::vector<void*> results;
    
    if (!data || dataSize == 0 || pattern.empty() || mask.empty() || pattern.size() != mask.size()) {
        return results;
    }
    
    const size_t patternSize = pattern.size();
    
    // Create the bad character table
    const int alphabetSize = 256;
    std::vector<size_t> badChar(alphabetSize, patternSize);
    
    for (size_t i = 0; i < patternSize - 1; i++) {
        if (mask[i] != '?') {
            badChar[pattern[i]] = patternSize - 1 - i;
        }
    }
    
    // Boyer-Moore-Horspool search
    size_t i = 0;
    while (i <= dataSize - patternSize) {
        size_t j = patternSize - 1;
        
        // Check pattern from right to left
        while (j != static_cast<size_t>(-1) && (mask[j] == '?' || pattern[j] == data[i + j])) {
            j--;
        }
        
        // Pattern found
        if (j == static_cast<size_t>(-1)) {
            results.push_back(const_cast<uint8_t*>(data + i));
        }
        
        // Shift based on bad character rule
        size_t shift = badChar[data[i + patternSize - 1]];
        i += shift;
    }
    
    return results;
}

std::vector<std::pair<void*, int>> PatternScanner::FuzzyPatternMatch(
    const uint8_t* data,
    size_t dataSize,
    const std::vector<uint8_t>& pattern,
    int maxDistance) {
    
    std::vector<std::pair<void*, int>> results;
    
    if (!data || dataSize == 0 || pattern.empty() || maxDistance < 0) {
        return results;
    }
    
    // First do an exact search to find candidates
    std::vector<void*> exactMatches = BoyerMooreHorspoolSearch(
        data,
        dataSize,
        pattern,
        std::string(pattern.size(), 'x') // All bytes must match exactly
    );
    
    // For each exact match, calculate the confidence score
    for (void* matchAddr : exactMatches) {
        results.emplace_back(matchAddr, 100); // 100% confidence for exact matches
    }
    
    // If no exact matches and fuzzy matching is requested, do some approximate matching
    if (exactMatches.empty() && maxDistance > 0) {
        // This is a simplified approach - for real fuzzy matching we would use
        // a more sophisticated algorithm like Levenshtein distance or Smith-Waterman
        
        // For now, allow a sliding window approach that counts matching bytes
        for (size_t i = 0; i <= dataSize - pattern.size(); i++) {
            int mismatches = 0;
            
            for (size_t j = 0; j < pattern.size(); j++) {
                if (data[i + j] != pattern[j]) {
                    mismatches++;
                    if (mismatches > maxDistance) {
                        break;
                    }
                }
            }
            
            if (mismatches <= maxDistance) {
                // Calculate confidence score (0-100)
                int confidence = 100 - static_cast<int>((static_cast<float>(mismatches) / pattern.size()) * 100);
                results.emplace_back(const_cast<uint8_t*>(data + i), confidence);
            }
        }
    }
    
    return results;
}

} // namespace DXHook
} // namespace UndownUnlock 