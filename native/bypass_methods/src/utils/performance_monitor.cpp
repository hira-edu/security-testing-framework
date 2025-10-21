#include "include/utils/performance_monitor.h"
#include "include/utils/error_handler.h"
#include <sstream>
#include <iomanip>
#include <filesystem>
#include <algorithm>
#include <psapi.h>
#include <pdh.h>

namespace UndownUnlock::Utils {

// Static member initialization
PerformanceMonitor* PerformanceMonitor::instance_ = nullptr;
std::mutex PerformanceMonitor::instance_mutex_;

// Static member initialization for other classes
std::atomic<double> CpuUsageMonitor::cpu_usage_(0.0);
std::chrono::system_clock::time_point CpuUsageMonitor::last_check_;
std::chrono::milliseconds CpuUsageMonitor::check_interval_(std::chrono::seconds(1));
std::atomic<bool> CpuUsageMonitor::monitoring_enabled_(false);
std::thread CpuUsageMonitor::monitoring_thread_;
std::atomic<bool> CpuUsageMonitor::thread_running_(false);

ULARGE_INTEGER CpuUsageMonitor::last_cpu_time_ = {0};
ULARGE_INTEGER CpuUsageMonitor::last_system_time_ = {0};

std::atomic<size_t> MemoryUsageMonitor::memory_usage_(0);
std::atomic<size_t> MemoryUsageMonitor::peak_memory_usage_(0);
std::chrono::system_clock::time_point MemoryUsageMonitor::last_check_;
std::chrono::milliseconds MemoryUsageMonitor::check_interval_(std::chrono::seconds(1));
std::atomic<bool> MemoryUsageMonitor::monitoring_enabled_(false);
std::thread MemoryUsageMonitor::monitoring_thread_;
std::atomic<bool> MemoryUsageMonitor::thread_running_(false);

std::atomic<size_t> ThreadUsageMonitor::thread_count_(0);
std::atomic<size_t> ThreadUsageMonitor::active_thread_count_(0);
std::chrono::system_clock::time_point ThreadUsageMonitor::last_check_;
std::chrono::milliseconds ThreadUsageMonitor::check_interval_(std::chrono::seconds(1));
std::atomic<bool> ThreadUsageMonitor::monitoring_enabled_(false);
std::thread ThreadUsageMonitor::monitoring_thread_;
std::atomic<bool> ThreadUsageMonitor::thread_running_(false);

std::vector<PerformanceProfiler::ProfilePoint> PerformanceProfiler::profile_points_;
std::mutex PerformanceProfiler::profile_mutex_;

std::vector<BottleneckDetector::BottleneckInfo> BottleneckDetector::detected_bottlenecks_;
std::mutex BottleneckDetector::bottlenecks_mutex_;

std::vector<PerformanceAlert::AlertRule> PerformanceAlert::alert_rules_;
std::mutex PerformanceAlert::alert_mutex_;

// PerformanceMonitor implementation
PerformanceMonitor::PerformanceMonitor() : monitoring_enabled_(false), 
                                          sampling_thread_running_(false) {
    stats_.start_time = std::chrono::system_clock::now();
    last_sampling_ = std::chrono::system_clock::now();
}

PerformanceMonitor::~PerformanceMonitor() {
    stop_monitoring();
    if (sampling_thread_.joinable()) {
        sampling_thread_.join();
    }
}

PerformanceMonitor& PerformanceMonitor::get_instance() {
    std::lock_guard<std::mutex> lock(instance_mutex_);
    if (!instance_) {
        instance_ = new PerformanceMonitor();
    }
    return *instance_;
}

void PerformanceMonitor::initialize(const PerformanceConfig& config) {
    std::lock_guard<std::mutex> lock(instance_mutex_);
    if (!instance_) {
        instance_ = new PerformanceMonitor();
    }
    instance_->set_config(config);
}

void PerformanceMonitor::shutdown() {
    std::lock_guard<std::mutex> lock(instance_mutex_);
    if (instance_) {
        delete instance_;
        instance_ = nullptr;
    }
}

void PerformanceMonitor::start_monitoring() {
    if (monitoring_enabled_.load()) {
        return;
    }
    
    monitoring_enabled_.store(true);
    sampling_thread_running_.store(true);
    sampling_thread_ = std::thread(&PerformanceMonitor::sampling_worker, this);
    
    // Start system monitors
    if (config_.track_cpu_usage) {
        CpuUsageMonitor::start_monitoring();
    }
    if (config_.track_memory_usage) {
        MemoryUsageMonitor::start_monitoring();
    }
    if (config_.track_thread_usage) {
        ThreadUsageMonitor::start_monitoring();
    }
}

void PerformanceMonitor::stop_monitoring() {
    if (!monitoring_enabled_.load()) {
        return;
    }
    
    monitoring_enabled_.store(false);
    sampling_thread_running_.store(false);
    
    if (sampling_thread_.joinable()) {
        sampling_thread_.join();
    }
    
    // Stop system monitors
    CpuUsageMonitor::stop_monitoring();
    MemoryUsageMonitor::stop_monitoring();
    ThreadUsageMonitor::stop_monitoring();
}

void PerformanceMonitor::add_metric(const std::string& name, MetricType type, 
                                   const std::string& description) {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    
    if (metrics_.size() >= config_.max_metrics) {
        LOG_WARNING("Maximum number of metrics reached, cannot add: " + name, ErrorCategory::GENERAL);
        return;
    }
    
    PerformanceMetric metric;
    metric.name = name;
    metric.description = description;
    metric.type = type;
    metric.first_update = std::chrono::system_clock::now();
    metric.last_update = metric.first_update;
    metric.max_samples = config_.max_samples_per_metric;
    
    metrics_[name] = metric;
}

void PerformanceMonitor::update_metric(const std::string& name, double value) {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    
    auto it = metrics_.find(name);
    if (it == metrics_.end()) {
        LOG_WARNING("Metric not found: " + name, ErrorCategory::GENERAL);
        return;
    }
    
    auto& metric = it->second;
    metric.value = value;
    metric.last_update = std::chrono::system_clock::now();
    metric.count++;
    metric.sum += value;
    
    if (value < metric.min_value || metric.count == 1) {
        metric.min_value = value;
    }
    if (value > metric.max_value || metric.count == 1) {
        metric.max_value = value;
    }
    
    // Add to samples
    metric.samples.push_back(value);
    if (metric.samples.size() > metric.max_samples) {
        metric.samples.erase(metric.samples.begin());
    }
}

void PerformanceMonitor::increment_metric(const std::string& name, double increment) {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    
    auto it = metrics_.find(name);
    if (it == metrics_.end()) {
        LOG_WARNING("Metric not found: " + name, ErrorCategory::GENERAL);
        return;
    }
    
    auto& metric = it->second;
    metric.value += increment;
    metric.last_update = std::chrono::system_clock::now();
    metric.count++;
    metric.sum += increment;
    
    if (metric.value < metric.min_value || metric.count == 1) {
        metric.min_value = metric.value;
    }
    if (metric.value > metric.max_value || metric.count == 1) {
        metric.max_value = metric.value;
    }
    
    // Add to samples
    metric.samples.push_back(metric.value);
    if (metric.samples.size() > metric.max_samples) {
        metric.samples.erase(metric.samples.begin());
    }
}

PerformanceStats PerformanceMonitor::get_stats() const {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    std::lock_guard<std::mutex> lock2(measurements_mutex_);
    
    PerformanceStats stats = stats_;
    stats.metrics = metrics_;
    stats.end_time = std::chrono::system_clock::now();
    
    // Update system metrics
    if (config_.track_cpu_usage) {
        stats.cpu_usage = current_cpu_usage_.load();
    }
    if (config_.track_memory_usage) {
        stats.memory_usage = current_memory_usage_.load();
    }
    if (config_.track_thread_usage) {
        stats.thread_count = current_thread_count_.load();
    }
    
    return stats;
}

void PerformanceMonitor::reset() {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    std::lock_guard<std::mutex> lock2(measurements_mutex_);
    
    metrics_.clear();
    active_measurements_.clear();
    completed_measurements_.clear();
    
    stats_ = PerformanceStats();
    stats_.start_time = std::chrono::system_clock::now();
}

void PerformanceMonitor::set_config(const PerformanceConfig& config) {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    config_ = config;
}

void PerformanceMonitor::start_measurement(const std::string& name, const std::string& context) {
    std::lock_guard<std::mutex> lock(measurements_mutex_);
    
    PerformancePoint point;
    point.name = name;
    point.start_time = std::chrono::high_resolution_clock::now();
    point.context = context;
    point.thread_id = std::to_string(GetCurrentThreadId());
    point.completed = false;
    
    active_measurements_[name] = point;
    stats_.active_measurements++;
}

void PerformanceMonitor::end_measurement(const std::string& name) {
    std::lock_guard<std::mutex> lock(measurements_mutex_);
    
    auto it = active_measurements_.find(name);
    if (it == active_measurements_.end()) {
        LOG_WARNING("Measurement not found: " + name, ErrorCategory::GENERAL);
        return;
    }
    
    auto& point = it->second;
    point.end_time = std::chrono::high_resolution_clock::now();
    point.completed = true;
    
    completed_measurements_.push_back(point);
    active_measurements_.erase(it);
    
    stats_.total_measurements++;
    stats_.active_measurements--;
}

double PerformanceMonitor::get_measurement_duration(const std::string& name) {
    std::lock_guard<std::mutex> lock(measurements_mutex_);
    
    // Check active measurements first
    auto active_it = active_measurements_.find(name);
    if (active_it != active_measurements_.end()) {
        auto now = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(
            now - active_it->second.start_time);
        return duration.count() / 1000000.0; // Convert to milliseconds
    }
    
    // Check completed measurements
    for (const auto& measurement : completed_measurements_) {
        if (measurement.name == name && measurement.completed) {
            auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(
                measurement.end_time - measurement.start_time);
            return duration.count() / 1000000.0; // Convert to milliseconds
        }
    }
    
    return -1.0; // Not found
}

void PerformanceMonitor::set_callback(std::function<void(const PerformanceStats&)> callback) {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    config_.callback = callback;
}

void PerformanceMonitor::generate_report(const std::string& filename) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        LOG_ERROR("Failed to open performance report file: " + filename, ErrorCategory::FILE_IO);
        return;
    }
    
    auto stats = get_stats();
    
    file << "=== Performance Monitor Report ===\n";
    file << "Generated: " << format_timestamp(std::chrono::system_clock::now()) << "\n\n";
    
    file << "=== System Metrics ===\n";
    file << "CPU Usage: " << std::fixed << std::setprecision(2) << stats.cpu_usage << "%\n";
    file << "Memory Usage: " << MemoryUtils::format_memory_size(stats.memory_usage) << "\n";
    file << "Thread Count: " << stats.thread_count << "\n";
    
    file << "\n=== Performance Metrics ===\n";
    for (const auto& pair : stats.metrics) {
        file << format_metric(pair.second) << "\n";
    }
    
    file << "\n=== Performance Measurements ===\n";
    for (const auto& measurement : stats.metrics) {
        file << format_measurement(measurement.second) << "\n";
    }
    
    file << "\n=== Bottlenecks ===\n";
    for (const auto& bottleneck : stats.bottlenecks) {
        file << "- " << bottleneck << "\n";
    }
    
    file << "\n=== Warnings ===\n";
    for (const auto& warning : stats.warnings) {
        file << "- " << warning << "\n";
    }
    
    file.close();
}

