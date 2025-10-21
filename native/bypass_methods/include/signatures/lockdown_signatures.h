#pragma once

#include <string>
#include <vector>
#include <cstdint> // For uint8_t if used in pattern directly, though string is fine

namespace UndownUnlock {
namespace Signatures {

struct SignatureInfo {
    std::string name;        // e.g., "LDB_CheckWindowFocus"
    std::string idaPattern;  // e.g., "55 8B EC 83 E4 F8 ?? ?? ?? ??"
    int searchOffset = 0;    // Offset from the found pattern to the actual function start or desired address
    int resultOffset = 0;    // If the found address needs further adjustment to point to the actual function start
                           // Often the pattern itself is designed to start at the function, so this might be 0.
                           // Or, if the pattern includes a JMP/CALL, this could be an offset from the pattern start
                           // to the instruction containing the relative address.
};

// Function to retrieve the list of defined LockDown Browser related signatures
std::vector<SignatureInfo> GetLockdownSignatures();

// Declaration for the test function (implementation will be in the .cpp)
// Forward declare PatternScanner if its full definition isn't needed here.
// However, since the test function is closely tied to it, including its header is fine.
// Assuming PatternScanner is in DXHook namespace based on previous files.
namespace DXHook { class PatternScanner; } // Forward declaration
void TestLockdownSignatures(const DXHook::PatternScanner& scanner);
// If PatternScanner is in a different namespace, adjust accordingly.
// For now, assuming UndownUnlock::DXHook::PatternScanner

} // namespace Signatures
} // namespace UndownUnlock
