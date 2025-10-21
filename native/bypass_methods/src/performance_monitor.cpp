#include "include/performance_monitor.h"

#include <algorithm>

namespace {
std::mutex g_performance_monitor_instance_mutex;
PerformanceMonitor* g_performance_monitor_instance = nullptr;
} // namespace

// === PerformanceMonitor::Timer ==============================================

PerformanceMonitor::Timer::Timer(PerformanceMonitor& monitor, std::string name)
    : monitor_(&monitor),
      raw_name_(std::move(name)),
      qualified_name_(monitor.qualify(raw_name_)),
      start_(std::chrono::steady_clock::now()),
      stopped_(false),
      elapsed_ms_(0.0),
      inner_timer_(qualified_name_) {}

PerformanceMonitor::Timer::Timer(Timer&& other) noexcept
    : monitor_(other.monitor_),
      raw_name_(std::move(other.raw_name_)),
      qualified_name_(std::move(other.qualified_name_)),
      start_(other.start_),
      stopped_(other.stopped_),
      elapsed_ms_(other.elapsed_ms_),
      inner_timer_(std::move(other.inner_timer_)) {
    other.monitor_ = nullptr;
    other.stopped_ = true;
}

PerformanceMonitor::Timer& PerformanceMonitor::Timer::operator=(Timer&& other) noexcept {
    if (this != &other) {
        release();
        monitor_ = other.monitor_;
        raw_name_ = std::move(other.raw_name_);
        qualified_name_ = std::move(other.qualified_name_);
        start_ = other.start_;
        stopped_ = other.stopped_;
        elapsed_ms_ = other.elapsed_ms_;
        inner_timer_ = std::move(other.inner_timer_);
        other.monitor_ = nullptr;
        other.stopped_ = true;
    }
    return *this;
}

PerformanceMonitor::Timer::~Timer() {
    release();
}

void PerformanceMonitor::Timer::Stop() {
    if (stopped_) {
        return;
    }

    inner_timer_.stop();
    elapsed_ms_ = inner_timer_.get_elapsed_ms();
    if (elapsed_ms_ <= 0.0) {
        auto end = std::chrono::steady_clock::now();
        elapsed_ms_ =
            std::chrono::duration<double, std::milli>(end - start_).count();
    }

    if (monitor_) {
        monitor_->RecordOperation(raw_name_, elapsed_ms_);
    }

    stopped_ = true;
}

double PerformanceMonitor::Timer::GetElapsedTime() const {
    return elapsed_ms_;
}

void PerformanceMonitor::Timer::release() {
    if (!stopped_) {
        Stop();
    }
}

// === PerformanceMonitor =====================================================

PerformanceMonitor::PerformanceMonitor()
    : PerformanceMonitor("") {}

PerformanceMonitor::PerformanceMonitor(std::string component)
    : initialized_(true),
      next_operation_id_(1),
      native_monitor_(&utils::PerformanceMonitor::get_instance()),
      component_(std::move(component)) {
    summary_ = {};
}

void PerformanceMonitor::Initialize() {
    std::lock_guard<std::mutex> lock(g_performance_monitor_instance_mutex);
    if (!g_performance_monitor_instance) {
        g_performance_monitor_instance = new PerformanceMonitor();
    } else {
        g_performance_monitor_instance->initialized_ = true;
        g_performance_monitor_instance->Reset();
    }
    (void)utils::PerformanceMonitor::get_instance();
}

void PerformanceMonitor::Shutdown() {
    std::lock_guard<std::mutex> lock(g_performance_monitor_instance_mutex);
    delete g_performance_monitor_instance;
    g_performance_monitor_instance = nullptr;
}

PerformanceMonitor& PerformanceMonitor::GetInstance() {
    std::lock_guard<std::mutex> lock(g_performance_monitor_instance_mutex);
    if (!g_performance_monitor_instance) {
        g_performance_monitor_instance = new PerformanceMonitor();
    }
    return *g_performance_monitor_instance;
}

bool PerformanceMonitor::is_initialized() const {
    return initialized_;
}

