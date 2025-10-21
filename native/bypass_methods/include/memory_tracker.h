#pragma once

#include <string>
#include <unordered_map>
#include <utility>

#include "utils/memory_tracker.h"

using MemoryCategory = utils::MemoryCategory;
using MemoryStatistics = utils::MemoryStatistics;

class MemoryTracker {
public:
    explicit MemoryTracker(std::string component = "")
        : component_(std::move(component)) {}

    static MemoryTracker& GetInstance() {
        static MemoryTracker instance;
        return instance;
    }

    static void Initialize() { utils::MemoryTracker::Initialize(); }
    static void Shutdown() { utils::MemoryTracker::Shutdown(); }

    bool IsInitialized() const {
        auto* tracker = utils::MemoryTracker::GetInstance();
        return tracker && tracker->is_initialized();
    }

    void Reset() {
        utils::MemoryTracker::GetInstance()->Reset();
        tag_to_id_.clear();
    }

    std::uint64_t TrackAllocation(const std::string& tag,
                                  std::size_t size,
                                  MemoryCategory category = MemoryCategory::GENERAL) {
        auto qualified = qualify(tag);
        auto id = utils::MemoryTracker::GetInstance()->track_allocation(qualified, size, category);
        tag_to_id_[qualified] = id;
        return id;
    }

    void TrackDeallocation(const std::string& tag) {
        auto qualified = qualify(tag);
        auto it = tag_to_id_.find(qualified);
        if (it != tag_to_id_.end()) {
            utils::MemoryTracker::GetInstance()->release_allocation(it->second);
            tag_to_id_.erase(it);
        }
    }

    bool HasAllocation(std::uint64_t id) const {
        return utils::MemoryTracker::GetInstance()->has_allocation(id);
    }

    bool HasLeaks() const {
        return utils::MemoryTracker::GetInstance()->has_leaks();
    }

    MemoryStatistics GetStatistics() const {
        return utils::MemoryTracker::GetInstance()->get_statistics();
    }

private:
    std::string qualify(const std::string& tag) const {
        if (component_.empty()) {
            return tag;
        }
        return component_ + ":" + tag;
    }

    std::string component_;
    mutable std::unordered_map<std::string, std::uint64_t> tag_to_id_;
};
