#include "../../include/signatures/dx_signatures.h"
#include "../../include/raii_wrappers.h"
#include "../../include/error_handler.h"
#include "../../include/memory_tracker.h"
#include "../../include/performance_monitor.h"
#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>

namespace UndownUnlock {
namespace DXHook {
namespace Signatures {

// Performance monitoring for LockDown signature operations
static PerformanceMonitor g_lockdownMonitor("LockDownSignatures");

// Memory tracking for LockDown signature resources
static MemoryTracker g_lockdownMemory("LockDownSignatures");

/**
 * @brief Structure to hold LockDown Browser signatures by version
 */
struct LockDownSignatures {
    std::string version;
    std::vector<SignaturePattern> patterns;
};

/**
 * @brief Get signatures for different versions of LockDown Browser
 * @return Vector of version-specific signature sets
 */
std::vector<LockDownSignatures> GetVersionedLockDownSignatures() {
    auto timer = g_lockdownMonitor.StartTimer("GetVersionedLockDownSignatures");
    
    try {
        std::vector<LockDownSignatures> versionedSignatures;
        
        // Track memory allocation for versioned signatures
        g_lockdownMemory.TrackAllocation("VersionedSignatures", sizeof(std::vector<LockDownSignatures>));
        
        // LockDown Browser 2.0.x signatures
        LockDownSignatures v2_0 = {
            "2.0.x",
            {
                // Anti-screen capture check
                {
                    "ScreenCaptureCheck_2_0",
                    ParsePattern("48 83 EC 28 33 C0 48 85 C9 74 20 48 8B 01 FF 50 10 84 C0 74 16 B8 01 00 00 00").first,
                    ParsePattern("48 83 EC 28 33 C0 48 85 C9 74 20 48 8B 01 FF 50 10 84 C0 74 16 B8 01 00 00 00").second,
                    "LockDownBrowser.exe",
                    "Main screen capture detection routine (version 2.0.x)"
                },
                
                // Window focus check
                {
                    "WindowFocusCheck_2_0",
                    ParsePattern("48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 20 33 FF 48 8B F1 48 8B 0D").first,
                    ParsePattern("48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 20 33 FF 48 8B F1 48 8B 0D").second,
                    "LockDownBrowser.exe",
                    "Window focus verification routine (version 2.0.x)"
                },
                
                // Process enumeration
                {
                    "ProcessEnum_2_0",
                    ParsePattern("48 89 5C 24 08 48 89 74 24 10 48 89 7C 24 18 55 41 54 41 55 41 56 41 57 48 8D AC 24").first,
                    ParsePattern("48 89 5C 24 08 48 89 74 24 10 48 89 7C 24 18 55 41 54 41 55 41 56 41 57 48 8D AC 24").second,
                    "LockDownBrowser.exe",
                    "Process enumeration routine (version 2.0.x)"
                }
            }
        };
        versionedSignatures.push_back(v2_0);
        
        // LockDown Browser 2.1.x signatures
        LockDownSignatures v2_1 = {
            "2.1.x",
            {
                // Anti-screen capture check (updated for 2.1.x)
                {
                    "ScreenCaptureCheck_2_1",
                    ParsePattern("48 89 4C 24 08 48 83 EC 38 48 8B 05 ? ? ? ? 48 85 C0 74 ? 48 8B 08 48 8B 01 FF 50 ? 84 C0").first,
                    ParsePattern("48 89 4C 24 08 48 83 EC 38 48 8B 05 ? ? ? ? 48 85 C0 74 ? 48 8B 08 48 8B 01 FF 50 ? 84 C0").second,
                    "LockDownBrowser.exe",
                    "Main screen capture detection routine (version 2.1.x)"
                },
                
                // Window focus check (updated for 2.1.x)
                {
                    "WindowFocusCheck_2_1",
                    ParsePattern("48 83 EC 28 FF 15 ? ? ? ? 48 85 C0 74 ? 48 83 C4 28 C3").first,
                    ParsePattern("48 83 EC 28 FF 15 ? ? ? ? 48 85 C0 74 ? 48 83 C4 28 C3").second,
                    "LockDownBrowser.exe",
                    "Window focus verification routine (version 2.1.x)"
                },
                
                // Browser rendering hook check
                {
                    "RenderHookCheck_2_1",
                    ParsePattern("40 53 48 83 EC 20 48 8B D9 E8 ? ? ? ? 33 D2 48 8B C8 E8 ? ? ? ? 48 8B C8 E8").first,
                    ParsePattern("40 53 48 83 EC 20 48 8B D9 E8 ? ? ? ? 33 D2 48 8B C8 E8 ? ? ? ? 48 8B C8 E8").second,
                    "LockDownBrowser.exe",
                    "Browser rendering hook detection routine (version 2.1.x)"
                }
            }
        };
        versionedSignatures.push_back(v2_1);
        
        // LockDown Browser 2.2.x signatures 
        LockDownSignatures v2_2 = {
            "2.2.x",
            {
                // Anti-screen capture check (updated for 2.2.x)
                {
                    "ScreenCaptureCheck_2_2",
                    ParsePattern("48 83 EC 48 48 C7 44 24 ? ? ? ? ? 48 89 5C 24 ? 48 89 74 24 ? 48 89 7C 24 ? 48 8B 05").first,
                    ParsePattern("48 83 EC 48 48 C7 44 24 ? ? ? ? ? 48 89 5C 24 ? 48 89 74 24 ? 48 89 7C 24 ? 48 8B 05").second,
                    "LockDownBrowser.exe",
                    "Main screen capture detection routine (version 2.2.x)"
                },
                
                // Memory integrity check
                {
                    "MemoryIntegrityCheck_2_2",
                    ParsePattern("40 53 48 83 EC 20 48 8B D9 48 85 D2 74 ? 48 8B 42 ? 48 85 C0 74 ? 48 8B 48 ? 48 85 C9").first,
                    ParsePattern("40 53 48 83 EC 20 48 8B D9 48 85 D2 74 ? 48 8B 42 ? 48 85 C0 74 ? 48 8B 48 ? 48 85 C9").second,
                    "LockDownBrowser.exe",
                    "Memory integrity check routine (version 2.2.x)"
                },
                
                // Direct3D hook detection
                {
                    "D3DHookCheck_2_2",
                    ParsePattern("48 8B 01 FF 50 ? 48 85 C0 74 ? 48 8B 10 48 8B C8 FF 52 ? 85 C0 74 ? B8 01 00 00 00").first,
                    ParsePattern("48 8B 01 FF 50 ? 48 85 C0 74 ? 48 8B 10 48 8B C8 FF 52 ? 85 C0 74 ? B8 01 00 00 00").second,
                    "LockDownBrowser.exe",
                    "Direct3D hook detection routine (version 2.2.x)"
                }
            }
        };
        versionedSignatures.push_back(v2_2);
        
        ErrorHandler::LogInfo(ErrorCategory::SIGNATURE_PARSING,
                            "Versioned LockDown signatures loaded successfully",
                            {{"VersionCount", std::to_string(versionedSignatures.size())}});
        
        timer.Stop();
        g_lockdownMonitor.RecordOperation("GetVersionedLockDownSignatures", timer.GetElapsedTime());
        
        return versionedSignatures;
        
    } catch (const std::exception& e) {
        timer.Stop();
        ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::EXCEPTION,
                             "Exception during versioned LockDown signature loading",
                             {{"Exception", e.what()},
                              {"Operation", "GetVersionedLockDownSignatures"}});
        throw;
    }
}

// Get all LockDown Browser signatures as a flat list
std::vector<SignaturePattern> GetLockDownSignatures() {
    auto timer = g_lockdownMonitor.StartTimer("GetLockDownSignatures");
    
    try {
        std::vector<SignaturePattern> allSignatures;
        
        // Track memory allocation for all signatures
        g_lockdownMemory.TrackAllocation("AllSignatures", sizeof(std::vector<SignaturePattern>));
        
        // Get versioned signatures and flatten them
        auto versionedSignatures = GetVersionedLockDownSignatures();
        for (const auto& versionSig : versionedSignatures) {
            for (const auto& sig : versionSig.patterns) {
                allSignatures.push_back(sig);
            }
        }
        
        ErrorHandler::LogInfo(ErrorCategory::SIGNATURE_PARSING,
                            "LockDown signatures flattened successfully",
                            {{"TotalSignatureCount", std::to_string(allSignatures.size())}});
        
        timer.Stop();
        g_lockdownMonitor.RecordOperation("GetLockDownSignatures", timer.GetElapsedTime());
        
        return allSignatures;
        
    } catch (const std::exception& e) {
        timer.Stop();
        ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::EXCEPTION,
                             "Exception during LockDown signature flattening",
                             {{"Exception", e.what()},
                              {"Operation", "GetLockDownSignatures"}});
        throw;
    }
}

// Get signatures for anti-detection countermeasures
std::vector<SignaturePattern> GetAntiDetectionSignatures() {
    auto timer = g_lockdownMonitor.StartTimer("GetAntiDetectionSignatures");
    
    try {
        std::vector<SignaturePattern> signatures;
        
        // Track memory allocation for anti-detection signatures
        g_lockdownMemory.TrackAllocation("AntiDetectionSignatures", sizeof(std::vector<SignaturePattern>));
        
        // Timing check signatures
        signatures.push_back({
            "TimingCheck",
            ParsePattern("48 8B 05 ? ? ? ? FF D0 48 8B D8 48 8B 05 ? ? ? ? FF D0 48 2B C3").first,
            ParsePattern("48 8B 05 ? ? ? ? FF D0 48 8B D8 48 8B 05 ? ? ? ? FF D0 48 2B C3").second,
            "LockDownBrowser.exe",
            "Performance timing check for anti-debug"
        });
        
        // Integrity check signatures
        signatures.push_back({
            "IntegrityCheck",
            ParsePattern("48 89 5C 24 ? 48 89 74 24 ? 57 48 83 EC 20 48 8B F9 48 8B CA 48 8B D1 E8 ? ? ? ? 84 C0").first,
            ParsePattern("48 89 5C 24 ? 48 89 74 24 ? 57 48 83 EC 20 48 8B F9 48 8B CA 48 8B D1 E8 ? ? ? ? 84 C0").second,
            "LockDownBrowser.exe",
            "Code integrity verification routine"
        });
        
        // Hook detection signatures
        signatures.push_back({
            "HookDetection",
            ParsePattern("48 8B 01 FF 90 ? ? ? ? 84 C0 74 ? 48 8B 03 48 8B CB FF 50 ? 84 C0 74 ? B0 01").first,
            ParsePattern("48 8B 01 FF 90 ? ? ? ? 84 C0 74 ? 48 8B 03 48 8B CB FF 50 ? 84 C0 74 ? B0 01").second,
            "LockDownBrowser.exe",
            "API/function hooking detection"
        });
        
        ErrorHandler::LogInfo(ErrorCategory::SIGNATURE_PARSING,
                            "Anti-detection signatures loaded successfully",
                            {{"SignatureCount", std::to_string(signatures.size())}});
        
        timer.Stop();
        g_lockdownMonitor.RecordOperation("GetAntiDetectionSignatures", timer.GetElapsedTime());
        
        return signatures;
        
    } catch (const std::exception& e) {
        timer.Stop();
        ErrorHandler::LogError(ErrorSeverity::ERROR, ErrorCategory::EXCEPTION,
                             "Exception during anti-detection signature loading",
                             {{"Exception", e.what()},
                              {"Operation", "GetAntiDetectionSignatures"}});
        throw;
    }
}

} // namespace Signatures
} // namespace DXHook
} // namespace UndownUnlock 