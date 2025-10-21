#pragma once

#include <windows.h>
#include <string>
#include <vector>
#include <iostream>
#include <algorithm> // For std::copy, std::fill_n

// Include the new trampoline utilities
#include "trampoline_utils.h"

// Define JMP_REL32_SIZE if not already defined
#ifndef JMP_REL32_SIZE
#define JMP_REL32_SIZE 5
#endif

class Hook {
public:
    Hook(std::string moduleName, std::string functionName, void* detourFunction)
        : moduleName_(std::move(moduleName)),
          functionName_(std::move(functionName)),
          detourFunction_(detourFunction),
          originalFunction_(nullptr),
          trampolineFunction_(nullptr),
          prologueSize_(0),
          copiedPrologueBytes_(nullptr),
          isInstalled_(false) {
        // originalBytes_ stores the JMP that overwrites the start of the target function
        originalBytes_ = new BYTE[JMP_REL32_SIZE];
        std::fill_n(originalBytes_, JMP_REL32_SIZE, 0xCC); // Initialize to INT3
    }

    virtual ~Hook() {
        if (isInstalled_) {
            if (!Uninstall()) {
                std::cerr << "Hook::~Hook - Failed to uninstall hook for " << functionName_
                          << " at address " << originalFunction_ << " during destruction." << std::endl;
            }
        }
        delete[] originalBytes_;
        delete[] copiedPrologueBytes_; // Ensure this is cleaned up
    }

    // Prevent copying and assignment
    Hook(const Hook&) = delete;
    Hook& operator=(const Hook&) = delete;

    virtual bool Install() {
        if (isInstalled_) {
            std::cout << "Hook::Install - Hook for " << functionName_ << " already installed." << std::endl;
            return true;
        }

        HMODULE hModule = GetModuleHandleA(moduleName_.c_str());
        if (!hModule) {
            std::cerr << "Hook::Install - Failed to get module handle for: " << moduleName_ << ". Error: " << GetLastError() << std::endl;
            return false;
        }

        originalFunction_ = GetProcAddress(hModule, functionName_.c_str());
        if (!originalFunction_) {
            std::cerr << "Hook::Install - Failed to get address for '" << functionName_ << "' in module '" << moduleName_ << "'. Error: " << GetLastError() << std::endl;
            return false;
        }

        // 1. Determine prologue size and allocate buffer for copied prologue bytes
        // Using a fixed minimum of JMP_REL32_SIZE for now due to CalculateMinimumPrologueSize simplification.
        // A real scenario might involve a more dynamic calculation here.
        // Let's use a slightly larger fixed size for more safety margin if CalculateMinimumPrologueSize is too basic.
        // For example, 6 to 8 bytes, but ensure TrampolineUtils::CalculateMinimumPrologueSize is respected.
        prologueSize_ = UndownUnlock::TrampolineUtils::CalculateMinimumPrologueSize(originalFunction_, JMP_REL32_SIZE + 1); // e.g., 6 bytes
        if (prologueSize_ == 0) { // CalculateMinimumPrologueSize might return 0 on error in a real impl.
             std::cerr << "Hook::Install - Failed to calculate prologue size for " << functionName_ << std::endl;
             return false;
        }
        delete[] copiedPrologueBytes_; // Delete if previously allocated (e.g. failed install attempt)
        copiedPrologueBytes_ = new BYTE[prologueSize_];
        std::fill_n(copiedPrologueBytes_, prologueSize_, 0xCC);


        // 2. Allocate the trampoline. copiedPrologueBytes_ will be filled by AllocateTrampoline.
        if (!UndownUnlock::TrampolineUtils::AllocateTrampoline(originalFunction_, prologueSize_, copiedPrologueBytes_, trampolineFunction_)) {
            std::cerr << "Hook::Install - Failed to allocate trampoline for " << functionName_ << std::endl;
            originalFunction_ = nullptr; // Reset on failure
            delete[] copiedPrologueBytes_;
            copiedPrologueBytes_ = nullptr;
            return false;
        }

        // 3. Write the JMP from the original function to our detour function.
        //    originalBytes_ (class member) will store the bytes overwritten by this JMP.
        if (!UndownUnlock::TrampolineUtils::WriteAbsoluteJump(originalFunction_, detourFunction_, originalBytes_, JMP_REL32_SIZE)) {
            std::cerr << "Hook::Install - Failed to write JMP for " << functionName_ << std::endl;
            UndownUnlock::TrampolineUtils::FreeTrampoline(trampolineFunction_); // Clean up allocated trampoline
            trampolineFunction_ = nullptr;
            originalFunction_ = nullptr;
            delete[] copiedPrologueBytes_;
            copiedPrologueBytes_ = nullptr;
            return false;
        }

        isInstalled_ = true;
        std::cout << "Hook::Install - Hook successfully installed for: " << functionName_ << " in " << moduleName_
                  << ". Trampoline at: " << trampolineFunction_ << std::endl;
        return true;
    }

