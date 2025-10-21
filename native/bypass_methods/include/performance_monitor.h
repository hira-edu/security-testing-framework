#pragma once

#include <chrono>
#include <cstddef>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>

#include "utils/performance_monitor.h"

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
    explicit PerformanceMonitor(std::string component = "");

    class Timer {
    public:
        Timer(PerformanceMonitor& monitor, std::string name);
        Timer(Timer&& other) noexcept;
        Timer& operator=(Timer&& other) noexcept;
        Timer(const Timer&) = delete;
        Timer& operator=(const Timer&) = delete;
        ~Timer();

        void Stop();
        double GetElapsedTime() const;

    private:
        void release();

        PerformanceMonitor* monitor_;
        std::string name_;
        std::chrono::steady_clock::time_point start_;
        bool stopped_;
        double elapsed_ms_;
        utils::PerformanceMonitor::ScopedTimer inner_timer_;
    };

    static void Initialize();
    static void Shutdown();
    static PerformanceMonitor& GetInstance();

    bool is_initialized() const;

    void Reset();

    Timer StartTimer(const std::string& name);

    std::size_t start_operation(const std::string& name);
    void end_operation(std::size_t operation_id);
    bool has_operation(std::size_t operation_id) const;

    void RecordOperation(const std::string& name, double duration_ms);

    void SetSlowOperationThreshold(const std::string& name,
                                   std::chrono::milliseconds threshold);
    bool IsOperationSlow(std::size_t operation_id) const;

    PerformanceSummary GetSummary() const;
    std::unordered_map<std::string, OperationStatistics> GetAllStats() const;
    OperationStatistics GetTimerStats(const std::string& name) const;

private:
    PerformanceMonitor();

    struct OperationRecord {
        std::string name;
        std::chrono::steady_clock::time_point start_time;
        double duration_ms = 0.0;
        bool completed = false;
    };

    void finalize_operation_locked(std::size_t id,
                                   const std::string& name,
                                   double duration_ms);

    std::string qualify(const std::string& name) const;

    mutable std::mutex mutex_;
    bool initialized_;
    std::atomic<std::size_t> next_operation_id_;
    std::unordered_map<std::size_t, OperationRecord> active_operations_;
    std::unordered_map<std::string, OperationStatistics> statistics_;
    std::unordered_map<std::string, std::chrono::milliseconds> slow_thresholds_;
    PerformanceSummary summary_;
    utils::PerformanceMonitor* native_monitor_;
    std::string component_;
};
