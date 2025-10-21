#include "utils/error_handler.h"

#include <algorithm>
#include <sstream>
#include <thread>

namespace utils {

namespace {
std::mutex g_handler_mutex;
ErrorHandler* g_handler = nullptr;

ErrorSeverity LogLevelToSeverity(LogLevel level) {
    switch (level) {
        case LogLevel::DEBUG:
            return ErrorSeverity::DEBUG;
        case LogLevel::INFO:
            return ErrorSeverity::INFO;
        case LogLevel::WARNING:
            return ErrorSeverity::WARNING;
        case LogLevel::ERROR:
            return ErrorSeverity::ERROR;
        case LogLevel::CRITICAL:
            return ErrorSeverity::CRITICAL;
        case LogLevel::FATAL:
            return ErrorSeverity::FATAL;
        default:
            return ErrorSeverity::INFO;
    }
}

bool SeverityAtLeast(ErrorSeverity lhs, ErrorSeverity rhs) {
    return static_cast<std::uint8_t>(lhs) >= static_cast<std::uint8_t>(rhs);
}
}  // namespace

// ====================== ErrorContext ==========================================

void ErrorContext::set(const std::string& key, const std::string& value) {
    values_[key] = value;
}

bool ErrorContext::contains(const std::string& key) const {
    return values_.find(key) != values_.end();
}

std::string ErrorContext::get(const std::string& key) const {
    auto it = values_.find(key);
    return it != values_.end() ? it->second : std::string{};
}

void ErrorContext::clear() {
    values_.clear();
}

bool ErrorContext::empty() const {
    return values_.empty();
}

const std::unordered_map<std::string, std::string>& ErrorContext::values() const {
    return values_;
}

// ====================== ErrorHandler ==========================================

ErrorHandler::ErrorHandler()
    : initialized_(true),
      minimum_level_(LogLevel::DEBUG) {}

void ErrorHandler::Initialize() {
    std::lock_guard<std::mutex> lock(g_handler_mutex);
    if (!g_handler) {
        g_handler = new ErrorHandler();
    }
}

void ErrorHandler::Shutdown() {
    std::lock_guard<std::mutex> lock(g_handler_mutex);
    delete g_handler;
    g_handler = nullptr;
}

ErrorHandler* ErrorHandler::GetInstance() {
    std::lock_guard<std::mutex> lock(g_handler_mutex);
    if (!g_handler) {
        g_handler = new ErrorHandler();
    }
    return g_handler;
}

bool ErrorHandler::is_initialized() const {
    return initialized_.load(std::memory_order_relaxed);
}

void ErrorHandler::set_minimum_log_level(LogLevel level) {
    minimum_level_.store(level, std::memory_order_relaxed);
}

LogLevel ErrorHandler::get_minimum_log_level() const {
    return minimum_level_.load(std::memory_order_relaxed);
}

void ErrorHandler::ClearLogs() {
    std::lock_guard<std::mutex> lock(mutex_);
    logs_.clear();
    statistics_ = ErrorStatistics{};
}

std::vector<ErrorLog> ErrorHandler::GetLogs() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return logs_;
}

std::vector<ErrorLog> ErrorHandler::GetErrors() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<ErrorLog> result;
    for (const auto& log : logs_) {
        if (SeverityAtLeast(log.severity, ErrorSeverity::WARNING)) {
            result.push_back(log);
        }
    }
    return result;
}

std::vector<ErrorContextInfo> ErrorHandler::GetContexts() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return context_history_;
}

ErrorStatistics ErrorHandler::get_error_statistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return statistics_;
}

ScopedErrorContext ErrorHandler::CreateContext(const std::string& name,
                                               std::map<std::string, std::string> metadata) {
    return ScopedErrorContext(*this, name, std::move(metadata));
}

void ErrorHandler::set_error_context(const ErrorContext& context) {
    std::lock_guard<std::mutex> lock(mutex_);
    context_stack_.clear();
    if (!context.values().empty()) {
        std::vector<std::pair<std::string, std::string>> pairs;
        pairs.reserve(context.values().size());
        for (const auto& [key, value] : context.values()) {
            pairs.emplace_back(key, value);
        }
        context_stack_.push_back(std::move(pairs));
    }
}

void ErrorHandler::clear_error_context() {
    std::lock_guard<std::mutex> lock(mutex_);
    context_stack_.clear();
}

