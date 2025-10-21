#include "../../include/signatures/lockdown_signatures.h"
#include "../../include/memory/pattern_scanner.h" // For PatternScanner::ParsePatternString
#include <iostream>
#include <vector>
#include <iomanip> // For std::hex, std::setw, std::setfill
#include <algorithm> // For std::min

namespace UndownUnlock {
namespace Signatures {

// Static database of LockDown Browser related signatures
// Using the SignatureInfo struct defined in lockdown_signatures.h
static const std::vector<SignatureInfo> g_internalLockdownSignatures = {
    {
        "LDB_CheckWindowFocus",                                 // name
        "55 8B EC 83 E4 F8 81 EC ?? ?? ?? ?? A1 ?? ?? ?? ??",   // idaPattern
        0,                                                      // searchOffset
        0                                                       // resultOffset
    },
    {
        "LDB_IsScreenshotAllowed",                              // name
        "8B FF 55 8B EC 83 EC 10 A1 ?? ?? ?? ?? 33 C5 89 45 FC",// idaPattern
        0,
        0
    },
    {
        "LDB_VirtualMachineDetection",                          // name
        // Example pattern that is shorter and has a clear non-wildcard part for testing BMH-like logic
        "40 53 48 83 EC 20 48 ?? D9 E8 ?? ?? 00 00 48",         // idaPattern
        0,
        0
    }
};

std::vector<SignatureInfo> GetLockdownSignatures() {
    return g_internalLockdownSignatures;
}

// Helper function for manual pattern matching (for testing purposes)
bool ManualSearch(const std::vector<uint8_t>& data,
                  const std::vector<uint8_t>& pattern,
                  const std::string& mask,
                  size_t& foundOffset) {
    if (pattern.empty() || data.size() < pattern.size()) {
        return false;
    }
    for (size_t i = 0; i <= data.size() - pattern.size(); ++i) {
        bool match = true;
        for (size_t j = 0; j < pattern.size(); ++j) {
            if (mask[j] == 'x' && data[i + j] != pattern[j]) {
                match = false;
                break;
            }
        }
        if (match) {
            foundOffset = i;
            return true;
        }
    }
    return false;
}


// Test function implementation
// The 'scanner' parameter is a bit problematic for a self-contained unit test of patterns
// against a local byte array, because PatternScanner::ScanForPattern operates on its internal
// m_memoryRegions. We'll use scanner for ParsePatternString (static) and do manual search.
void TestLockdownSignatures(const DXHook::PatternScanner& scanner) {
    std::cout << "\n--- Testing LockDown Browser Signatures ---" << std::endl;

    // Define a sample memory block.
    // Embed "LDB_CheckWindowFocus": "55 8B EC 83 E4 F8 81 EC ?? ?? ?? ?? A1 ?? ?? ?? ??"
    // Actual:                          55 8B EC 83 E4 F8 81 EC DE AD BE EF A1 12 34 56 78
    std::vector<uint8_t> testMemoryBlock = {
        0xCA, 0xFE, 0xBA, 0xBE,                                 // Prefix
        0x55, 0x8B, 0xEC, 0x83, 0xE4, 0xF8, 0x81, 0xEC,         // LDB_CheckWindowFocus part 1
        0xDE, 0xAD, 0xBE, 0xEF,                                 // Placeholder for ?? ?? ?? ??
        0xA1,                                                   // A1
        0x12, 0x34, 0x56, 0x78,                                 // Placeholder for ?? ?? ?? ??
        0xF0, 0x0D,                                             // Suffix
        // Embed "LDB_VirtualMachineDetection": "40 53 48 83 EC 20 48 ?? D9 E8 ?? ?? 00 00 48"
        // Actual:                               40 53 48 83 EC 20 48 FF D9 E8 AA BB 00 00 48
        0xDE, 0xCO, 0xDE,                                       // Some more prefix
        0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x48,               // LDB_VirtualMachineDetection part 1
        0xFF,                                                   // Placeholder for ?? (e.g. a register like B8+r)
        0xD9, 0xE8,                                             // D9 E8
        0xAA, 0xBB,                                             // Placeholder for ?? ??
        0x00, 0x00, 0x48                                        // 00 00 48
    };

    std::cout << "Test Memory Block (size " << testMemoryBlock.size() << "): ";
    for(size_t i = 0; i < std::min((size_t)32, testMemoryBlock.size()); ++i) { // Print first 32 bytes
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)testMemoryBlock[i] << " ";
    }
    std::cout << "..." << std::dec << std::endl;

    auto signaturesToTest = GetLockdownSignatures();

    for (const auto& sigInfo : signaturesToTest) {
        std::cout << "\nTesting signature: '" << sigInfo.name << "' (Pattern: " << sigInfo.idaPattern << ")" << std::endl;

        auto parsedPair = DXHook::PatternScanner::ParsePatternString(sigInfo.idaPattern);
        const std::vector<uint8_t>& patternBytes = parsedPair.first;
        const std::string& mask = parsedPair.second;

        if (patternBytes.empty()) {
            std::cout << "  -> Failed to parse pattern string." << std::endl;
            continue;
        }

        std::cout << "  Parsed (" << patternBytes.size() << " bytes): ";
        for(size_t i = 0; i < patternBytes.size(); ++i) {
            if (mask[i] == '?') std::cout << "?? ";
            else std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)patternBytes[i] << " ";
        }
        std::cout << std::dec << std::endl;

        // Perform a manual search on our local testMemoryBlock
        size_t foundOffset = 0;
        bool foundInTestBlock = ManualSearch(testMemoryBlock, patternBytes, mask, foundOffset);

        if (foundInTestBlock) {
            std::cout << "  -> FOUND in local test block at offset: " << foundOffset
                      << " (0x" << std::hex << foundOffset << std::dec << ")." << std::endl;
        } else {
            std::cout << "  -> NOT FOUND in local test block." << std::endl;
        }

        // Note on using the passed 'scanner' instance:
        // The PatternScanner::ScanForPattern method searches within its own initialized memory regions.
        // To test against 'testMemoryBlock' using the 'scanner' instance, one would typically need to:
        // 1. Ensure 'scanner' is not const.
        // 2. Call 'scanner.AddMemoryRegion({testMemoryBlock.data(), testMemoryBlock.size(), PAGE_READONLY, "TestBlock"})'.
        // 3. Call 'scanner.ScanForPattern(patternBytes, mask, sigInfo.name, "TestBlock")'.
        // 4. Remove the test region.
        // This is too complex for this simple test function's scope if 'scanner' is const or for one-off tests.
        // The manual search above serves to verify pattern processing for this task.
        std::cout << "  (Note: To use the provided 'PatternScanner' instance for this specific test block, "
                  << "it would need to be configured to scan this block.)" << std::endl;
    }
    std::cout << "\n--- LockDown Browser Signatures Test Complete ---" << std::endl;
}

} // namespace Signatures
} // namespace UndownUnlock
