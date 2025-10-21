#pragma once

#include <windows.h>

#include <atomic>
#include <chrono>
#include <cstdint>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "utils/error_handler.h"

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
    PROCESS = 20,
    UNKNOWN = 21
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
    void remove(const std::string& key);
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
    ErrorSeverity severity = ErrorSeverity::INFO;
    ErrorCategory category = ErrorCategory::GENERAL;
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
    static ErrorHandler& GetInstance();

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

    static void LogInfo(const std::string& component,
                        const std::string& message,
                        const std::map<std::string, std::string>& details = {});

    static void LogInfo(ErrorCategory category,
                        const std::string& message,
                        const std::map<std::string, std::string>& details = {});

    static void LogWarning(const std::string& component,
                           const std::string& message,
                           const std::map<std::string, std::string>& details = {});

    static void LogWarning(ErrorCategory category,
                           const std::string& message,
                           const std::map<std::string, std::string>& details = {});

    static void LogError(const std::string& component,
                         const std::string& message,
                         ErrorSeverity severity,
                         ErrorCategory category,
                         const std::map<std::string, std::string>& details = {},
                         DWORD windows_error = 0);

    static void LogError(ErrorSeverity severity,
                         ErrorCategory category,
                         const std::string& message,
                         const std::map<std::string, std::string>& details = {},
                         DWORD windows_error = 0);

private:
    ErrorHandler();

    static utils::ErrorSeverity ToNativeSeverity(ErrorSeverity severity);
    static utils::ErrorCategory ToNativeCategory(ErrorCategory category);

    void log_message(ErrorSeverity severity,
                     ErrorCategory category,
                     const std::string& component,
                     const std::string& message,
                     const std::map<std::string, std::string>& details,
                     const std::string& function = "",
                     const std::string& file = "",
                     int line = 0,
                     DWORD windows_error = 0);

    void log_internal(const std::string& component,
                      ErrorSeverity severity,
                      ErrorCategory category,
                      const std::string& message,
                      const std::map<std::string, std::string>& details,
                      const std::string& function = "",
                      const std::string& file = "",
                      int line = 0,
                      DWORD windows_error = 0);

    mutable std::mutex mutex_;
    bool initialized_;
    LogLevel minimum_log_level_;
    ErrorStatistics statistics_;
    std::vector<ErrorLog> logs_;
    std::vector<ErrorContextInfo> contexts_;
    ErrorContext current_context_;
    utils::ErrorHandler* native_handler_;
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
    std::map<std::string, std::string> metadata_;
    bool active_;
    std::unique_ptr<utils::error_utils::ScopedErrorContext> native_context_;
};