void ErrorHandler::report_error(ErrorSeverity severity,
                                ErrorCategory category,
                                const std::string& message,
                                const std::string& function,
                                const std::string& file,
                                int line,
                                DWORD windows_error) {
    LogLevel min_level = minimum_level_.load(std::memory_order_relaxed);
    if (!SeverityAtLeast(severity, LogLevelToSeverity(min_level))) {
        return;
    }

    ErrorLog entry;
    entry.severity = severity;
    entry.category = category;
    entry.message = message;
    entry.function = function;
    entry.file = file;
    entry.line = line;
    entry.windows_error = windows_error;
    entry.timestamp = std::chrono::system_clock::now();
    entry.context = capture_context();

    append_log(entry);
}

void ErrorHandler::debug(const std::string& message,
                         ErrorCategory category,
                         const std::string& function,
                         const std::string& file,
                         int line) {
    report_error(ErrorSeverity::DEBUG, category, message, function, file, line);
}

void ErrorHandler::info(const std::string& message,
                        ErrorCategory category,
                        const std::string& function,
                        const std::string& file,
                        int line) {
    report_error(ErrorSeverity::INFO, category, message, function, file, line);
}

void ErrorHandler::warning(const std::string& message,
                           ErrorCategory category,
                           const std::string& function,
                           const std::string& file,
                           int line,
                           DWORD windows_error) {
    report_error(ErrorSeverity::WARNING, category, message, function, file, line, windows_error);
}

void ErrorHandler::error(const std::string& message,
                         ErrorCategory category,
                         const std::string& function,
                         const std::string& file,
                         int line,
                         DWORD windows_error,
                         RecoveryStrategy /*strategy*/) {
    report_error(ErrorSeverity::ERROR, category, message, function, file, line, windows_error);
}

void ErrorHandler::critical(const std::string& message,
                            ErrorCategory category,
                            const std::string& function,
                            const std::string& file,
                            int line,
                            DWORD windows_error) {
    report_error(ErrorSeverity::CRITICAL, category, message, function, file, line, windows_error);
}

void ErrorHandler::fatal(const std::string& message,
                         ErrorCategory category,
                         const std::string& function,
                         const std::string& file,
                         int line,
                         DWORD windows_error) {
    report_error(ErrorSeverity::FATAL, category, message, function, file, line, windows_error);
}

void ErrorHandler::LogInfo(const std::string& component,
                           const std::string& message,
                           const std::map<std::string, std::string>& details) {
    ErrorLog entry;
    entry.severity = ErrorSeverity::INFO;
    entry.category = ErrorCategory::GENERAL;
    entry.component = component;
    entry.message = message;
    entry.details = details;
    entry.timestamp = std::chrono::system_clock::now();
    entry.context = capture_context();

    append_log(entry);
}

void ErrorHandler::LogInfo(ErrorCategory category,
                           const std::string& message,
                           const std::map<std::string, std::string>& details) {
    ErrorLog entry;
    entry.severity = ErrorSeverity::INFO;
    entry.category = category;
    entry.message = message;
    entry.details = details;
    entry.timestamp = std::chrono::system_clock::now();
    entry.context = capture_context();

    append_log(entry);
}

void ErrorHandler::LogWarning(const std::string& component,
                              const std::string& message,
                              const std::map<std::string, std::string>& details) {
    ErrorLog entry;
    entry.severity = ErrorSeverity::WARNING;
    entry.category = ErrorCategory::GENERAL;
    entry.component = component;
    entry.message = message;
    entry.details = details;
    entry.timestamp = std::chrono::system_clock::now();
    entry.context = capture_context();

    append_log(entry);
}

void ErrorHandler::LogWarning(ErrorCategory category,
                              const std::string& message,
                              const std::map<std::string, std::string>& details) {
    ErrorLog entry;
    entry.severity = ErrorSeverity::WARNING;
    entry.category = category;
    entry.message = message;
    entry.details = details;
    entry.timestamp = std::chrono::system_clock::now();
    entry.context = capture_context();

    append_log(entry);
}

void ErrorHandler::LogError(const std::string& component,
                            const std::string& message,
                            ErrorSeverity severity,
                            ErrorCategory category,
                            const std::map<std::string, std::string>& details) {
    ErrorLog entry;
    entry.severity = severity;
    entry.category = category;
    entry.component = component;
    entry.message = message;
    entry.details = details;
    entry.timestamp = std::chrono::system_clock::now();
    entry.context = capture_context();

    append_log(entry);
}