    virtual bool Uninstall() {
        if (!isInstalled_) {
            // std::cout << "Hook::Uninstall - Hook for " << functionName_ << " not installed or already uninstalled." << std::endl;
            return true;
        }
        if (!originalFunction_) { // Should not happen if isInstalled_ is true
            std::cerr << "Hook::Uninstall - Cannot uninstall " << functionName_ << ", original function address is null but hook marked installed." << std::endl;
            isInstalled_ = false;
            return false;
        }

        // 1. Restore the original bytes at the start of the target function
        if (!UndownUnlock::TrampolineUtils::RestoreOriginalBytes(originalFunction_, originalBytes_, JMP_REL32_SIZE)) {
            std::cerr << "Hook::Uninstall - Failed to restore original bytes for: " << functionName_
                      << " at " << originalFunction_ << ". Critical error, function state is corrupt." << std::endl;
            // Even if this fails, we should try to free the trampoline.
            // The hook is in a bad state.
        }

        // 2. Free the trampoline memory
        if (trampolineFunction_) {
            if (!UndownUnlock::TrampolineUtils::FreeTrampoline(trampolineFunction_)) {
                std::cerr << "Hook::Uninstall - Failed to free trampoline memory for " << functionName_
                          << " at " << trampolineFunction_ << "." << std::endl;
            }
            trampolineFunction_ = nullptr;
        }

        delete[] copiedPrologueBytes_;
        copiedPrologueBytes_ = nullptr;

        isInstalled_ = false; // Mark as uninstalled
        std::cout << "Hook::Uninstall - Hook successfully uninstalled for: " << functionName_ << std::endl;
        return true; // Return true even if some cleanup steps had issues, as we attempted.
    }

    bool IsInstalled() const {
        return isInstalled_;
    }

    template<typename T>
    T GetOriginalFunctionTrampoline() const {
        if (!isInstalled_ || !trampolineFunction_) {
            // If hook is not installed, or trampoline somehow not set,
            // returning originalFunction_ is problematic as it might be hooked by someone else
            // or could be the raw function. For now, this indicates an error or unhooked state.
            // A robust system might throw or return an error code.
            // std::cerr << "Warning: Attempting to get trampoline for uninstalled or failed hook: " << functionName_ << std::endl;
            // Returning originalFunction_ directly is only safe if truly unhooked.
            // If trampolineFunction_ is null but isInstalled_ is true, it's an error state.
            return reinterpret_cast<T>(originalFunction_);
        }
        return reinterpret_cast<T>(trampolineFunction_);
    }

    const std::string& GetFunctionName() const {
        return functionName_;
    }

    const std::string& GetModuleName() const {
        return moduleName_;
    }

protected:
    std::string moduleName_;
    std::string functionName_;
    void* detourFunction_;      // Our detour function
    LPVOID originalFunction_;   // Address of the original function being hooked

    LPVOID trampolineFunction_; // Address of the allocated trampoline
    SIZE_T prologueSize_;       // Number of original instruction bytes copied to the trampoline
    PBYTE copiedPrologueBytes_; // Buffer holding those copied original instruction bytes

    PBYTE originalBytes_;       // Buffer holding the bytes overwritten by the JMP at the start of originalFunction_ (size JMP_REL32_SIZE)
    bool isInstalled_;
};
