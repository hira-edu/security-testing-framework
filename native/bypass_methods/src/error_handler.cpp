#include "include/error_handler.h"

#include <algorithm>
#include <iterator>

namespace {
std::mutex g_error_handler_instance_mutex;
ErrorHandler* g_error_handler_instance = nullptr;
} // namespace

// === ErrorContext ===========================================================

void ErrorContext::set(const std::string& key, const std::string& value) {
    values_[key] = value;
}

bool ErrorContext::contains(const std::string& key) const {
    return values_.find(key) != values_.end();
}

std::string ErrorContext::get(const std::string& key) const {
    auto it = values_.find(key);
    return it == values_.end() ? std::string{} : it->second;
}

void ErrorContext::remove(const std::string& key) {
    values_.erase(key);
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

// === ErrorHandler ===========================================================

static int ToLogLevelValue(LogLevel level) {
    return static_cast<int>(level);
}

static int ToSeverityValue(ErrorSeverity severity) {
    return static_cast<int>(severity);
}

utils::ErrorSeverity ErrorHandler::ToNativeSeverity(ErrorSeverity severity) {
    switch (severity) {
        case ErrorSeverity::DEBUG: return utils::ErrorSeverity::DEBUG;
        case ErrorSeverity::INFO: return utils::ErrorSeverity::INFO;
        case ErrorSeverity::WARNING: return utils::ErrorSeverity::WARNING;
        case ErrorSeverity::ERROR: return utils::ErrorSeverity::ERROR;
        case ErrorSeverity::CRITICAL: return utils::ErrorSeverity::CRITICAL;
        case ErrorSeverity::FATAL: return utils::ErrorSeverity::FATAL;
    }
    return utils::ErrorSeverity::INFO;
}

utils::ErrorCategory ErrorHandler::ToNativeCategory(ErrorCategory category) {
    switch (category) {
        case ErrorCategory::GENERAL: return utils::ErrorCategory::GENERAL;
        case ErrorCategory::WINDOWS_API: return utils::ErrorCategory::WINDOWS_API;
        case ErrorCategory::GRAPHICS: return utils::ErrorCategory::GRAPHICS;
        case ErrorCategory::MEMORY: return utils::ErrorCategory::MEMORY;
        case ErrorCategory::NETWORK: return utils::ErrorCategory::NETWORK;
        case ErrorCategory::FILE_IO:
        case ErrorCategory::FILE_SYSTEM: return utils::ErrorCategory::FILE_IO;
        case ErrorCategory::SECURITY: return utils::ErrorCategory::SECURITY;
        case ErrorCategory::PERFORMANCE: return utils::ErrorCategory::PERFORMANCE;
        case ErrorCategory::HOOK: return utils::ErrorCategory::HOOK;
        case ErrorCategory::SYSTEM:
        case ErrorCategory::PROCESS:
        case ErrorCategory::DEPENDENCY:
        case ErrorCategory::EXCEPTION: return utils::ErrorCategory::SYSTEM;
        case ErrorCategory::SIGNATURE_PARSING: return utils::ErrorCategory::UNKNOWN;
        case ErrorCategory::INVALID_PARAMETER: return utils::ErrorCategory::UNKNOWN;
        case ErrorCategory::CAPTURE: return utils::ErrorCategory::CAPTURE;
        case ErrorCategory::INJECTION: return utils::ErrorCategory::INJECTION;
        case ErrorCategory::DIRECTX: return utils::ErrorCategory::DIRECTX;
        case ErrorCategory::COM: return utils::ErrorCategory::COM;
        case ErrorCategory::THREADING: return utils::ErrorCategory::THREADING;
        case ErrorCategory::SYNCHRONIZATION: return utils::ErrorCategory::SYNCHRONIZATION;
        case ErrorCategory::UNKNOWN: return utils::ErrorCategory::UNKNOWN;
    }
    return utils::ErrorCategory::UNKNOWN;
}

ErrorHandler::ErrorHandler()
    : initialized_(true),
      minimum_log_level_(LogLevel::INFO),
      statistics_{},
      native_handler_(&utils::ErrorHandler::get_instance()) {
    logs_.clear();
    contexts_.clear();
    current_context_.clear();
}

void ErrorHandler::Initialize() {
    std::lock_guard<std::mutex> lock(g_error_handler_instance_mutex);
    if (!g_error_handler_instance) {
        g_error_handler_instance = new ErrorHandler();
    } else {
        g_error_handler_instance->initialized_ = true;
        g_error_handler_instance->ClearLogs();
    }
    (void)utils::ErrorHandler::get_instance();
}

void ErrorHandler::Shutdown() {
    std::lock_guard<std::mutex> lock(g_error_handler_instance_mutex);
    delete g_error_handler_instance;
    g_error_handler_instance = nullptr;
}

ErrorHandler& ErrorHandler::GetInstance() {
    std::lock_guard<std::mutex> lock(g_error_handler_instance_mutex);
    if (!g_error_handler_instance) {
        g_error_handler_instance = new ErrorHandler();
    }
    return *g_error_handler_instance;
}

bool ErrorHandler::is_initialized() const {
    return initialized_;
}

void ErrorHandler::set_minimum_log_level(LogLevel level) {
    std::lock_guard<std::mutex> lock(mutex_);
    minimum_log_level_ = level;
}

LogLevel ErrorHandler::get_minimum_log_level() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return minimum_log_level_;
}

