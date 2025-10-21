#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace utils {

enum class MemoryCategory : std::uint8_t {
    GENERAL = 0,
    SYSTEM = 1,
    GRAPHICS = 2
};

struct MemoryStatistics {
    std::size_t active_allocations = 0;
    std::size_t total_allocations = 0;
    std::size_t total_releases = 0;
    std::size_t active_bytes = 0;
    std::size_t peak_bytes = 0;
};

class MemoryTracker {
public:
    static void Initialize();
    static void Shutdown();
    static MemoryTracker* GetInstance();

    bool is_initialized() const;
    void Reset();

    std::uint64_t track_allocation(const std::string& tag,
                                   std::size_t size,
                                   MemoryCategory category);
    void release_allocation(std::uint64_t id);
    bool has_allocation(std::uint64_t id) const;

    bool has_leaks() const;
    MemoryStatistics get_statistics() const;

private:
    MemoryTracker();

    struct AllocationRecord {
        std::uint64_t id = 0;
        std::string tag;
        std::size_t size = 0;
        MemoryCategory category = MemoryCategory::GENERAL;
        std::chrono::system_clock::time_point timestamp;
        bool active = false;
    };

    mutable std::mutex mutex_;
    bool initialized_;
    std::atomic<std::uint64_t> next_id_;
    std::unordered_map<std::uint64_t, AllocationRecord> allocations_;
    MemoryStatistics statistics_;
};

}  // namespace utils

