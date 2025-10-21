#include "utils/error_handler.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <filesystem>
#include <thread>
#include <chrono>

namespace utils {

// Global error handler instance
static ErrorHandler* g_error_handler = nullptr;

// ErrorHandler implementation
ErrorHandler::ErrorHandler()
    : minimum_severity_(ErrorSeverity::INFO),
      log_outputs_(LogOutput::CONSOLE | LogOutput::FILE),
      max_log_file_size_(10 * 1024 * 1024), // 10MB
      max_log_files_(5),
      include_stack_trace_(true),
      include_timestamp_(true),
      include_thread_info_(true),
      current_log_file_size_(0),
      stop_monitoring_(false) {
    
    // Initialize statistics vectors
    severity_counts_.resize(6, 0); // DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL
    category_counts_.resize(17, 0); // All categories
    
    // Initialize recovery strategies
    severity_recovery_strategies_.resize(6, RecoveryStrategy::NONE);
    category_recovery_strategies_.resize(17, RecoveryStrategy::NONE);
    severity_recovery_handlers_.resize(6);
    category_recovery_handlers_.resize(17);
    
    // Set default log file path
    log_file_path_ = "logs/error_handler.log";
    
    // Initialize log outputs
    initialize_log_outputs();
    
    // Set global instance
    g_error_handler = this;
    
    logger.info("ErrorHandler initialized successfully");
}

ErrorHandler::~ErrorHandler() {
    stop_monitoring();
    cleanup_log_outputs();
    g_error_handler = nullptr;
}

ErrorHandler& ErrorHandler::get_instance() {
    static ErrorHandler instance;
    return instance;
}

void ErrorHandler::report_error(ErrorSeverity severity, ErrorCategory category,
                               const std::string& message, const std::string& function,
                               const std::string& file, int line, DWORD windows_error) {
    if (severity < minimum_severity_.load()) {
        return;
    }
    
    ErrorInfo error_info;
    error_info.severity = severity;
    error_info.category = category;
    error_info.message = message;
    error_info.function = function;
    error_info.file = file;
    error_info.line = line;
    error_info.windows_error = windows_error;
    error_info.timestamp = std::chrono::system_clock::now();
    error_info.thread_id = get_thread_id();
    error_info.process_id = get_process_id();
    
    if (include_stack_trace_.load()) {
        error_info.stack_trace = get_stack_trace();
    }
    
    report_error(error_info);
}

void ErrorHandler::report_error(const ErrorInfo& error_info) {
    if (error_info.severity < minimum_severity_.load()) {
        return;
    }
    
    // Update statistics
    {
        std::lock_guard<std::mutex> lock(stats_mutex_);
        size_t severity_index = static_cast<size_t>(error_info.severity);
        size_t category_index = static_cast<size_t>(error_info.category);
        
        if (severity_index < severity_counts_.size()) {
            severity_counts_[severity_index]++;
        }
        if (category_index < category_counts_.size()) {
            category_counts_[category_index]++;
        }
        total_error_count_++;
    }
    
    // Format error message
    std::string formatted_message = format_error_message(error_info);
    
    // Write to outputs
    write_to_outputs(error_info, formatted_message);
    
    // Handle recovery
    handle_recovery(error_info);
    
    // Check log rotation
    check_log_rotation();
}

void ErrorHandler::debug(const std::string& message, ErrorCategory category,
                        const std::string& function, const std::string& file, int line) {
    report_error(ErrorSeverity::DEBUG, category, message, function, file, line);
}

void ErrorHandler::info(const std::string& message, ErrorCategory category,
                       const std::string& function, const std::string& file, int line) {
    report_error(ErrorSeverity::INFO, category, message, function, file, line);
}

void ErrorHandler::warning(const std::string& message, ErrorCategory category,
                          const std::string& function, const std::string& file, int line) {
    report_error(ErrorSeverity::WARNING, category, message, function, file, line);
}

void ErrorHandler::error(const std::string& message, ErrorCategory category,
                        const std::string& function, const std::string& file, int line,
                        DWORD windows_error) {
    report_error(ErrorSeverity::ERROR, category, message, function, file, line, windows_error);
}

void ErrorHandler::critical(const std::string& message, ErrorCategory category,
                           const std::string& function, const std::string& file, int line,
                           DWORD windows_error) {
    report_error(ErrorSeverity::CRITICAL, category, message, function, file, line, windows_error);
}

void ErrorHandler::fatal(const std::string& message, ErrorCategory category,
                        const std::string& function, const std::string& file, int line,
                        DWORD windows_error) {
    report_error(ErrorSeverity::FATAL, category, message, function, file, line, windows_error);
}

void ErrorHandler::set_minimum_severity(ErrorSeverity severity) {
    minimum_severity_.store(severity);
}

void ErrorHandler::set_log_outputs(LogOutput outputs) {
    log_outputs_.store(outputs);
    // Reinitialize outputs
    cleanup_log_outputs();
    initialize_log_outputs();
}

void ErrorHandler::set_log_file_path(const std::string& path) {
    std::lock_guard<std::mutex> lock(config_mutex_);
    log_file_path_ = path;
    
    // Create directory if it doesn't exist
    std::filesystem::path file_path(path);
    std::filesystem::create_directories(file_path.parent_path());
}

void ErrorHandler::set_max_log_file_size(size_t max_size) {
    max_log_file_size_.store(max_size);
}

void ErrorHandler::set_max_log_files(size_t max_files) {
    max_log_files_.store(max_files);
}

void ErrorHandler::set_include_stack_trace(bool include) {
    include_stack_trace_.store(include);
}

void ErrorHandler::set_include_timestamp(bool include) {
    include_timestamp_.store(include);
}

void ErrorHandler::set_include_thread_info(bool include) {
    include_thread_info_.store(include);
}

void ErrorHandler::set_recovery_strategy(ErrorSeverity severity, RecoveryStrategy strategy) {
    size_t index = static_cast<size_t>(severity);
    if (index < severity_recovery_strategies_.size()) {
        severity_recovery_strategies_[index] = strategy;
    }
}

void ErrorHandler::set_recovery_strategy(ErrorCategory category, RecoveryStrategy strategy) {
    size_t index = static_cast<size_t>(category);
    if (index < category_recovery_strategies_.size()) {
        category_recovery_strategies_[index] = strategy;
    }
}

void ErrorHandler::set_custom_recovery_handler(ErrorSeverity severity,
                                              std::function<void(const ErrorInfo&)> handler) {
    size_t index = static_cast<size_t>(severity);
    if (index < severity_recovery_handlers_.size()) {
        severity_recovery_handlers_[index] = handler;
    }
}

void ErrorHandler::set_custom_recovery_handler(ErrorCategory category,
                                              std::function<void(const ErrorInfo&)> handler) {
    size_t index = static_cast<size_t>(category);
    if (index < category_recovery_handlers_.size()) {
        category_recovery_handlers_[index] = handler;
    }
}

size_t ErrorHandler::get_error_count(ErrorSeverity severity) const {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    size_t index = static_cast<size_t>(severity);
    if (index < severity_counts_.size()) {
        return severity_counts_[index].load();
    }
    return 0;
}

size_t ErrorHandler::get_error_count(ErrorCategory category) const {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    size_t index = static_cast<size_t>(category);
    if (index < category_counts_.size()) {
        return category_counts_[index].load();
    }
    return 0;
}

size_t ErrorHandler::get_total_error_count() const {
    return total_error_count_.load();
}

void ErrorHandler::reset_statistics() {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    for (auto& count : severity_counts_) {
        count.store(0);
    }
    for (auto& count : category_counts_) {
        count.store(0);
    }
    total_error_count_.store(0);
}

void ErrorHandler::flush_logs() {
    std::lock_guard<std::mutex> lock(log_mutex_);
    for (auto& output : log_outputs_) {
        output->flush();
    }
}

void ErrorHandler::rotate_log_files() {
    std::lock_guard<std::mutex> lock(config_mutex_);
    
    if (log_file_path_.empty()) {
        return;
    }
    
    std::filesystem::path file_path(log_file_path_);
    std::filesystem::path directory = file_path.parent_path();
    std::string filename = file_path.stem().string();
    std::string extension = file_path.extension().string();
    
    // Remove old log files beyond max_log_files_
    for (size_t i = max_log_files_.load(); i < 100; ++i) {
        std::filesystem::path old_file = directory / (filename + "_" + std::to_string(i) + extension);
        if (std::filesystem::exists(old_file)) {
            std::filesystem::remove(old_file);
        }
    }
    
    // Rotate existing log files
    for (size_t i = max_log_files_.load() - 1; i > 0; --i) {
        std::filesystem::path old_file = directory / (filename + "_" + std::to_string(i - 1) + extension);
        std::filesystem::path new_file = directory / (filename + "_" + std::to_string(i) + extension);
        if (std::filesystem::exists(old_file)) {
            std::filesystem::rename(old_file, new_file);
        }
    }
    
    // Rename current log file
    if (std::filesystem::exists(file_path)) {
        std::filesystem::path rotated_file = directory / (filename + "_1" + extension);
        std::filesystem::rename(file_path, rotated_file);
    }
    
    current_log_file_size_.store(0);
}

void ErrorHandler::clear_logs() {
    std::lock_guard<std::mutex> lock(log_mutex_);
    for (auto& output : log_outputs_) {
        output->close();
    }
    log_outputs_.clear();
    initialize_log_outputs();
}

std::string ErrorHandler::severity_to_string(ErrorSeverity severity) const {
    switch (severity) {
        case ErrorSeverity::DEBUG: return "DEBUG";
        case ErrorSeverity::INFO: return "INFO";
        case ErrorSeverity::WARNING: return "WARNING";
        case ErrorSeverity::ERROR: return "ERROR";
        case ErrorSeverity::CRITICAL: return "CRITICAL";
        case ErrorSeverity::FATAL: return "FATAL";
        default: return "UNKNOWN";
    }
}

std::string ErrorHandler::category_to_string(ErrorCategory category) const {
    switch (category) {
        case ErrorCategory::GENERAL: return "GENERAL";
        case ErrorCategory::MEMORY: return "MEMORY";
        case ErrorCategory::FILE_IO: return "FILE_IO";
        case ErrorCategory::NETWORK: return "NETWORK";
        case ErrorCategory::GRAPHICS: return "GRAPHICS";
        case ErrorCategory::HOOK: return "HOOK";
        case ErrorCategory::INJECTION: return "INJECTION";
        case ErrorCategory::CAPTURE: return "CAPTURE";
        case ErrorCategory::SYSTEM: return "SYSTEM";
        case ErrorCategory::SECURITY: return "SECURITY";
        case ErrorCategory::PERFORMANCE: return "PERFORMANCE";
        case ErrorCategory::THREADING: return "THREADING";
        case ErrorCategory::SYNCHRONIZATION: return "SYNCHRONIZATION";
        case ErrorCategory::WINDOWS_API: return "WINDOWS_API";
        case ErrorCategory::COM: return "COM";
        case ErrorCategory::DIRECTX: return "DIRECTX";
        case ErrorCategory::UNKNOWN: return "UNKNOWN";
        default: return "UNKNOWN";
    }
}

std::string ErrorHandler::get_stack_trace() const {
    // This is a simplified implementation
    // In a real implementation, you would use a library like StackWalker or dbghelp
    return "Stack trace not available in this implementation";
}

std::string ErrorHandler::get_thread_id() const {
    std::stringstream ss;
    ss << std::this_thread::get_id();
    return ss.str();
}

std::string ErrorHandler::get_process_id() const {
    return std::to_string(GetCurrentProcessId());
}

std::string ErrorHandler::get_windows_error_message(DWORD error_code) const {
    return error_utils::get_windows_error_message(error_code);
}

std::string ErrorHandler::get_last_windows_error_message() const {
    return error_utils::get_last_windows_error_message();
}

void ErrorHandler::push_error_context(const std::string& context) {
    std::lock_guard<std::mutex> lock(context_mutex_);
    error_context_stack_.push_back(context);
}

void ErrorHandler::pop_error_context() {
    std::lock_guard<std::mutex> lock(context_mutex_);
    if (!error_context_stack_.empty()) {
        error_context_stack_.pop_back();
    }
}

std::string ErrorHandler::get_current_error_context() const {
    std::lock_guard<std::mutex> lock(context_mutex_);
    if (error_context_stack_.empty()) {
        return "";
    }
    
    std::stringstream ss;
    for (size_t i = 0; i < error_context_stack_.size(); ++i) {
        if (i > 0) ss << " > ";
        ss << error_context_stack_[i];
    }
    return ss.str();
}

void ErrorHandler::initialize_log_outputs() {
    std::lock_guard<std::mutex> lock(log_mutex_);
    
    LogOutput outputs = log_outputs_.load();
    
    if (outputs & LogOutput::CONSOLE) {
        log_outputs_.push_back(std::make_unique<ConsoleLogOutput>());
    }
    
    if (outputs & LogOutput::FILE) {
        if (!log_file_path_.empty()) {
            log_outputs_.push_back(std::make_unique<FileLogOutput>(log_file_path_));
        }
    }
    
    if (outputs & LogOutput::EVENT_LOG) {
        log_outputs_.push_back(std::make_unique<EventLogOutput>());
    }
    
    if (outputs & LogOutput::DEBUGGER) {
        log_outputs_.push_back(std::make_unique<DebuggerLogOutput>());
    }
}

void ErrorHandler::cleanup_log_outputs() {
    std::lock_guard<std::mutex> lock(log_mutex_);
    for (auto& output : log_outputs_) {
        output->close();
    }
    log_outputs_.clear();
}

void ErrorHandler::write_to_outputs(const ErrorInfo& error_info, const std::string& formatted_message) {
    std::lock_guard<std::mutex> lock(log_mutex_);
    for (auto& output : log_outputs_) {
        try {
            output->write(error_info, formatted_message);
        } catch (...) {
            // Don't let output errors propagate
        }
    }
}

void ErrorHandler::handle_recovery(const ErrorInfo& error_info) {
    // Check severity-based recovery strategy
    size_t severity_index = static_cast<size_t>(error_info.severity);
    if (severity_index < severity_recovery_strategies_.size()) {
        RecoveryStrategy strategy = severity_recovery_strategies_[severity_index];
        if (strategy != RecoveryStrategy::NONE) {
            execute_recovery_strategy(strategy, error_info);
        }
        
        // Check for custom handler
        if (severity_index < severity_recovery_handlers_.size() && severity_recovery_handlers_[severity_index]) {
            try {
                severity_recovery_handlers_[severity_index](error_info);
            } catch (...) {
                // Don't let recovery handler errors propagate
            }
        }
    }
    
    // Check category-based recovery strategy
    size_t category_index = static_cast<size_t>(error_info.category);
    if (category_index < category_recovery_strategies_.size()) {
        RecoveryStrategy strategy = category_recovery_strategies_[category_index];
        if (strategy != RecoveryStrategy::NONE) {
            execute_recovery_strategy(strategy, error_info);
        }
        
        // Check for custom handler
        if (category_index < category_recovery_handlers_.size() && category_recovery_handlers_[category_index]) {
            try {
                category_recovery_handlers_[category_index](error_info);
            } catch (...) {
                // Don't let recovery handler errors propagate
            }
        }
    }
}

void ErrorHandler::execute_recovery_strategy(RecoveryStrategy strategy, const ErrorInfo& error_info) {
    switch (strategy) {
        case RecoveryStrategy::RETRY:
            // In a real implementation, you might implement retry logic
            break;
        case RecoveryStrategy::FALLBACK:
            // In a real implementation, you might implement fallback logic
            break;
        case RecoveryStrategy::RESTART:
            // In a real implementation, you might implement restart logic
            break;
        case RecoveryStrategy::TERMINATE:
            // In a real implementation, you might implement termination logic
            break;
        case RecoveryStrategy::LOG_AND_CONTINUE:
            // Already handled by logging
            break;
        case RecoveryStrategy::LOG_AND_THROW:
            // In a real implementation, you might throw an exception
            break;
        case RecoveryStrategy::NONE:
        default:
            break;
    }
}

std::string ErrorHandler::format_error_message(const ErrorInfo& error_info) const {
    std::stringstream ss;
    
    if (include_timestamp_.load()) {
        ss << "[" << get_timestamp_string() << "] ";
    }
    
    ss << "[" << severity_to_string(error_info.severity) << "] ";
    ss << "[" << category_to_string(error_info.category) << "] ";
    
    if (include_thread_info_.load()) {
        ss << "[TID:" << error_info.thread_id << "] ";
        ss << "[PID:" << error_info.process_id << "] ";
    }
    
    ss << error_info.message;
    
    if (!error_info.function.empty()) {
        ss << " (Function: " << error_info.function;
        if (!error_info.file.empty()) {
            ss << ", File: " << error_info.file << ":" << error_info.line;
        }
        ss << ")";
    }
    
    if (error_info.windows_error != 0) {
        ss << " [Windows Error: " << error_info.windows_error << " - " 
           << get_windows_error_message(error_info.windows_error) << "]";
    }
    
    std::string context = get_current_error_context();
    if (!context.empty()) {
        ss << " [Context: " << context << "]";
    }
    
    if (!error_info.stack_trace.empty()) {
        ss << "\nStack Trace:\n" << error_info.stack_trace;
    }
    
    return ss.str();
}

std::string ErrorHandler::get_timestamp_string() const {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    ss << "." << std::setfill('0') << std::setw(3) << ms.count();
    return ss.str();
}

void ErrorHandler::check_log_rotation() {
    if (current_log_file_size_.load() > max_log_file_size_.load()) {
        rotate_log_files();
    }
}

// ConsoleLogOutput implementation
ConsoleLogOutput::ConsoleLogOutput()
    : use_colors_(true), use_unicode_(true), console_handle_(GetStdHandle(STD_OUTPUT_HANDLE)) {
}

ConsoleLogOutput::~ConsoleLogOutput() {
    close();
}

void ConsoleLogOutput::write(const ErrorInfo& error_info, const std::string& formatted_message) {
    if (use_colors_) {
        set_console_color(error_info.severity);
    }
    
    std::cout << formatted_message << std::endl;
    
    if (use_colors_) {
        reset_console_color();
    }
}

void ConsoleLogOutput::flush() {
    std::cout.flush();
}

void ConsoleLogOutput::close() {
    // Nothing to do for console output
}

void ConsoleLogOutput::set_use_colors(bool use_colors) {
    use_colors_ = use_colors;
}

void ConsoleLogOutput::set_use_unicode(bool use_unicode) {
    use_unicode_ = use_unicode;
}

void ConsoleLogOutput::set_console_color(ErrorSeverity severity) {
    if (console_handle_ == INVALID_HANDLE_VALUE) {
        return;
    }
    
    WORD color = FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE; // Default white
    
    switch (severity) {
        case ErrorSeverity::DEBUG:
            color = FOREGROUND_INTENSITY; // Bright white
            break;
        case ErrorSeverity::INFO:
            color = FOREGROUND_GREEN | FOREGROUND_INTENSITY; // Bright green
            break;
        case ErrorSeverity::WARNING:
            color = FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_INTENSITY; // Bright yellow
            break;
        case ErrorSeverity::ERROR:
            color = FOREGROUND_RED | FOREGROUND_INTENSITY; // Bright red
            break;
        case ErrorSeverity::CRITICAL:
            color = FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_INTENSITY; // Bright magenta
            break;
        case ErrorSeverity::FATAL:
            color = FOREGROUND_RED | FOREGROUND_INTENSITY; // Bright red
            break;
    }
    
    SetConsoleTextAttribute(console_handle_, color);
}

void ConsoleLogOutput::reset_console_color() {
    if (console_handle_ != INVALID_HANDLE_VALUE) {
        SetConsoleTextAttribute(console_handle_, 
                               FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE);
    }
}

// FileLogOutput implementation
FileLogOutput::FileLogOutput(const std::string& file_path)
    : file_path_(file_path), max_file_size_(10 * 1024 * 1024), max_files_(5),
      file_handle_(INVALID_HANDLE_VALUE) {
    open_file();
}

FileLogOutput::~FileLogOutput() {
    close();
}

void FileLogOutput::write(const ErrorInfo& error_info, const std::string& formatted_message) {
    if (file_handle_ == INVALID_HANDLE_VALUE) {
        return;
    }
    
    std::lock_guard<std::mutex> lock(file_mutex_);
    
    std::string message = formatted_message + "\n";
    DWORD bytes_written = 0;
    
    if (WriteFile(file_handle_, message.c_str(), static_cast<DWORD>(message.length()),
                  &bytes_written, nullptr)) {
        current_log_file_size_ += bytes_written;
        check_file_size();
    }
}

void FileLogOutput::flush() {
    if (file_handle_ != INVALID_HANDLE_VALUE) {
        FlushFileBuffers(file_handle_);
    }
}

void FileLogOutput::close() {
    close_file();
}

void FileLogOutput::set_file_path(const std::string& file_path) {
    std::lock_guard<std::mutex> lock(file_mutex_);
    close_file();
    file_path_ = file_path;
    open_file();
}

void FileLogOutput::set_max_file_size(size_t max_size) {
    max_file_size_ = max_size;
}

void FileLogOutput::set_max_files(size_t max_files) {
    max_files_ = max_files;
}

void FileLogOutput::rotate_files() {
    std::lock_guard<std::mutex> lock(file_mutex_);
    
    close_file();
    
    std::filesystem::path file_path(file_path_);
    std::filesystem::path directory = file_path.parent_path();
    std::string filename = file_path.stem().string();
    std::string extension = file_path.extension().string();
    
    // Remove old log files beyond max_files_
    for (size_t i = max_files_; i < 100; ++i) {
        std::filesystem::path old_file = directory / (filename + "_" + std::to_string(i) + extension);
        if (std::filesystem::exists(old_file)) {
            std::filesystem::remove(old_file);
        }
    }
    
    // Rotate existing log files
    for (size_t i = max_files_ - 1; i > 0; --i) {
        std::filesystem::path old_file = directory / (filename + "_" + std::to_string(i - 1) + extension);
        std::filesystem::path new_file = directory / (filename + "_" + std::to_string(i) + extension);
        if (std::filesystem::exists(old_file)) {
            std::filesystem::rename(old_file, new_file);
        }
    }
    
    // Rename current log file
    if (std::filesystem::exists(file_path)) {
        std::filesystem::path rotated_file = directory / (filename + "_1" + extension);
        std::filesystem::rename(file_path, rotated_file);
    }
    
    open_file();
}

bool FileLogOutput::open_file() {
    if (file_path_.empty()) {
        return false;
    }
    
    // Create directory if it doesn't exist
    std::filesystem::path file_path(file_path_);
    std::filesystem::create_directories(file_path.parent_path());
    
    file_handle_ = CreateFileA(
        file_path_.c_str(),
        GENERIC_WRITE,
        FILE_SHARE_READ,
        nullptr,
        OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        nullptr
    );
    
    if (file_handle_ == INVALID_HANDLE_VALUE) {
        return false;
    }
    
    // Move to end of file
    SetFilePointer(file_handle_, 0, nullptr, FILE_END);
    
    // Get current file size
    DWORD file_size = GetFileSize(file_handle_, nullptr);
    current_log_file_size_ = file_size;
    
    return true;
}

void FileLogOutput::close_file() {
    if (file_handle_ != INVALID_HANDLE_VALUE) {
        CloseHandle(file_handle_);
        file_handle_ = INVALID_HANDLE_VALUE;
    }
}

void FileLogOutput::check_file_size() {
    if (current_log_file_size_ > max_file_size_) {
        rotate_files();
    }
}

std::string FileLogOutput::get_rotated_file_path(size_t index) const {
    std::filesystem::path file_path(file_path_);
    std::filesystem::path directory = file_path.parent_path();
    std::string filename = file_path.stem().string();
    std::string extension = file_path.extension().string();
    
    return (directory / (filename + "_" + std::to_string(index) + extension)).string();
}

// EventLogOutput implementation
EventLogOutput::EventLogOutput(const std::string& source_name)
    : source_name_(source_name), event_log_handle_(nullptr) {
    register_event_source();
}

EventLogOutput::~EventLogOutput() {
    close();
}

void EventLogOutput::write(const ErrorInfo& error_info, const std::string& formatted_message) {
    if (event_log_handle_ == nullptr) {
        return;
    }
    
    WORD event_type = severity_to_event_type(error_info.severity);
    WORD event_category = static_cast<WORD>(error_info.category);
    
    const char* strings[] = { formatted_message.c_str() };
    
    ReportEventA(event_log_handle_, event_type, event_category, 0, nullptr, 1, 0, strings, nullptr);
}

void EventLogOutput::flush() {
    // Event log doesn't need explicit flushing
}

void EventLogOutput::close() {
    deregister_event_source();
}

void EventLogOutput::set_source_name(const std::string& source_name) {
    deregister_event_source();
    source_name_ = source_name;
    register_event_source();
}

WORD EventLogOutput::severity_to_event_type(ErrorSeverity severity) const {
    switch (severity) {
        case ErrorSeverity::DEBUG:
        case ErrorSeverity::INFO:
            return EVENTLOG_INFORMATION_TYPE;
        case ErrorSeverity::WARNING:
            return EVENTLOG_WARNING_TYPE;
        case ErrorSeverity::ERROR:
        case ErrorSeverity::CRITICAL:
        case ErrorSeverity::FATAL:
            return EVENTLOG_ERROR_TYPE;
        default:
            return EVENTLOG_INFORMATION_TYPE;
    }
}

bool EventLogOutput::register_event_source() {
    event_log_handle_ = RegisterEventSourceA(nullptr, source_name_.c_str());
    return event_log_handle_ != nullptr;
}

void EventLogOutput::deregister_event_source() {
    if (event_log_handle_ != nullptr) {
        DeregisterEventSource(event_log_handle_);
        event_log_handle_ = nullptr;
    }
}

// DebuggerLogOutput implementation
DebuggerLogOutput::DebuggerLogOutput()
    : include_debug_info_(true) {
}

DebuggerLogOutput::~DebuggerLogOutput() {
    close();
}

void DebuggerLogOutput::write(const ErrorInfo& error_info, const std::string& formatted_message) {
    if (include_debug_info_) {
        std::string debug_message = format_debug_info(error_info) + "\n" + formatted_message;
        OutputDebugStringA(debug_message.c_str());
    } else {
        OutputDebugStringA((formatted_message + "\n").c_str());
    }
}

void DebuggerLogOutput::flush() {
    // Debug output doesn't need explicit flushing
}

void DebuggerLogOutput::close() {
    // Nothing to do for debug output
}

void DebuggerLogOutput::set_include_debug_info(bool include) {
    include_debug_info_ = include;
}

std::string DebuggerLogOutput::format_debug_info(const ErrorInfo& error_info) const {
    std::stringstream ss;
    ss << "[DEBUG] Severity: " << static_cast<int>(error_info.severity)
       << ", Category: " << static_cast<int>(error_info.category)
       << ", Thread: " << error_info.thread_id
       << ", Process: " << error_info.process_id;
    return ss.str();
}

// Error utilities implementation
namespace error_utils {

std::string get_windows_error_message(DWORD error_code) {
    if (error_code == 0) {
        return "No error";
    }
    
    LPSTR message_buffer = nullptr;
    DWORD length = FormatMessageA(
        FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
        nullptr,
        error_code,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        reinterpret_cast<LPSTR>(&message_buffer),
        0,
        nullptr
    );
    
    if (length == 0 || message_buffer == nullptr) {
        return "Unknown error code: " + std::to_string(error_code);
    }
    
    std::string message(message_buffer);
    LocalFree(message_buffer);
    
    // Remove trailing newlines and spaces
    while (!message.empty() && (message.back() == '\n' || message.back() == '\r' || message.back() == ' ')) {
        message.pop_back();
    }
    
    return message;
}

std::string get_last_windows_error_message() {
    return get_windows_error_message(GetLastError());
}

std::string get_stack_trace() {
    // This is a simplified implementation
    // In a real implementation, you would use a library like StackWalker or dbghelp
    return "Stack trace not available in this implementation";
}

std::string get_call_stack(size_t max_frames) {
    // This is a simplified implementation
    // In a real implementation, you would use a library like StackWalker or dbghelp
    return "Call stack not available in this implementation";
}

std::string get_thread_id() {
    std::stringstream ss;
    ss << std::this_thread::get_id();
    return ss.str();
}

std::string get_process_id() {
    return std::to_string(GetCurrentProcessId());
}

// ScopedErrorContext implementation
ScopedErrorContext::ScopedErrorContext(const std::string& context)
    : context_(context) {
    ErrorHandler::get_instance().push_error_context(context);
}

ScopedErrorContext::~ScopedErrorContext() {
    ErrorHandler::get_instance().pop_error_context();
}

} // namespace error_utils

} // namespace utils 