void PerformanceMonitor::print_stats() {
    auto stats = get_stats();
    printf("=== Performance Statistics ===\n");
    printf("%s", format_stats(stats).c_str());
}

void PerformanceMonitor::print_metrics() {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    printf("=== Performance Metrics ===\n");
    for (const auto& pair : metrics_) {
        printf("%s\n", format_metric(pair.second).c_str());
    }
}

void PerformanceMonitor::print_measurements() {
    std::lock_guard<std::mutex> lock(measurements_mutex_);
    printf("=== Performance Measurements ===\n");
    for (const auto& measurement : completed_measurements_) {
        printf("%s\n", format_measurement(measurement).c_str());
    }
}

void PerformanceMonitor::sampling_worker() {
    while (sampling_thread_running_.load()) {
        update_system_metrics();
        detect_bottlenecks();
        check_warnings();
        cleanup_old_samples();
        
        if (config_.callback) {
            config_.callback(get_stats());
        }
        
        std::this_thread::sleep_for(config_.sampling_interval);
    }
}

void PerformanceMonitor::update_system_metrics() {
    if (config_.track_cpu_usage) {
        current_cpu_usage_.store(CpuUsageMonitor::get_cpu_usage());
    }
    if (config_.track_memory_usage) {
        current_memory_usage_.store(MemoryUsageMonitor::get_memory_usage());
    }
    if (config_.track_thread_usage) {
        current_thread_count_.store(ThreadUsageMonitor::get_thread_count());
    }
}

