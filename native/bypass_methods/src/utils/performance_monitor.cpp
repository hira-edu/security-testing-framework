#include "utils/performance_monitor.h"

#include <algorithm>\\n#include <deque>

namespace utils {

namespace {
std::mutex g_instance_mutex;
PerformanceMonitor* g_instance = nullptr;
constexpr std::size_t kMaxCompletedOperations = 1024;
}

PerformanceMonitor::PerformanceMonitor()
    : initialized_(true), next_operation_id_(1) {
    summary_ = PerformanceSummary{};
}

void PerformanceMonitor::Initialize() {
    std::lock_guard<std::mutex> lock(g_instance_mutex);
    if (!g_instance) {
        g_instance = new PerformanceMonitor();
    }
}

void PerformanceMonitor::Shutdown() {
    std::lock_guard<std::mutex> lock(g_instance_mutex);
    delete g_instance;
    g_instance = nullptr;
}

PerformanceMonitor* PerformanceMonitor::GetInstance() {
    std::lock_guard<std::mutex> lock(g_instance_mutex);
    if (!g_instance) {
        g_instance = new PerformanceMonitor();
    }
    return g_instance;
}

bool PerformanceMonitor::is_initialized() const {
    return initialized_;
}

void PerformanceMonitor::Reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    active_operations_.clear();
    completed_operations_.clear();
    completion_order_.clear();
    statistics_.clear();
    summary_ = PerformanceSummary{};
    next_operation_id_.store(1, std::memory_order_relaxed);
}

PerformanceMonitor::ScopedTimer PerformanceMonitor::StartTimer(const std::string& name) {
    return ScopedTimer(*GetInstance(), name);
}

std::size_t PerformanceMonitor::start_operation(const std::string& name) {
    auto id = next_operation_id_.fetch_add(1, std::memory_order_relaxed);
    OperationRecord record;
    record.name = name;
    record.start_time = std::chrono::steady_clock::now();
    record.completed = false;

    std::lock_guard<std::mutex> lock(mutex_);
    active_operations_[id] = record;
    return id;
}

void PerformanceMonitor::end_operation(std::size_t operation_id) {
    OperationRecord record;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = active_operations_.find(operation_id);
        if (it == active_operations_.end()) {
            return;
        }
        it->second.end_time = std::chrono::steady_clock::now();
        it->second.duration_ms = std::chrono::duration<double, std::milli>(
            it->second.end_time - it->second.start_time).count();
        it->second.completed = true;
        record = it->second;
        active_operations_.erase(it);

        completed_operations_[operation_id] = record;
        completion_order_.push_back(operation_id);
        if (completion_order_.size() > kMaxCompletedOperations) {
            auto oldest = completion_order_.front();
            completion_order_.pop_front();
            completed_operations_.erase(oldest);
        }

        finalize_operation_locked(operation_id, record.name, record.duration_ms);
    }
}

bool PerformanceMonitor::has_operation(std::size_t operation_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (active_operations_.count(operation_id) > 0) {
        return true;
    }
    return completed_operations_.count(operation_id) > 0;
}

void PerformanceMonitor::record_operation(const std::string& name, double duration_ms) {
    auto id = next_operation_id_.fetch_add(1, std::memory_order_relaxed);
    std::lock_guard<std::mutex> lock(mutex_);

    OperationRecord record;
    record.name = name;
    record.start_time = std::chrono::steady_clock::now();
    record.end_time = record.start_time;
    record.duration_ms = duration_ms;
    record.completed = true;

    completed_operations_[id] = record;
    completion_order_.push_back(id);
    if (completion_order_.size() > kMaxCompletedOperations) {
        auto oldest = completion_order_.front();
        completion_order_.pop_front();
        completed_operations_.erase(oldest);
    }

    finalize_operation_locked(id, name, duration_ms);
}

void PerformanceMonitor::set_slow_operation_threshold(const std::string& name,
                                                      std::chrono::milliseconds threshold) {
    std::lock_guard<std::mutex> lock(mutex_);
    slow_thresholds_[name] = threshold;
}

