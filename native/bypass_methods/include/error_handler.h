#pragma once

#include <map>
#include <string>

#include "utils/error_handler.h"

using ErrorSeverity = utils::ErrorSeverity;
using ErrorCategory = utils::ErrorCategory;
using RecoveryStrategy = utils::RecoveryStrategy;
using LogLevel = utils::LogLevel;
using ErrorLog = utils::ErrorLog;
using ErrorContextInfo = utils::ErrorContextInfo;
using ErrorStatistics = utils::ErrorStatistics;

class ErrorHandler final {
public:
    static void Initialize() { utils::ErrorHandler::Initialize(); }
    static void Shutdown() { utils::ErrorHandler::Shutdown(); }

    static utils::ErrorHandler& GetInstance() {
        return *utils::ErrorHandler::GetInstance();
    }

    static void LogInfo(const std::string& component,
                        const std::string& message,
                        const std::map<std::string, std::string>& details = {}) {
        GetInstance().LogInfo(component, message, details);
    }

    static void LogInfo(ErrorCategory category,
                        const std::string& message,
                        const std::map<std::string, std::string>& details = {}) {
        GetInstance().LogInfo(category, message, details);
    }

    static void LogWarning(const std::string& component,
                           const std::string& message,
                           const std::map<std::string, std::string>& details = {}) {
        GetInstance().LogWarning(component, message, details);
    }

    static void LogWarning(ErrorCategory category,
                           const std::string& message,
                           const std::map<std::string, std::string>& details = {}) {
        GetInstance().LogWarning(category, message, details);
    }

    static void LogError(const std::string& component,
                         const std::string& message,
                         ErrorSeverity severity,
                         ErrorCategory category,
                         const std::map<std::string, std::string>& details = {}) {
        GetInstance().LogError(component, message, severity, category, details);
    }

    static void LogError(ErrorSeverity severity,
                         ErrorCategory category,
                         const std::string& message,
                         const std::map<std::string, std::string>& details = {}) {
        GetInstance().LogError(severity, category, message, details);
    }
};