void PerformanceMonitor::detect_bottlenecks() {
    auto stats = get_stats();
    
    // CPU bottleneck detection
    if (stats.cpu_usage > 90.0) {
        stats_.bottlenecks.push_back("High CPU usage: " + std::to_string(stats.cpu_usage) + "%");
    }
    
    // Memory bottleneck detection
    if (stats.memory_usage > 1024 * 1024 * 1024) { // 1GB
        stats_.bottlenecks.push_back("High memory usage: " + MemoryUtils::format_memory_size(stats.memory_usage));
    }
    
    // Thread bottleneck detection
    if (stats.thread_count > 100) {
        stats_.bottlenecks.push_back("High thread count: " + std::to_string(stats.thread_count));
    }
    
    // Measurement bottleneck detection
    for (const auto& pair : stats.metrics) {
        if (pair.second.type == MetricType::TIMER && pair.second.value > 1000.0) {
            stats_.bottlenecks.push_back("Slow operation: " + pair.first + " (" + 
                                       std::to_string(pair.second.value) + "ms)");
        }
    }
}

void PerformanceMonitor::check_warnings() {
    auto stats = get_stats();
    
    // CPU warnings
    if (stats.cpu_usage > 80.0) {
        stats_.warnings.push_back("CPU usage is high: " + std::to_string(stats.cpu_usage) + "%");
    }
    
    // Memory warnings
    if (stats.memory_usage > 512 * 1024 * 1024) { // 512MB
        stats_.warnings.push_back("Memory usage is high: " + MemoryUtils::format_memory_size(stats.memory_usage));
    }
    
    // Thread warnings
    if (stats.thread_count > 50) {
        stats_.warnings.push_back("Thread count is high: " + std::to_string(stats.thread_count));
    }
}

