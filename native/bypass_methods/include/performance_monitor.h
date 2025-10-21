#pragma once

#include <chrono>
#include <string>
#include <unordered_map>
#include <utility>

#include "utils/performance_monitor.h"

using OperationStatistics = utils::OperationStatistics;
using PerformanceSummary = utils::PerformanceSummary;

class PerformanceMonitor {
public:
    class Timer {
    public:
        explicit Timer(utils::PerformanceMonitor::ScopedTimer inner)
            : inner_(std::move(inner)) {}

        Timer(Timer&&) noexcept = default;
        Timer& operator=(Timer&&) noexcept = default;
        Timer(const Timer&) = delete;
        Timer& operator=(const Timer&) = delete;

        void Stop() { inner_.Stop(); }
        double GetElapsedTime() const { return inner_.GetElapsedTime(); }

    private:
        utils::PerformanceMonitor::ScopedTimer inner_;
    };

    explicit PerformanceMonitor(std::string component = "")
        : component_(std::move(component)) {}

    static PerformanceMonitor& GetInstance() {
        static PerformanceMonitor instance;
        return instance;
    }

    static void Initialize() { utils::PerformanceMonitor::Initialize(); }
    static void Shutdown() { utils::PerformanceMonitor::Shutdown(); }

    bool IsInitialized() const {
        auto* monitor = utils::PerformanceMonitor::GetInstance();
        return monitor && monitor->is_initialized();
    }

    void Reset() { utils::PerformanceMonitor::GetInstance()->Reset(); }

    Timer StartTimer(const std::string& name) {
        return Timer(utils::PerformanceMonitor::GetInstance()->StartTimer(qualify(name)));
    }

    std::size_t start_operation(const std::string& name) {
        return utils::PerformanceMonitor::GetInstance()->start_operation(qualify(name));
    }

    void end_operation(std::size_t id) {
        utils::PerformanceMonitor::GetInstance()->end_operation(id);
    }

    bool has_operation(std::size_t id) const {
        return utils::PerformanceMonitor::GetInstance()->has_operation(id);
    }

    void RecordOperation(const std::string& name, double duration_ms) {
        utils::PerformanceMonitor::GetInstance()->record_operation(qualify(name), duration_ms);
    }

    void SetSlowOperationThreshold(const std::string& name,
                                   std::chrono::milliseconds threshold) {
        utils::PerformanceMonitor::GetInstance()->set_slow_operation_threshold(qualify(name), threshold);
    }

    bool IsOperationSlow(std::size_t id) const {
        return utils::PerformanceMonitor::GetInstance()->is_operation_slow(id);
    }

    PerformanceSummary GetSummary() const {
        return utils::PerformanceMonitor::GetInstance()->get_performance_statistics();
    }

    std::unordered_map<std::string, OperationStatistics> GetAllStats() const {
        return utils::PerformanceMonitor::GetInstance()->get_operation_statistics();
    }

private:
    std::string qualify(const std::string& name) const {
        if (component_.empty()) {
            return name;
        }
        return component_ + ":" + name;
    }

    std::string component_;
};