void ErrorHandler::ClearLogs() {
    std::lock_guard<std::mutex> lock(mutex_);
    logs_.clear();
    contexts_.clear();
    statistics_ = {};
    current_context_.clear();
}

std::vector<ErrorLog> ErrorHandler::GetLogs() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return logs_;
}

std::vector<ErrorLog> ErrorHandler::GetErrors() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<ErrorLog> filtered;
    std::copy_if(logs_.begin(), logs_.end(), std::back_inserter(filtered),
                 [](const ErrorLog& entry) {
                     return entry.severity == ErrorSeverity::ERROR ||
                            entry.severity == ErrorSeverity::CRITICAL ||
                            entry.severity == ErrorSeverity::FATAL;
                 });
    return filtered;
}

std::vector<ErrorContextInfo> ErrorHandler::GetContexts() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return contexts_;
}

ErrorStatistics ErrorHandler::get_error_statistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return statistics_;
}

ScopedErrorContext ErrorHandler::CreateContext(
    const std::string& name,
    std::map<std::string, std::string> metadata) {
    return ScopedErrorContext(*this, name, std::move(metadata));
}

void ErrorHandler::set_error_context(const ErrorContext& context) {
    std::lock_guard<std::mutex> lock(mutex_);
    current_context_ = context;
}

void ErrorHandler::clear_error_context() {
    std::lock_guard<std::mutex> lock(mutex_);
    current_context_.clear();
}

void ErrorHandler::report_error(ErrorSeverity severity,
                                ErrorCategory category,
                                const std::string& message,
                                const std::string& function,
                                const std::string& file,
                                int line,
                                DWORD windows_error) {
    log_internal("", severity, category, message, {}, function, file, line, windows_error);
}

void ErrorHandler::debug(const std::string& message,
                         ErrorCategory category,
                         const std::string& function,
                         const std::string& file,
                         int line) {
    log_internal("", ErrorSeverity::DEBUG, category, message, {}, function, file, line, 0);
}

void ErrorHandler::info(const std::string& message,
                        ErrorCategory category,
                        const std::string& function,
                        const std::string& file,
                        int line) {
    log_internal("", ErrorSeverity::INFO, category, message, {}, function, file, line, 0);
}

void ErrorHandler::warning(const std::string& message,
                           ErrorCategory category,
                           const std::string& function,
                           const std::string& file,
                           int line,
                           DWORD windows_error) {
    log_internal("", ErrorSeverity::WARNING, category, message, {}, function, file, line, windows_error);
}

void ErrorHandler::error(const std::string& message,
                         ErrorCategory category,
                         const std::string& function,
                         const std::string& file,
                         int line,
                         DWORD windows_error,
                         RecoveryStrategy) {
    log_internal("", ErrorSeverity::ERROR, category, message, {}, function, file, line, windows_error);
}

void ErrorHandler::critical(const std::string& message,
                            ErrorCategory category,
                            const std::string& function,
                            const std::string& file,
                            int line,
                            DWORD windows_error) {
    log_internal("", ErrorSeverity::CRITICAL, category, message, {}, function, file, line, windows_error);
}

void ErrorHandler::fatal(const std::string& message,
                         ErrorCategory category,
                         const std::string& function,
                         const std::string& file,
                         int line,
                         DWORD windows_error) {
    log_internal("", ErrorSeverity::FATAL, category, message, {}, function, file, line, windows_error);
}

void ErrorHandler::LogInfo(const std::string& component,
                           const std::string& message,
                           const std::map<std::string, std::string>& details) {
    GetInstance().log_message(ErrorSeverity::INFO, ErrorCategory::GENERAL, component, message, details);
}

void ErrorHandler::LogInfo(ErrorCategory category,
                           const std::string& message,
                           const std::map<std::string, std::string>& details) {
    GetInstance().log_message(ErrorSeverity::INFO, category, "", message, details);
}

void ErrorHandler::LogWarning(const std::string& component,
                              const std::string& message,
                              const std::map<std::string, std::string>& details) {
    GetInstance().log_message(ErrorSeverity::WARNING, ErrorCategory::GENERAL, component, message, details);
}

void ErrorHandler::LogWarning(ErrorCategory category,
                              const std::string& message,
                              const std::map<std::string, std::string>& details) {
    GetInstance().log_message(ErrorSeverity::WARNING, category, "", message, details);
}

