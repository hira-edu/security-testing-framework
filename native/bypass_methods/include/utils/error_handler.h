#pragma once

#include <windows.h>

#include <cstdint>

#ifdef ERROR
#undef ERROR
#endif
#ifdef WARNING
#undef WARNING
#endif
#ifdef INFO
#undef INFO
#endif
#ifdef DEBUG
#undef DEBUG
#endif
#ifdef CRITICAL
#undef CRITICAL
#endif
#ifdef FATAL
#undef FATAL
#endif

#include <atomic>
#include <chrono>
#include <map>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace utils {

enum class ErrorSeverity : std::uint8_t {
    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3,
    CRITICAL = 4,
    FATAL = 5
};

enum class ErrorCategory : std::uint8_t {
    GENERAL = 0,
    WINDOWS_API = 1,
    GRAPHICS = 2,
    MEMORY = 3,
    NETWORK = 4,
    FILE_IO = 5,
    SECURITY = 6,
    PERFORMANCE = 7,
    HOOK = 8,
    SYSTEM = 9,
    SIGNATURE_PARSING = 10,
    INVALID_PARAMETER = 11,
    CAPTURE = 12,
    INJECTION = 13,
    DIRECTX = 14,
    COM = 15,
    DEPENDENCY = 16,
    EXCEPTION = 17,
    THREADING = 18,
    SYNCHRONIZATION = 19,
    UNKNOWN = 20
};

enum class RecoveryStrategy : std::uint8_t {
    NONE = 0,
    AUTOMATIC = 1,
    MANUAL = 2,
    FATAL = 3
};

enum class LogLevel : std::uint8_t {
    DEBUG = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3,
    CRITICAL = 4,
    FATAL = 5
};

struct ErrorContext {
    void set(const std::string& key, const std::string& value);
    bool contains(const std::string& key) const;
    std::string get(const std::string& key) const;
    void clear();
    bool empty() const;
    const std::unordered_map<std::string, std::string>& values() const;

private:
    std::unordered_map<std::string, std::string> values_;
};

struct ErrorContextInfo {
    std::string name;
    std::map<std::string, std::string> metadata;
    std::chrono::system_clock::time_point timestamp;
};

struct ErrorLog {
    ErrorSeverity severity;
    ErrorCategory category;
    std::string component;
    std::string message;
    std::map<std::string, std::string> details;
    std::string function;
    std::string file;
    int line = 0;
    DWORD windows_error = 0;
    std::chrono::system_clock::time_point timestamp;
    std::vector<std::pair<std::string, std::string>> context;
};

struct ErrorStatistics {
    std::size_t total_errors = 0;
    std::size_t total_warnings = 0;
    std::size_t total_info_messages = 0;
    std::size_t total_debug_messages = 0;
    std::size_t total_critical = 0;
};

class ScopedErrorContext;

class ErrorHandler {
public:
    static void Initialize();
    static void Shutdown();
    static ErrorHandler* GetInstance();

    bool is_initialized() const;

    void set_minimum_log_level(LogLevel level);
    LogLevel get_minimum_log_level() const;

    void ClearLogs();
    std::vector<ErrorLog> GetLogs() const;
    std::vector<ErrorLog> GetErrors() const;
    std::vector<ErrorContextInfo> GetContexts() const;
    ErrorStatistics get_error_statistics() const;

    ScopedErrorContext CreateContext(const std::string& name,
                                     std::map<std::string, std::string> metadata = {});
    void set_error_context(const ErrorContext& context);
    void clear_error_context();

    void report_error(ErrorSeverity severity,
                      ErrorCategory category,
                      const std::string& message,
                      const std::string& function = "",
                      const std::string& file = "",
                      int line = 0,
                      DWORD windows_error = 0);

    void debug(const std::string& message,
               ErrorCategory category = ErrorCategory::GENERAL,
               const std::string& function = "",
               const std::string& file = "",
               int line = 0);

    void info(const std::string& message,
              ErrorCategory category = ErrorCategory::GENERAL,
              const std::string& function = "",
              const std::string& file = "",
              int line = 0);

    void warning(const std::string& message,
               ErrorCategory category = ErrorCategory::GENERAL,
               const std::string& function = "",
               const std::string& file = "",
               int line = 0,
               DWORD windows_error = 0);

