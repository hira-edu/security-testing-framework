#include "utils/memory_tracker.h"

#include <algorithm>\\n#include <chrono>

namespace utils {

namespace {
std::mutex g_tracker_mutex;
MemoryTracker* g_tracker = nullptr;
}

MemoryTracker::MemoryTracker()
    : initialized_(true), next_id_(1) {
    statistics_ = MemoryStatistics{};
}

void MemoryTracker::Initialize() {
    std::lock_guard<std::mutex> lock(g_tracker_mutex);
    if (!g_tracker) {
        g_tracker = new MemoryTracker();
    }
}

void MemoryTracker::Shutdown() {
    std::lock_guard<std::mutex> lock(g_tracker_mutex);
    delete g_tracker;
    g_tracker = nullptr;
}

MemoryTracker* MemoryTracker::GetInstance() {
    std::lock_guard<std::mutex> lock(g_tracker_mutex);
    if (!g_tracker) {
        g_tracker = new MemoryTracker();
    }
    return g_tracker;
}

bool MemoryTracker::is_initialized() const {
    return initialized_;
}

void MemoryTracker::Reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    allocations_.clear();
    statistics_ = MemoryStatistics{};
    next_id_.store(1, std::memory_order_relaxed);
}

std::uint64_t MemoryTracker::track_allocation(const std::string& tag,
                                              std::size_t size,
                                              MemoryCategory category) {
    auto id = next_id_.fetch_add(1, std::memory_order_relaxed);
    AllocationRecord record;
    record.id = id;
    record.tag = tag;
    record.size = size;
    record.category = category;
    record.timestamp = std::chrono::system_clock::now();
    record.active = true;

    std::lock_guard<std::mutex> lock(mutex_);
    allocations_[id] = record;
    statistics_.total_allocations += 1;
    statistics_.active_allocations += 1;
    statistics_.active_bytes += size;
    statistics_.peak_bytes = std::max(statistics_.peak_bytes, statistics_.active_bytes);
    return id;
}

void MemoryTracker::release_allocation(std::uint64_t id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = allocations_.find(id);
    if (it == allocations_.end()) {
        return;
    }
    if (it->second.active) {
        statistics_.active_bytes -= it->second.size;
        if (statistics_.active_allocations > 0) {
            statistics_.active_allocations -= 1;
        }
        statistics_.total_releases += 1;
        it->second.active = false;
    }
}

bool MemoryTracker::has_allocation(std::uint64_t id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = allocations_.find(id);
    return it != allocations_.end() && it->second.active;
}

bool MemoryTracker::has_leaks() const {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& entry : allocations_) {
        if (entry.second.active) {
            return true;
        }
    }
    return false;
}

MemoryStatistics MemoryTracker::get_statistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return statistics_;
}

}  // namespace utils