void ErrorHandler::LogError(const std::string& component,
                            const std::string& message,
                            ErrorSeverity severity,
                            ErrorCategory category,
                            const std::map<std::string, std::string>& details,
                            DWORD windows_error) {
    GetInstance().log_message(severity, category, component, message, details, "", "", 0, windows_error);
}

void ErrorHandler::LogError(ErrorSeverity severity,
                            ErrorCategory category,
                            const std::string& message,
                            const std::map<std::string, std::string>& details,
                            DWORD windows_error) {
    GetInstance().log_message(severity, category, "", message, details, "", "", 0, windows_error);
}

void ErrorHandler::log_internal(const std::string& component,
                                ErrorSeverity severity,
                                ErrorCategory category,
                                const std::string& message,
                                const std::map<std::string, std::string>& details,
                                const std::string& function,
                                const std::string& file,
                                int line,
                                DWORD windows_error) {
    if (ToSeverityValue(severity) < ToLogLevelValue(minimum_log_level_)) {
        return;
    }

    std::unique_lock<std::mutex> lock(mutex_);

    ErrorLog entry;
    entry.severity = severity;
    entry.category = category;
    entry.component = component;
    entry.message = message;
    entry.details = details;
    entry.function = function;
    entry.file = file;
    entry.line = line;
    entry.windows_error = windows_error;
    entry.timestamp = std::chrono::system_clock::now();

    for (const auto& pair : current_context_.values()) {
        entry.context.emplace_back(pair.first, pair.second);
    }

    logs_.push_back(entry);

    switch (severity) {
        case ErrorSeverity::DEBUG: statistics_.total_debug_messages++; break;
        case ErrorSeverity::INFO: statistics_.total_info_messages++; break;
        case ErrorSeverity::WARNING: statistics_.total_warnings++; break;
        case ErrorSeverity::ERROR:
            statistics_.total_errors++;
            break;
        case ErrorSeverity::CRITICAL:
            statistics_.total_errors++;
            statistics_.total_critical++;
            break;
        case ErrorSeverity::FATAL:
            statistics_.total_errors++;
            statistics_.total_critical++;
            break;
    }

    lock.unlock();

    // Forward to native handler for consolidated logging.
    auto native_category = ToNativeCategory(category);
    auto native_severity = ToNativeSeverity(severity);
    auto& native = utils::ErrorHandler::get_instance();

    switch (native_severity) {
        case utils::ErrorSeverity::DEBUG:
            native.debug(message, native_category, function, file, line);
            break;
        case utils::ErrorSeverity::INFO:
            native.info(message, native_category, function, file, line);
            break;
        case utils::ErrorSeverity::WARNING:
            native.warning(message, native_category, function, file, line);
            break;
        case utils::ErrorSeverity::ERROR:
            native.error(message, native_category, function, file, line, windows_error);
            break;
        case utils::ErrorSeverity::CRITICAL:
            native.critical(message, native_category, function, file, line, windows_error);
            break;
        case utils::ErrorSeverity::FATAL:
            native.fatal(message, native_category, function, file, line, windows_error);
            break;
    }
}

// === ScopedErrorContext =====================================================

ScopedErrorContext::ScopedErrorContext(ErrorHandler& handler,
                                       std::string name,
                                       std::map<std::string, std::string> metadata)
    : handler_(&handler),
      name_(std::move(name)),
      metadata_(std::move(metadata)),
      active_(true),
      native_context_(std::make_unique<utils::error_utils::ScopedErrorContext>(name_)) {
    ErrorContext context;
    for (const auto& pair : metadata_) {
        context.set(pair.first, pair.second);
    }

    {
        std::lock_guard<std::mutex> lock(handler.mutex_);
        ErrorContextInfo info;
        info.name = name_;
        info.metadata = metadata_;
        info.timestamp = std::chrono::system_clock::now();
        handler.contexts_.push_back(std::move(info));
        handler.current_context_ = context;
    }
}

ScopedErrorContext::ScopedErrorContext(ScopedErrorContext&& other) noexcept
    : handler_(other.handler_),
      name_(std::move(other.name_)),
      metadata_(std::move(other.metadata_)),
      active_(other.active_),
      native_context_(std::move(other.native_context_)) {
    other.active_ = false;
    other.handler_ = nullptr;
}

ScopedErrorContext& ScopedErrorContext::operator=(ScopedErrorContext&& other) noexcept {
    if (this != &other) {
        release();
        handler_ = other.handler_;
        name_ = std::move(other.name_);
        metadata_ = std::move(other.metadata_);
        active_ = other.active_;
        native_context_ = std::move(other.native_context_);
        other.active_ = false;
        other.handler_ = nullptr;
    }
    return *this;
}

ScopedErrorContext::~ScopedErrorContext() {
    release();
}

void ScopedErrorContext::release() {
    if (active_ && handler_) {
        handler_->clear_error_context();
        active_ = false;
    }
}
