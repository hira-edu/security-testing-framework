#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>
#include <map>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

#include "utils/memory_tracker.h"

enum class MemoryCategory : std::uint8_t {
    GENERAL = 0,
    SYSTEM = 1,
    GRAPHICS = 2
};

struct AllocationRecord {
    std::uint64_t id = 0;
    std::string name;
    std::size_t size = 0;
    MemoryCategory category = MemoryCategory::GENERAL;
    std::chrono::system_clock::time_point timestamp;
    bool active = false;
};

struct MemoryStatistics {
    std::size_t active_allocations = 0;
    std::size_t total_allocations = 0;
    std::size_t total_releases = 0;
    std::size_t active_bytes = 0;
    std::size_t peak_bytes = 0;
    std::size_t peak_allocations = 0;
};

class MemoryTracker {
public:
    explicit MemoryTracker(std::string component = "");
    static void Initialize();
    static void Shutdown();
    static MemoryTracker& GetInstance();

    bool is_initialized() const;
    void Reset();

    std::uint64_t TrackAllocation(const std::string& name,
                                  std::size_t size,
                                  MemoryCategory category = MemoryCategory::GENERAL);
    void TrackDeallocation(const std::string& name);
    void ReleaseAllocation(std::uint64_t id);
    bool HasAllocation(std::uint64_t id) const;

    bool HasLeaks() const;
    MemoryStatistics GetStatistics() const;
    std::size_t GetTotalAllocated() const;
    std::vector<AllocationRecord> GetAllocations() const;
    std::vector<AllocationRecord> GetLeaks() const;

    // Legacy API compatibility helpers
    std::uint64_t track_allocation(const std::string& name,
                                   std::size_t size,
                                   MemoryCategory category = MemoryCategory::GENERAL) {
        return TrackAllocation(name, size, category);
    }

    void track_deallocation(const std::string& name) {
        TrackDeallocation(name);
    }

    void release_allocation(std::uint64_t id) {
        ReleaseAllocation(id);
    }

private:
    MemoryTracker();

    std::string qualify(const std::string& name) const;

    mutable std::mutex mutex_;
    bool initialized_;
    std::atomic<std::uint64_t> next_id_;
    std::unordered_map<std::uint64_t, AllocationRecord> allocations_;
    std::unordered_map<std::string, std::vector<std::uint64_t>> allocation_ids_by_name_;
    MemoryStatistics statistics_;
    utils::MemoryTracker* native_tracker_;
    std::string component_;
};
