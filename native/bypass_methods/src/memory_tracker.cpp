#include "include/memory_tracker.h"

#include <algorithm>

namespace {
std::mutex g_memory_tracker_instance_mutex;
MemoryTracker* g_memory_tracker_instance = nullptr;
} // namespace

MemoryTracker::MemoryTracker()
    : MemoryTracker("") {}

MemoryTracker::MemoryTracker(std::string component)
    : initialized_(true),
      next_id_(1),
      native_tracker_(&utils::MemoryTracker::get_instance()),
      component_(std::move(component)) {
    statistics_ = {};
}

void MemoryTracker::Initialize() {
    std::lock_guard<std::mutex> lock(g_memory_tracker_instance_mutex);
    if (!g_memory_tracker_instance) {
        g_memory_tracker_instance = new MemoryTracker();
    } else {
        g_memory_tracker_instance->initialized_ = true;
        g_memory_tracker_instance->Reset();
    }
    (void)utils::MemoryTracker::get_instance();
}

void MemoryTracker::Shutdown() {
    std::lock_guard<std::mutex> lock(g_memory_tracker_instance_mutex);
    delete g_memory_tracker_instance;
    g_memory_tracker_instance = nullptr;
}

MemoryTracker& MemoryTracker::GetInstance() {
    std::lock_guard<std::mutex> lock(g_memory_tracker_instance_mutex);
    if (!g_memory_tracker_instance) {
        g_memory_tracker_instance = new MemoryTracker();
    }
    return *g_memory_tracker_instance;
}

bool MemoryTracker::is_initialized() const {
    return initialized_;
}

void MemoryTracker::Reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    allocations_.clear();
    allocation_ids_by_name_.clear();
    statistics_ = {};
    next_id_.store(1, std::memory_order_relaxed);
}

std::uint64_t MemoryTracker::TrackAllocation(const std::string& name,
                                             std::size_t size,
                                             MemoryCategory category) {
    auto id = next_id_.fetch_add(1, std::memory_order_relaxed);
    auto now = std::chrono::system_clock::now();
    auto qualified = qualify(name);

    std::lock_guard<std::mutex> lock(mutex_);

    AllocationRecord record;
    record.id = id;
    record.name = qualified;
    record.size = size;
    record.category = category;
    record.timestamp = now;
    record.active = true;

    allocations_[id] = record;
    allocation_ids_by_name_[qualified].push_back(id);

    statistics_.total_allocations++;
    statistics_.active_allocations++;
    statistics_.active_bytes += size;
    statistics_.peak_bytes = std::max(statistics_.peak_bytes, statistics_.active_bytes);
    statistics_.peak_allocations = std::max(statistics_.peak_allocations, statistics_.active_allocations);

    return id;
}

void MemoryTracker::TrackDeallocation(const std::string& name) {
    auto qualified = qualify(name);

    std::lock_guard<std::mutex> lock(mutex_);
    auto ids_it = allocation_ids_by_name_.find(qualified);
    if (ids_it == allocation_ids_by_name_.end()) {
        return;
    }

    for (auto id : ids_it->second) {
        auto alloc_it = allocations_.find(id);
        if (alloc_it != allocations_.end() && alloc_it->second.active) {
            alloc_it->second.active = false;
            statistics_.total_releases++;
            if (statistics_.active_allocations > 0) {
                statistics_.active_allocations--;
            }
            if (statistics_.active_bytes >= alloc_it->second.size) {
                statistics_.active_bytes -= alloc_it->second.size;
            } else {
                statistics_.active_bytes = 0;
            }
            break;
        }
    }
}

void MemoryTracker::ReleaseAllocation(std::uint64_t id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto alloc_it = allocations_.find(id);
    if (alloc_it == allocations_.end() || !alloc_it->second.active) {
        return;
    }

    AllocationRecord& record = alloc_it->second;
    record.active = false;

    statistics_.total_releases++;
    if (statistics_.active_allocations > 0) {
        statistics_.active_allocations--;
    }
    if (statistics_.active_bytes >= record.size) {
        statistics_.active_bytes -= record.size;
    } else {
        statistics_.active_bytes = 0;
    }

    auto ids_it = allocation_ids_by_name_.find(record.name);
    if (ids_it != allocation_ids_by_name_.end()) {
        auto& ids = ids_it->second;
        ids.erase(std::remove(ids.begin(), ids.end(), id), ids.end());
        if (ids.empty()) {
            allocation_ids_by_name_.erase(ids_it);
        }
    }
}

bool MemoryTracker::HasAllocation(std::uint64_t id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = allocations_.find(id);
    return it != allocations_.end() && it->second.active;
}

bool MemoryTracker::HasLeaks() const {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& pair : allocations_) {
        if (pair.second.active) {
            return true;
        }
    }
    return false;
}

MemoryStatistics MemoryTracker::GetStatistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return statistics_;
}

std::size_t MemoryTracker::GetTotalAllocated() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return statistics_.active_bytes;
}

std::vector<AllocationRecord> MemoryTracker::GetAllocations() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<AllocationRecord> records;
    records.reserve(allocations_.size());
    for (const auto& pair : allocations_) {
        records.push_back(pair.second);
    }
    return records;
}

std::vector<AllocationRecord> MemoryTracker::GetLeaks() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<AllocationRecord> leaks;
    for (const auto& pair : allocations_) {
        if (pair.second.active) {
            leaks.push_back(pair.second);
        }
    }
    return leaks;
}

void MemoryTracker::finalize_allocation_locked(std::uint64_t) {}

std::string MemoryTracker::qualify(const std::string& name) const {
    if (component_.empty()) {
        return name;
    }
    return component_ + ":" + name;
}