void PerformanceMonitor::cleanup_old_samples() {
    std::lock_guard<std::mutex> lock(metrics_mutex_);
    
    auto now = std::chrono::system_clock::now();
    for (auto& pair : metrics_) {
        auto& metric = pair.second;
        if (metric.samples.size() > metric.max_samples) {
            metric.samples.erase(metric.samples.begin());
        }
    }
}

std::string PerformanceMonitor::format_metric(const PerformanceMetric& metric) {
    std::ostringstream oss;
    oss << "Metric: " << metric.name;
    if (!metric.description.empty()) {
        oss << " (" << metric.description << ")";
    }
    oss << "\n  Type: " << metric_type_to_string(metric.type);
    oss << "\n  Value: " << std::fixed << std::setprecision(2) << metric.value;
    oss << "\n  Min: " << metric.min_value << ", Max: " << metric.max_value;
    oss << "\n  Count: " << metric.count << ", Sum: " << metric.sum;
    if (!metric.samples.empty()) {
        oss << "\n  Average: " << calculate_average(metric.samples);
        oss << "\n  Samples: " << metric.samples.size();
    }
    return oss.str();
}

std::string PerformanceMonitor::format_measurement(const PerformancePoint& measurement) {
    std::ostringstream oss;
    oss << "Measurement: " << measurement.name;
    if (!measurement.context.empty()) {
        oss << " (Context: " << measurement.context << ")";
    }
    oss << "\n  Thread: " << measurement.thread_id;
    oss << "\n  Completed: " << (measurement.completed ? "Yes" : "No");
    if (measurement.completed) {
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(
            measurement.end_time - measurement.start_time);
        oss << "\n  Duration: " << (duration.count() / 1000000.0) << "ms";
    }
    return oss.str();
}

std::string PerformanceMonitor::format_stats(const PerformanceStats& stats) {
    std::ostringstream oss;
    oss << "Start Time: " << format_timestamp(stats.start_time) << "\n";
    oss << "End Time: " << format_timestamp(stats.end_time) << "\n";
    oss << "Total Measurements: " << stats.total_measurements << "\n";
    oss << "Active Measurements: " << stats.active_measurements << "\n";
    oss << "CPU Usage: " << std::fixed << std::setprecision(2) << stats.cpu_usage << "%\n";
    oss << "Memory Usage: " << MemoryUtils::format_memory_size(stats.memory_usage) << "\n";
    oss << "Thread Count: " << stats.thread_count << "\n";
    oss << "Metrics Count: " << stats.metrics.size() << "\n";
    oss << "Bottlenecks: " << stats.bottlenecks.size() << "\n";
    oss << "Warnings: " << stats.warnings.size() << "\n";
    return oss.str();
}

double PerformanceMonitor::calculate_average(const std::vector<double>& samples) {
    if (samples.empty()) return 0.0;
    
    double sum = 0.0;
    for (double sample : samples) {
        sum += sample;
    }
    return sum / samples.size();
}

double PerformanceMonitor::calculate_percentile(const std::vector<double>& samples, double percentile) {
    if (samples.empty()) return 0.0;
    
    std::vector<double> sorted_samples = samples;
    std::sort(sorted_samples.begin(), sorted_samples.end());
    
    size_t index = static_cast<size_t>(percentile * sorted_samples.size() / 100.0);
    if (index >= sorted_samples.size()) {
        index = sorted_samples.size() - 1;
    }
    
    return sorted_samples[index];
}

std::string PerformanceMonitor::format_timestamp(const std::chrono::system_clock::time_point& timestamp) {
    auto time_t = std::chrono::system_clock::to_time_t(timestamp);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        timestamp.time_since_epoch()) % 1000;
    
    std::ostringstream oss;
    oss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    oss << "." << std::setfill('0') << std::setw(3) << ms.count();
    return oss.str();
}