void PerformanceMonitor::Reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    active_operations_.clear();
    statistics_.clear();
    slow_thresholds_.clear();
    summary_ = {};
    next_operation_id_.store(1, std::memory_order_relaxed);
    if (native_monitor_) {
        native_monitor_->reset();
    }
}

PerformanceMonitor::Timer PerformanceMonitor::StartTimer(const std::string& name) {
    return Timer(*this, name);
}

std::size_t PerformanceMonitor::start_operation(const std::string& name) {
    auto id = next_operation_id_.fetch_add(1, std::memory_order_relaxed);
    OperationRecord record;
    record.name = qualify(name);
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
        record = it->second;
        active_operations_.erase(it);
    }

    auto end_time = std::chrono::steady_clock::now();
    double duration_ms =
        std::chrono::duration<double, std::milli>(end_time - record.start_time).count();

    record.duration_ms = duration_ms;
    record.completed = true;

    std::lock_guard<std::mutex> lock(mutex_);
    finalize_operation_locked(operation_id, record.name, duration_ms);
}

bool PerformanceMonitor::has_operation(std::size_t operation_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return active_operations_.find(operation_id) != active_operations_.end();
}

void PerformanceMonitor::RecordOperation(const std::string& name, double duration_ms) {
    std::size_t id = next_operation_id_.fetch_add(1, std::memory_order_relaxed);
    auto qualified = qualify(name);

    {
        std::lock_guard<std::mutex> lock(mutex_);
        finalize_operation_locked(id, qualified, duration_ms);
    }

    if (native_monitor_) {
        native_monitor_->record_timer(qualified, duration_ms, "");
    }
}

void PerformanceMonitor::SetSlowOperationThreshold(const std::string& name,
                                                   std::chrono::milliseconds threshold) {
    std::lock_guard<std::mutex> lock(mutex_);
    slow_thresholds_[qualify(name)] = threshold;
}

bool PerformanceMonitor::IsOperationSlow(std::size_t operation_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = active_operations_.find(operation_id);
    if (it == active_operations_.end()) {
        return false;
    }
    auto threshold_it = slow_thresholds_.find(it->second.name);
    if (threshold_it == slow_thresholds_.end()) {
        return false;
    }

    auto now = std::chrono::steady_clock::now();
    double duration_ms =
        std::chrono::duration<double, std::milli>(now - it->second.start_time).count();
    return duration_ms >= static_cast<double>(threshold_it->second.count());
}

PerformanceSummary PerformanceMonitor::GetSummary() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return summary_;
}

std::unordered_map<std::string, OperationStatistics> PerformanceMonitor::GetAllStats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return statistics_;
}

OperationStatistics PerformanceMonitor::GetTimerStats(const std::string& name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = statistics_.find(qualify(name));
    if (it == statistics_.end()) {
        return OperationStatistics{};
    }
    return it->second;
}

void PerformanceMonitor::finalize_operation_locked(std::size_t,
                                                    const std::string& name,
                                                    double duration_ms) {
    auto& stats = statistics_[name];

    if (stats.count == 0) {
        stats.min_duration_ms = duration_ms;
        stats.max_duration_ms = duration_ms;
    } else {
        stats.min_duration_ms = std::min(stats.min_duration_ms, duration_ms);
        stats.max_duration_ms = std::max(stats.max_duration_ms, duration_ms);
    }

    stats.count++;
    stats.total_duration_ms += duration_ms;
    stats.average_duration_ms = stats.total_duration_ms / static_cast<double>(stats.count);
    stats.last_duration_ms = duration_ms;

    auto threshold_it = slow_thresholds_.find(name);
    if (threshold_it != slow_thresholds_.end() &&
        duration_ms >= static_cast<double>(threshold_it->second.count())) {
        stats.slow_count++;
        summary_.slow_operations++;
    }

    summary_.total_operations++;
    summary_.total_duration_ms += duration_ms;
}

std::string PerformanceMonitor::qualify(const std::string& name) const {
    if (component_.empty()) {
        return name;
    }
    return component_ + ":" + name;
}