bool PerformanceMonitor::is_operation_slow(std::size_t operation_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto completed = completed_operations_.find(operation_id);
    if (completed != completed_operations_.end()) {
        auto it = slow_thresholds_.find(completed->second.name);
        if (it == slow_thresholds_.end()) {
            return false;
        }
        return completed->second.duration_ms >= it->second.count();
    }

    auto active = active_operations_.find(operation_id);
    if (active == active_operations_.end()) {
        return false;
    }
    auto it = slow_thresholds_.find(active->second.name);
    if (it == slow_thresholds_.end()) {
        return false;
    }
    auto now = std::chrono::steady_clock::now();
    double duration_ms = std::chrono::duration<double, std::milli>(
        now - active->second.start_time).count();
    return duration_ms >= it->second.count();
}

PerformanceSummary PerformanceMonitor::get_performance_statistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return summary_;
}

std::unordered_map<std::string, OperationStatistics>
PerformanceMonitor::get_operation_statistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return statistics_;
}

void PerformanceMonitor::finalize_operation_locked(std::size_t /*id*/, const std::string& name,
                                                   double duration_ms) {
    auto& stats = statistics_[name];
    stats.count += 1;
    stats.total_duration_ms += duration_ms;
    stats.last_duration_ms = duration_ms;

    if (stats.count == 1) {
        stats.min_duration_ms = duration_ms;
        stats.max_duration_ms = duration_ms;
    } else {
        stats.min_duration_ms = std::min(stats.min_duration_ms, duration_ms);
        stats.max_duration_ms = std::max(stats.max_duration_ms, duration_ms);
    }
    stats.average_duration_ms = stats.total_duration_ms / static_cast<double>(stats.count);

    summary_.total_operations += 1;
    summary_.total_duration_ms += duration_ms;

    auto threshold_it = slow_thresholds_.find(name);
    if (threshold_it != slow_thresholds_.end() && duration_ms >= threshold_it->second.count()) {
        stats.slow_count += 1;
        summary_.slow_operations += 1;
    }
}

PerformanceMonitor::ScopedTimer::ScopedTimer(PerformanceMonitor& monitor, std::string name)
    : monitor_(&monitor),
      name_(std::move(name)),
      start_(std::chrono::steady_clock::now()),
      stopped_(false),
      elapsed_ms_(0.0) {}

PerformanceMonitor::ScopedTimer::ScopedTimer(ScopedTimer&& other) noexcept
    : monitor_(other.monitor_),
      name_(std::move(other.name_)),
      start_(other.start_),
      stopped_(other.stopped_),
      elapsed_ms_(other.elapsed_ms_) {
    other.monitor_ = nullptr;
    other.stopped_ = true;
}

PerformanceMonitor::ScopedTimer& PerformanceMonitor::ScopedTimer::operator=(ScopedTimer&& other) noexcept {
    if (this != &other) {
        release();
        monitor_ = other.monitor_;
        name_ = std::move(other.name_);
        start_ = other.start_;
        stopped_ = other.stopped_;
        elapsed_ms_ = other.elapsed_ms_;
        other.monitor_ = nullptr;
        other.stopped_ = true;
    }
    return *this;
}

PerformanceMonitor::ScopedTimer::~ScopedTimer() {
    release();
}

void PerformanceMonitor::ScopedTimer::Stop() {
    if (!monitor_ || stopped_) {
        return;
    }
    auto end = std::chrono::steady_clock::now();
    elapsed_ms_ = std::chrono::duration<double, std::milli>(end - start_).count();
    monitor_->record_operation(name_, elapsed_ms_);
    stopped_ = true;
}

double PerformanceMonitor::ScopedTimer::GetElapsedTime() const {
    if (stopped_) {
        return elapsed_ms_;
    }
    auto now = std::chrono::steady_clock::now();
    return std::chrono::duration<double, std::milli>(now - start_).count();
}

void PerformanceMonitor::ScopedTimer::release() {
    if (monitor_ && !stopped_) {
        Stop();
    }
    monitor_ = nullptr;
}

}  // namespace utils