std::string PerformanceMonitor::metric_type_to_string(MetricType type) {
    switch (type) {
        case MetricType::COUNTER: return "COUNTER";
        case MetricType::GAUGE: return "GAUGE";
        case MetricType::HISTOGRAM: return "HISTOGRAM";
        case MetricType::TIMER: return "TIMER";
        case MetricType::RATE: return "RATE";
        default: return "UNKNOWN";
    }
}

// CpuUsageMonitor implementation
void CpuUsageMonitor::start_monitoring(std::chrono::milliseconds interval) {
    check_interval_ = interval;
    monitoring_enabled_.store(true);
    thread_running_.store(true);
    monitoring_thread_ = std::thread(&CpuUsageMonitor::monitoring_worker);
}

void CpuUsageMonitor::stop_monitoring() {
    monitoring_enabled_.store(false);
    thread_running_.store(false);
    if (monitoring_thread_.joinable()) {
        monitoring_thread_.join();
    }
}

double CpuUsageMonitor::get_cpu_usage() {
    return cpu_usage_.load();
}

void CpuUsageMonitor::monitoring_worker() {
    while (thread_running_.load()) {
        cpu_usage_.store(calculate_cpu_usage());
        std::this_thread::sleep_for(check_interval_);
    }
}

double CpuUsageMonitor::calculate_cpu_usage() {
    FILETIME idle_time, kernel_time, user_time;
    if (!GetSystemTimes(&idle_time, &kernel_time, &user_time)) {
        return 0.0;
    }
    
    ULARGE_INTEGER current_idle, current_kernel, current_user;
    current_idle.LowPart = idle_time.dwLowDateTime;
    current_idle.HighPart = idle_time.dwHighDateTime;
    current_kernel.LowPart = kernel_time.dwLowDateTime;
    current_kernel.HighPart = kernel_time.dwHighDateTime;
    current_user.LowPart = user_time.dwLowDateTime;
    current_user.HighPart = user_time.dwHighDateTime;
    
    ULARGE_INTEGER current_system = {0};
    current_system.QuadPart = current_kernel.QuadPart + current_user.QuadPart;
    
    if (last_system_time_.QuadPart != 0) {
        ULARGE_INTEGER idle_diff, system_diff;
        idle_diff.QuadPart = current_idle.QuadPart - last_cpu_time_.QuadPart;
        system_diff.QuadPart = current_system.QuadPart - last_system_time_.QuadPart;
        
        if (system_diff.QuadPart > 0) {
            double cpu_usage = 100.0 - (idle_diff.QuadPart * 100.0 / system_diff.QuadPart);
            return std::max(0.0, std::min(100.0, cpu_usage));
        }
    }
    
    last_cpu_time_ = current_idle;
    last_system_time_ = current_system;
    return 0.0;
}

// MemoryUsageMonitor implementation
void MemoryUsageMonitor::start_monitoring(std::chrono::milliseconds interval) {
    check_interval_ = interval;
    monitoring_enabled_.store(true);
    thread_running_.store(true);
    monitoring_thread_ = std::thread(&MemoryUsageMonitor::monitoring_worker);
}

void MemoryUsageMonitor::stop_monitoring() {
    monitoring_enabled_.store(false);
    thread_running_.store(false);
    if (monitoring_thread_.joinable()) {
        monitoring_thread_.join();
    }
}

size_t MemoryUsageMonitor::get_memory_usage() {
    return memory_usage_.load();
}

size_t MemoryUsageMonitor::get_peak_memory_usage() {
    return peak_memory_usage_.load();
}

void MemoryUsageMonitor::monitoring_worker() {
    while (thread_running_.load()) {
        size_t current_usage = calculate_memory_usage();
        memory_usage_.store(current_usage);
        
        size_t peak = peak_memory_usage_.load();
        if (current_usage > peak) {
            peak_memory_usage_.store(current_usage);
        }
        
        std::this_thread::sleep_for(check_interval_);
    }
}

size_t MemoryUsageMonitor::calculate_memory_usage() {
    PROCESS_MEMORY_COUNTERS_EX pmc;
    if (GetProcessMemoryInfo(GetCurrentProcess(), 
                            reinterpret_cast<PROCESS_MEMORY_COUNTERS*>(&pmc), sizeof(pmc))) {
        return pmc.WorkingSetSize;
    }
    return 0;
}

// ThreadUsageMonitor implementation
void ThreadUsageMonitor::start_monitoring(std::chrono::milliseconds interval) {
    check_interval_ = interval;
    monitoring_enabled_.store(true);
    thread_running_.store(true);
    monitoring_thread_ = std::thread(&ThreadUsageMonitor::monitoring_worker);
}

