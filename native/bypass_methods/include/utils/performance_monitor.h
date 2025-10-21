#pragma once

#include <atomic>
#include <chrono>
#include <cstddef>
#include <deque>
#include <mutex>
#include <string>
#include <unordered_map>
#include <deque>

namespace utils {

struct OperationStatistics {
    std::size_t count = 0;
    double total_duration_ms = 0.0;
    double min_duration_ms = 0.0;
    double max_duration_ms = 0.0;
    double average_duration_ms = 0.0;
    double last_duration_ms = 0.0;
    std::size_t slow_count = 0;
};

struct PerformanceSummary {
    std::size_t total_operations = 0;
    std::size_t slow_operations = 0;
    double total_duration_ms = 0.0;
};

class PerformanceMonitor {
public:
    class ScopedTimer {
    public:
        ScopedTimer(PerformanceMonitor& monitor, std::string name);
        ScopedTimer(ScopedTimer&& other) noexcept;
        ScopedTimer& operator=(ScopedTimer&& other) noexcept;
        ScopedTimer(const ScopedTimer&) = delete;
        ScopedTimer& operator=(const ScopedTimer&) = delete;
        ~ScopedTimer();

        void Stop();
        double GetElapsedTime() const;

    private:
        void release();

        PerformanceMonitor* monitor_;
        std::string name_;
        std::chrono::steady_clock::time_point start_;
        bool stopped_;
        double elapsed_ms_;
    };

    static void Initialize();
    static void Shutdown();
    static PerformanceMonitor* GetInstance();

    bool is_initialized() const;

    void Reset();

    ScopedTimer StartTimer(const std::string& name);

    std::size_t start_operation(const std::string& name);
    void end_operation(std::size_t operation_id);
    bool has_operation(std::size_t operation_id) const;

    void record_operation(const std::string& name, double duration_ms);

    void set_slow_operation_threshold(const std::string& name,
                                      std::chrono::milliseconds threshold);
    bool is_operation_slow(std::size_t operation_id) const;

    PerformanceSummary get_performance_statistics() const;
    std::unordered_map<std::string, OperationStatistics> get_operation_statistics() const;

private:
    PerformanceMonitor();

    struct OperationRecord {
        std::string name;
        std::chrono::steady_clock::time_point start_time;
        std::chrono::steady_clock::time_point end_time;
        double duration_ms = 0.0;
        bool completed = false;
    };

    void finalize_operation_locked(std::size_t id,
                                   const std::string& name,
                                   double duration_ms);

    mutable std::mutex mutex_;
    bool initialized_;
    std::atomic<std::size_t> next_operation_id_;
    std::unordered_map<std::size_t, OperationRecord> active_operations_;
    std::unordered_map<std::size_t, OperationRecord> completed_operations_;
    std::deque<std::size_t> completion_order_;
    std::unordered_map<std::string, OperationStatistics> statistics_;
    std::unordered_map<std::string, std::chrono::milliseconds> slow_thresholds_;
    PerformanceSummary summary_;
};

}  // namespace utils