void ErrorHandler::LogError(ErrorSeverity severity,
                            ErrorCategory category,
                            const std::string& message,
                            const std::map<std::string, std::string>& details) {
    ErrorLog entry;
    entry.severity = severity;
    entry.category = category;
    entry.message = message;
    entry.details = details;
    entry.timestamp = std::chrono::system_clock::now();
    entry.context = capture_context();

    append_log(entry);
}

void ErrorHandler::append_log(const ErrorLog& entry) {
    std::lock_guard<std::mutex> lock(mutex_);
    logs_.push_back(entry);

    switch (entry.severity) {
        case ErrorSeverity::DEBUG:
            statistics_.total_debug_messages += 1;
            break;
        case ErrorSeverity::INFO:
            statistics_.total_info_messages += 1;
            break;
        case ErrorSeverity::WARNING:
            statistics_.total_warnings += 1;
            break;
        case ErrorSeverity::ERROR:
            statistics_.total_errors += 1;
            break;
        case ErrorSeverity::CRITICAL:
        case ErrorSeverity::FATAL:
            statistics_.total_errors += 1;
            statistics_.total_critical += 1;
            break;
    }
}

std::vector<std::pair<std::string, std::string>> ErrorHandler::capture_context() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::pair<std::string, std::string>> result;
    for (const auto& ctx : context_stack_) {
        result.insert(result.end(), ctx.begin(), ctx.end());
    }
    return result;
}

// ====================== ScopedErrorContext ====================================

ScopedErrorContext::ScopedErrorContext(ErrorHandler& handler,
                                       std::string name,
                                       std::map<std::string, std::string> metadata)
    : handler_(&handler), name_(std::move(name)) {
    ErrorContextInfo info;
    info.name = name_;
    info.metadata = std::move(metadata);
    info.timestamp = std::chrono::system_clock::now();

    std::lock_guard<std::mutex> lock(handler_->mutex_);
    handler_->context_history_.push_back(info);
    std::vector<std::pair<std::string, std::string>> pairs;
    pairs.reserve(info.metadata.size());
    for (const auto& [key, value] : info.metadata) {
        pairs.emplace_back(key, value);
    }
    handler_->context_stack_.push_back(std::move(pairs));
}

ScopedErrorContext::ScopedErrorContext(ScopedErrorContext&& other) noexcept
    : handler_(other.handler_), name_(std::move(other.name_)) {
    other.handler_ = nullptr;
}

ScopedErrorContext& ScopedErrorContext::operator=(ScopedErrorContext&& other) noexcept {
    if (this != &other) {
        release();
        handler_ = other.handler_;
        name_ = std::move(other.name_);
        other.handler_ = nullptr;
    }
    return *this;
}

ScopedErrorContext::~ScopedErrorContext() {
    release();
}

void ScopedErrorContext::release() {
    if (!handler_) {
        return;
    }
    std::lock_guard<std::mutex> lock(handler_->mutex_);
    if (!handler_->context_stack_.empty()) {
        handler_->context_stack_.pop_back();
    }
    handler_ = nullptr;
}

// ====================== error_utils ===========================================

namespace error_utils {

std::string get_windows_error_message(DWORD error_code) {
    if (error_code == 0) {
        return "Success";
    }

    LPSTR buffer = nullptr;
    DWORD size = FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |
                                    FORMAT_MESSAGE_IGNORE_INSERTS,
                                nullptr,
                                error_code,
                                MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
                                reinterpret_cast<LPSTR>(&buffer),
                                0,
                                nullptr);
    if (size == 0 || buffer == nullptr) {
        return "Unknown error (" + std::to_string(error_code) + ")";
    }

    std::string message(buffer, buffer + size);
    LocalFree(buffer);
    while (!message.empty() && (message.back() == '\r' || message.back() == '\n')) {
        message.pop_back();
    }
    return message;
}

std::string get_last_windows_error_message() {
    return get_windows_error_message(GetLastError());
}

std::string get_stack_trace() {
    return "Stack trace not available";
}

std::string get_thread_id() {
    std::ostringstream oss;
    oss << std::this_thread::get_id();
    return oss.str();
}

std::string get_process_id() {
    return std::to_string(GetCurrentProcessId());
}

}  // namespace error_utils

}  // namespace utils