void ThreadUsageMonitor::stop_monitoring() {
    monitoring_enabled_.store(false);
    thread_running_.store(false);
    if (monitoring_thread_.joinable()) {
        monitoring_thread_.join();
    }
}

size_t ThreadUsageMonitor::get_thread_count() {
    return thread_count_.load();
}

size_t ThreadUsageMonitor::get_active_thread_count() {
    return active_thread_count_.load();
}

void ThreadUsageMonitor::monitoring_worker() {
    while (thread_running_.load()) {
        calculate_thread_usage();
        std::this_thread::sleep_for(check_interval_);
    }
}

void ThreadUsageMonitor::calculate_thread_usage() {
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        return;
    }
    
    THREADENTRY32 thread_entry;
    thread_entry.dwSize = sizeof(THREADENTRY32);
    
    size_t total_threads = 0;
    size_t active_threads = 0;
    DWORD current_process_id = GetCurrentProcessId();
    
    if (Thread32First(snapshot, &thread_entry)) {
        do {
            if (thread_entry.th32OwnerProcessID == current_process_id) {
                total_threads++;
                if (thread_entry.th32ThreadID != GetCurrentThreadId()) {
                    active_threads++;
                }
            }
        } while (Thread32Next(snapshot, &thread_entry));
    }
    
    CloseHandle(snapshot);
    
    thread_count_.store(total_threads);
    active_thread_count_.store(active_threads);
}

// PerformanceProfiler implementation
void PerformanceProfiler::add_profile_point(const std::string& name) {
    std::lock_guard<std::mutex> lock(profile_mutex_);
    ProfilePoint point;
    point.name = name;
    point.timestamp = std::chrono::system_clock::now();
    point.stats = PerformanceMonitor::get_instance().get_stats();
    profile_points_.push_back(point);
}

void PerformanceProfiler::clear_profile() {
    std::lock_guard<std::mutex> lock(profile_mutex_);
    profile_points_.clear();
}

std::vector<PerformanceProfiler::ProfilePoint> PerformanceProfiler::get_profile() {
    std::lock_guard<std::mutex> lock(profile_mutex_);
    return profile_points_;
}

void PerformanceProfiler::generate_profile_report(const std::string& filename) {
    auto profile = get_profile();
    std::ofstream file(filename);
    if (!file.is_open()) {
        LOG_ERROR("Failed to open profile report file: " + filename, ErrorCategory::FILE_IO);
        return;
    }
    
    file << "=== Performance Profile Report ===\n";
    file << "Generated: " << PerformanceMonitor::get_instance().format_timestamp(std::chrono::system_clock::now()) << "\n\n";
    
    for (const auto& point : profile) {
        file << "=== Profile Point: " << point.name << " ===\n";
        file << "Timestamp: " << PerformanceMonitor::get_instance().format_timestamp(point.timestamp) << "\n";
        file << PerformanceMonitor::get_instance().format_stats(point.stats) << "\n";
    }
    
    file.close();
}

void PerformanceProfiler::print_profile() {
    auto profile = get_profile();
    printf("=== Performance Profile ===\n");
    for (const auto& point : profile) {
        printf("Profile Point: %s\n", point.name.c_str());
        printf("Timestamp: %s\n", PerformanceMonitor::get_instance().format_timestamp(point.timestamp).c_str());
        printf("%s", PerformanceMonitor::get_instance().format_stats(point.stats).c_str());
        printf("\n");
    }
}

// BottleneckDetector implementation
void BottleneckDetector::detect_bottlenecks(const PerformanceStats& stats) {
    std::lock_guard<std::mutex> lock(bottlenecks_mutex_);
    detected_bottlenecks_.clear();
    
    check_cpu_bottlenecks(stats);
    check_memory_bottlenecks(stats);
    check_thread_bottlenecks(stats);
    check_measurement_bottlenecks(stats);
}

std::vector<BottleneckDetector::BottleneckInfo> BottleneckDetector::get_bottlenecks() {
    std::lock_guard<std::mutex> lock(bottlenecks_mutex_);
    return detected_bottlenecks_;
}

void BottleneckDetector::clear_bottlenecks() {
    std::lock_guard<std::mutex> lock(bottlenecks_mutex_);
    detected_bottlenecks_.clear();
}

size_t BottleneckDetector::get_bottleneck_count() {
    std::lock_guard<std::mutex> lock(bottlenecks_mutex_);
    return detected_bottlenecks_.size();
}