    void error(const std::string& message,
               ErrorCategory category = ErrorCategory::GENERAL,
               const std::string& function = "",
               const std::string& file = "",
               int line = 0,
               DWORD windows_error = 0,
               RecoveryStrategy strategy = RecoveryStrategy::NONE);

    void critical(const std::string& message,
                  ErrorCategory category = ErrorCategory::GENERAL,
                  const std::string& function = "",
                  const std::string& file = "",
                  int line = 0,
                  DWORD windows_error = 0);

    void fatal(const std::string& message,
               ErrorCategory category = ErrorCategory::GENERAL,
               const std::string& function = "",
               const std::string& file = "",
               int line = 0,
               DWORD windows_error = 0);

    void LogInfo(const std::string& component,
                 const std::string& message,
                 const std::map<std::string, std::string>& details = {});
    void LogInfo(ErrorCategory category,
                 const std::string& message,
                 const std::map<std::string, std::string>& details = {});

    void LogWarning(const std::string& component,
                    const std::string& message,
                    const std::map<std::string, std::string>& details = {});
    void LogWarning(ErrorCategory category,
                    const std::string& message,
                    const std::map<std::string, std::string>& details = {});

    void LogError(const std::string& component,
                  const std::string& message,
                  ErrorSeverity severity,
                  ErrorCategory category,
                  const std::map<std::string, std::string>& details = {});
    void LogError(ErrorSeverity severity,
                  ErrorCategory category,
                  const std::string& message,
                  const std::map<std::string, std::string>& details = {});

private:
    ErrorHandler();
    ~ErrorHandler() = default;

    ErrorHandler(const ErrorHandler&) = delete;
    ErrorHandler& operator=(const ErrorHandler&) = delete;

    void append_log(const ErrorLog& entry);
    bool should_emit(ErrorSeverity severity) const;
    std::vector<std::pair<std::string, std::string>> capture_context() const;

    std::atomic<bool> initialized_;
    std::atomic<LogLevel> minimum_level_;

    mutable std::mutex mutex_;
    std::vector<ErrorLog> logs_;
    std::vector<ErrorContextInfo> context_history_;
    std::vector<std::vector<std::pair<std::string, std::string>>> context_stack_;
    ErrorStatistics statistics_;
};

class ScopedErrorContext {
public:
    ScopedErrorContext(ErrorHandler& handler,
                       std::string name,
                       std::map<std::string, std::string> metadata = {});
    ScopedErrorContext(ScopedErrorContext&& other) noexcept;
    ScopedErrorContext& operator=(ScopedErrorContext&& other) noexcept;
    ScopedErrorContext(const ScopedErrorContext&) = delete;
    ScopedErrorContext& operator=(const ScopedErrorContext&) = delete;
    ~ScopedErrorContext();

private:
    void release();

    ErrorHandler* handler_;
    std::string name_;
};

namespace error_utils {

std::string get_windows_error_message(DWORD error_code);
std::string get_last_windows_error_message();
std::string get_stack_trace();
std::string get_thread_id();
std::string get_process_id();

}  // namespace error_utils

#define ERROR_REPORT(severity, category, message, windows_error) \
    utils::ErrorHandler::GetInstance()->report_error(            \
        severity, category, message, __FUNCTION__, __FILE__, __LINE__, windows_error)

#define ERROR_DEBUG(message, category) \
    utils::ErrorHandler::GetInstance()->debug(message, category, __FUNCTION__, __FILE__, __LINE__)

#define ERROR_INFO(message, category) \
    utils::ErrorHandler::GetInstance()->info(message, category, __FUNCTION__, __FILE__, __LINE__)

#define ERROR_WARNING(message, category) \
    utils::ErrorHandler::GetInstance()->warning(message, category, __FUNCTION__, __FILE__, __LINE__)

#define ERROR_ERROR(message, category, windows_error) \
    utils::ErrorHandler::GetInstance()->error(message, category, __FUNCTION__, __FILE__, __LINE__, windows_error)

#define ERROR_CRITICAL(message, category, windows_error) \
    utils::ErrorHandler::GetInstance()->critical(message, category, __FUNCTION__, __FILE__, __LINE__, windows_error)

#define ERROR_FATAL(message, category, windows_error) \
    utils::ErrorHandler::GetInstance()->fatal(message, category, __FUNCTION__, __FILE__, __LINE__, windows_error)

#define ERROR_CONTEXT(name) \
    utils::ScopedErrorContext error_context_##__LINE__(*utils::ErrorHandler::GetInstance(), name)

}  // namespace utils