void BottleneckDetector::generate_bottleneck_report(const std::string& filename) {
    auto bottlenecks = get_bottlenecks();
    std::ofstream file(filename);
    if (!file.is_open()) {
        LOG_ERROR("Failed to open bottleneck report file: " + filename, ErrorCategory::FILE_IO);
        return;
    }
    
    file << "=== Bottleneck Report ===\n";
    file << "Generated: " << PerformanceMonitor::get_instance().format_timestamp(std::chrono::system_clock::now()) << "\n\n";
    
    for (const auto& bottleneck : bottlenecks) {
        file << "Bottleneck: " << bottleneck.name << "\n";
        file << "Type: " << bottleneck.type << "\n";
        file << "Severity: " << bottleneck.severity << "\n";
        file << "Description: " << bottleneck.description << "\n";
        file << "Detection Time: " << PerformanceMonitor::get_instance().format_timestamp(bottleneck.detection_time) << "\n\n";
    }
    
    file.close();
}

void BottleneckDetector::print_bottlenecks() {
    auto bottlenecks = get_bottlenecks();
    printf("=== Bottlenecks ===\n");
    for (const auto& bottleneck : bottlenecks) {
        printf("Bottleneck: %s\n", bottleneck.name.c_str());
        printf("Type: %s\n", bottleneck.type.c_str());
        printf("Severity: %.2f\n", bottleneck.severity);
        printf("Description: %s\n", bottleneck.description.c_str());
        printf("Detection Time: %s\n\n", PerformanceMonitor::get_instance().format_timestamp(bottleneck.detection_time).c_str());
    }
}

void BottleneckDetector::check_cpu_bottlenecks(const PerformanceStats& stats) {
    if (stats.cpu_usage > 90.0) {
        BottleneckInfo bottleneck;
        bottleneck.name = "High CPU Usage";
        bottleneck.type = "CPU";
        bottleneck.severity = stats.cpu_usage / 100.0;
        bottleneck.description = "CPU usage is critically high: " + std::to_string(stats.cpu_usage) + "%";
        bottleneck.detection_time = std::chrono::system_clock::now();
        detected_bottlenecks_.push_back(bottleneck);
    }
}

void BottleneckDetector::check_memory_bottlenecks(const PerformanceStats& stats) {
    if (stats.memory_usage > 1024 * 1024 * 1024) { // 1GB
        BottleneckInfo bottleneck;
        bottleneck.name = "High Memory Usage";
        bottleneck.type = "Memory";
        bottleneck.severity = std::min(1.0, stats.memory_usage / (2.0 * 1024 * 1024 * 1024)); // Normalize to 2GB
        bottleneck.description = "Memory usage is high: " + MemoryUtils::format_memory_size(stats.memory_usage);
        bottleneck.detection_time = std::chrono::system_clock::now();
        detected_bottlenecks_.push_back(bottleneck);
    }
}

void BottleneckDetector::check_thread_bottlenecks(const PerformanceStats& stats) {
    if (stats.thread_count > 100) {
        BottleneckInfo bottleneck;
        bottleneck.name = "High Thread Count";
        bottleneck.type = "Thread";
        bottleneck.severity = std::min(1.0, stats.thread_count / 200.0); // Normalize to 200 threads
        bottleneck.description = "Thread count is high: " + std::to_string(stats.thread_count);
        bottleneck.detection_time = std::chrono::system_clock::now();
        detected_bottlenecks_.push_back(bottleneck);
    }
}

void BottleneckDetector::check_measurement_bottlenecks(const PerformanceStats& stats) {
    for (const auto& pair : stats.metrics) {
        if (pair.second.type == MetricType::TIMER && pair.second.value > 1000.0) {
            BottleneckInfo bottleneck;
            bottleneck.name = "Slow Operation: " + pair.first;
            bottleneck.type = "Performance";
            bottleneck.severity = std::min(1.0, pair.second.value / 5000.0); // Normalize to 5 seconds
            bottleneck.description = "Operation is slow: " + std::to_string(pair.second.value) + "ms";
            bottleneck.detection_time = std::chrono::system_clock::now();
            detected_bottlenecks_.push_back(bottleneck);
        }
    }
}

// PerformanceAlert implementation
void PerformanceAlert::add_alert_rule(const std::string& name, const std::string& metric_name,
                                     const std::string& condition, double threshold,
                                     std::function<void(const std::string&, double)> callback) {
    std::lock_guard<std::mutex> lock(alert_mutex_);
    AlertRule rule;
    rule.name = name;
    rule.metric_name = metric_name;
    rule.condition = condition;
    rule.threshold = threshold;
    rule.callback = callback;
    rule.enabled = true;
    alert_rules_.push_back(rule);
}

void PerformanceAlert::check_alerts(const PerformanceStats& stats) {
    std::lock_guard<std::mutex> lock(alert_mutex_);
    
    for (const auto& rule : alert_rules_) {
        if (!rule.enabled) continue;
        
        auto it = stats.metrics.find(rule.metric_name);
        if (it == stats.metrics.end()) continue;
        
        bool triggered = false;
        double value = it->second.value;
        
        if (rule.condition == ">" && value > rule.threshold) {
            triggered = true;
        } else if (rule.condition == "<" && value < rule.threshold) {
            triggered = true;
        } else if (rule.condition == ">=" && value >= rule.threshold) {
            triggered = true;
        } else if (rule.condition == "<=" && value <= rule.threshold) {
            triggered = true;
        } else if (rule.condition == "==" && value == rule.threshold) {
            triggered = true;
        }
        
        if (triggered && rule.callback) {
            rule.callback(rule.metric_name, value);
        }
    }
}

void PerformanceAlert::clear_alerts() {
    std::lock_guard<std::mutex> lock(alert_mutex_);
    alert_rules_.clear();
}

size_t PerformanceAlert::get_alert_rule_count() {
    std::lock_guard<std::mutex> lock(alert_mutex_);
    return alert_rules_.size();
}

void PerformanceAlert::print_alerts() {
    std::lock_guard<std::mutex> lock(alert_mutex_);
    printf("=== Performance Alerts ===\n");
    for (const auto& rule : alert_rules_) {
        printf("Alert: %s\n", rule.name.c_str());
        printf("Metric: %s\n", rule.metric_name.c_str());
        printf("Condition: %s %.2f\n", rule.condition.c_str(), rule.threshold);
        printf("Enabled: %s\n\n", rule.enabled ? "Yes" : "No");
    }
}

// PerformanceUtils implementation
namespace PerformanceUtils {
    double get_system_cpu_usage() {
        return CpuUsageMonitor::get_cpu_usage();
    }
    
    size_t get_system_memory_usage() {
        MEMORYSTATUSEX memInfo;
        memInfo.dwLength = sizeof(MEMORYSTATUSEX);
        if (GlobalMemoryStatusEx(&memInfo)) {
            return memInfo.ullTotalPhys - memInfo.ullAvailPhys;
        }
        return 0;
    }
    
    size_t get_system_available_memory() {
        MEMORYSTATUSEX memInfo;
        memInfo.dwLength = sizeof(MEMORYSTATUSEX);
        if (GlobalMemoryStatusEx(&memInfo)) {
            return memInfo.ullAvailPhys;
        }
        return 0;
    }
    
    size_t get_process_cpu_usage() {
        return static_cast<size_t>(CpuUsageMonitor::get_cpu_usage());
    }
    
    size_t get_process_memory_usage() {
        return MemoryUsageMonitor::get_memory_usage();
    }
    
    std::string format_duration(std::chrono::nanoseconds duration) {
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(duration);
        auto us = std::chrono::duration_cast<std::chrono::microseconds>(duration);
        auto ns = duration.count();
        
        if (ms.count() > 0) {
            return std::to_string(ms.count()) + "ms";
        } else if (us.count() > 0) {
            return std::to_string(us.count()) + "μs";
        } else {
            return std::to_string(ns) + "ns";
        }
    }
    
    std::string format_memory_size(size_t bytes) {
        return MemoryUtils::format_memory_size(bytes);
    }
    
    std::string format_percentage(double value) {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(2) << value << "%";
        return oss.str();
    }
    
    bool is_performance_critical() {
        auto cpu_usage = get_system_cpu_usage();
        auto memory_usage = get_system_memory_usage();
        auto available_memory = get_system_available_memory();
        
        return cpu_usage > 90.0 || available_memory < 512 * 1024 * 1024; // 512MB threshold
    }
    
    void optimize_performance() {
        // Force memory cleanup
        MemoryUtils::optimize_memory_usage();
        
        // Set process priority to normal
        SetPriorityClass(GetCurrentProcess(), NORMAL_PRIORITY_CLASS);
        
        // Reduce working set
        SetProcessWorkingSetSize(GetCurrentProcess(), -1, -1);
    }
    
    std::vector<std::string> get_performance_recommendations() {
        std::vector<std::string> recommendations;
        
        auto cpu_usage = get_system_cpu_usage();
        auto memory_usage = get_system_memory_usage();
        auto available_memory = get_system_available_memory();
        
        if (cpu_usage > 80.0) {
            recommendations.push_back("Consider reducing CPU-intensive operations");
        }
        
        if (available_memory < 1024 * 1024 * 1024) { // 1GB
            recommendations.push_back("Consider freeing up memory or reducing memory usage");
        }
        
        if (recommendations.empty()) {
            recommendations.push_back("Performance is within acceptable limits");
        }
        
        return recommendations;
    }
}

} // namespace UndownUnlock::Utils 