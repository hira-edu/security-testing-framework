#include "../../../include/hooks/trampoline_utils.h"
#include <windows.h>
#include <iostream> // For debugging
#include <stdexcept> // For exceptions if needed, though returning bool for now

// Define JMP_REL32_SIZE if not already defined (e.g. in a common header)
#ifndef JMP_REL32_SIZE
#define JMP_REL32_SIZE 5
#endif

// Define JMP_ABS_X64_SIZE for potential future x64 (though current code is x86 focused)
#ifndef JMP_ABS_X64_SIZE
#define JMP_ABS_X64_SIZE 14 // Example: MOV RAX, addr; JMP RAX
#endif


namespace UndownUnlock {
    namespace TrampolineUtils {

        // Simplified: Returns a fixed minimum size.
        // A proper implementation requires a disassembler.
        SIZE_T CalculateMinimumPrologueSize(LPCVOID functionAddress, SIZE_T minBytesToCopy) {
            // TODO: Implement basic instruction scanning if possible, or use a small disassembler library.
            // For now, ensuring it's at least JMP_REL32_SIZE for safety if we are overwriting with a JMP.
            // This function's purpose is to determine how many bytes of the ORIGINAL function
            // need to be copied to the trampoline without cutting an instruction.
            // It's not about the size of the JMP we *write* into the original function.
            // It's about how many original instructions we need to preserve.

            // Simplistic approach: return the requested minBytesToCopy, ensuring it's reasonable.
            // A common safe minimum for simple hooks is 5-7 bytes.
            // If minBytesToCopy is already 5 (for our JMP), then this is fine for that purpose.
            // The actual number of bytes to copy for the trampoline *must* be instruction-aligned.
            // For this simplified version, we'll assume the caller (Hook class) will decide a prologue size
            // (e.g. 5, 6, or more bytes) and this function just validates it minimally or would perform analysis.
            // Given the constraints, we'll just return a fixed known-safe-minimum like 5 or 6.
            // The Hook class will manage its `prologueSize_` member. This util function
            // would be more useful if it actually disassembled.
            // For now, let's make it simple: ensure at least 5 bytes.
            if (minBytesToCopy < JMP_REL32_SIZE) {
                return JMP_REL32_SIZE;
            }
            // std::cout << "[TrampolineUtils] CalculateMinimumPrologueSize: Using fixed size: " << minBytesToCopy << std::endl;
            return minBytesToCopy; // Return the requested size, assuming it's somewhat safe.
        }


        bool AllocateTrampoline(
            LPCVOID targetFunction,
            SIZE_T prologueSize,      // How many bytes of original function to copy
            PBYTE copiedPrologueBytes,// Buffer to store the copied prologue (allocated by caller)
            LPVOID& trampolineAddress // Out: Address of the allocated trampoline
        ) {
            if (!targetFunction || !copiedPrologueBytes || prologueSize == 0) {
                std::cerr << "[TrampolineUtils::AllocateTrampoline] Invalid arguments." << std::endl;
                return false;
            }

            // 1. Read prologueSize bytes from targetFunction into copiedPrologueBytes buffer
            DWORD oldProtectRead;
            if (!VirtualProtect(const_cast<LPVOID>(targetFunction), prologueSize, PAGE_EXECUTE_READ, &oldProtectRead)) {
                 std::cerr << "[TrampolineUtils::AllocateTrampoline] VirtualProtect (read) failed. Error: " << GetLastError() << std::endl;
                return false;
            }
            memcpy(copiedPrologueBytes, targetFunction, prologueSize);
            VirtualProtect(const_cast<LPVOID>(targetFunction), prologueSize, oldProtectRead, &oldProtectRead); // Restore protection


            // 2. Allocate executable memory for the trampoline
            // Trampoline size = prologueSize (original instructions) + JMP_REL32_SIZE (jmp back to original_func + prologueSize)
            SIZE_T trampolineTotalSize = prologueSize + JMP_REL32_SIZE;
            trampolineAddress = VirtualAlloc(NULL, trampolineTotalSize, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
            if (!trampolineAddress) {
                std::cerr << "[TrampolineUtils::AllocateTrampoline] VirtualAlloc failed. Error: " << GetLastError() << std::endl;
                return false;
            }

            // 3. Write the copiedPrologueBytes to the start of the trampoline
            memcpy(trampolineAddress, copiedPrologueBytes, prologueSize);

            // 4. Append a JMP from the trampoline (trampolineAddress + prologueSize)
            //    back to (targetFunction + prologueSize)
            PBYTE jmpLocationInTrampoline = static_cast<PBYTE>(trampolineAddress) + prologueSize;
            LPCVOID jumpBackTargetAddress = static_cast<LPCBYTE>(targetFunction) + prologueSize;

            // Calculate relative offset for the JMP
            // Offset = Destination - (Source + 5)
            // Destination = jumpBackTargetAddress
            // Source = jmpLocationInTrampoline (address of the 0xE9 byte)
            DWORD relativeOffset = (DWORD)jumpBackTargetAddress - ((DWORD)jmpLocationInTrampoline + JMP_REL32_SIZE);

            jmpLocationInTrampoline[0] = 0xE9; // JMP opcode
            memcpy(&jmpLocationInTrampoline[1], &relativeOffset, sizeof(DWORD));

            // 5. Finalize protection (usually PAGE_EXECUTE_READ)
            DWORD oldProtectTrampoline;
            if (!VirtualProtect(trampolineAddress, trampolineTotalSize, PAGE_EXECUTE_READ, &oldProtectTrampoline)) {
                std::cerr << "[TrampolineUtils::AllocateTrampoline] VirtualProtect (trampoline finalize) failed. Error: " << GetLastError() << std::endl;
                VirtualFree(trampolineAddress, 0, MEM_RELEASE); // Clean up allocated memory
                trampolineAddress = nullptr;
                return false;
            }

            FlushInstructionCache(GetCurrentProcess(), trampolineAddress, trampolineTotalSize);
            std::cout << "[TrampolineUtils::AllocateTrampoline] Trampoline allocated at " << trampolineAddress
                      << " for target " << targetFunction << ". Jumps back to " << jumpBackTargetAddress << std::endl;
            return true;
        }

        bool FreeTrampoline(LPVOID trampolineAddress) {
            if (!trampolineAddress) {
                // std::cout << "[TrampolineUtils::FreeTrampoline] No trampoline address provided or already freed." << std::endl;
                return true; // Nothing to free
            }
            if (VirtualFree(trampolineAddress, 0, MEM_RELEASE)) {
                std::cout << "[TrampolineUtils::FreeTrampoline] Trampoline memory at " << trampolineAddress << " freed." << std::endl;
                return true;
            } else {
                std::cerr << "[TrampolineUtils::FreeTrampoline] VirtualFree failed for address " << trampolineAddress
                          << ". Error: " << GetLastError() << std::endl;
                return false;
            }
        }

        bool WriteAbsoluteJump(
            LPVOID sourceAddress,       // Address to write the JMP instruction (target function)
            LPVOID destinationAddress,  // Address the JMP will go to (detour function)
            PBYTE originalBytesBuffer,  // Buffer to store the overwritten bytes (size = jumpInstructionSize)
            SIZE_T jumpInstructionSize) {

            if (!sourceAddress || !destinationAddress || !originalBytesBuffer || jumpInstructionSize < JMP_REL32_SIZE) {
                 std::cerr << "[TrampolineUtils::WriteAbsoluteJump] Invalid arguments." << std::endl;
                return false;
            }

            DWORD oldProtect;
            if (!VirtualProtect(sourceAddress, jumpInstructionSize, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                std::cerr << "[TrampolineUtils::WriteAbsoluteJump] VirtualProtect (Phase 1) failed. Error: " << GetLastError() << std::endl;
                return false;
            }

            // Save original bytes before overwriting
            memcpy(originalBytesBuffer, sourceAddress, jumpInstructionSize);

            // Write JMP instruction (relative jump for x86, 0xE9)
            // Offset = Destination - (Source + 5)
            PBYTE jmpInstructionTarget = static_cast<PBYTE>(sourceAddress);
            DWORD relativeOffset = (DWORD)destinationAddress - ((DWORD)sourceAddress + JMP_REL32_SIZE);

            jmpInstructionTarget[0] = 0xE9; // JMP opcode
            memcpy(&jmpInstructionTarget[1], &relativeOffset, sizeof(DWORD));

            // Fill remaining bytes with NOPs if jumpInstructionSize > JMP_REL32_SIZE (though typically it's exactly 5)
            for (SIZE_T i = JMP_REL32_SIZE; i < jumpInstructionSize; ++i) {
                jmpInstructionTarget[i] = 0x90; // NOP
            }

            if (!VirtualProtect(sourceAddress, jumpInstructionSize, oldProtect, &oldProtect)) {
                std::cerr << "[TrampolineUtils::WriteAbsoluteJump] VirtualProtect (Phase 2) failed. Error: " << GetLastError() << std::endl;
                // Attempt to restore original bytes if VP fails, though this is a bad state
                memcpy(sourceAddress, originalBytesBuffer, jumpInstructionSize);
                return false;
            }

            FlushInstructionCache(GetCurrentProcess(), sourceAddress, jumpInstructionSize);
            std::cout << "[TrampolineUtils::WriteAbsoluteJump] JMP written from " << sourceAddress << " to " << destinationAddress << std::endl;
            return true;
        }

        bool RestoreOriginalBytes(
            LPVOID targetAddress,
            PBYTE bytesBuffer,
            SIZE_T instructionSize) {

            if (!targetAddress || !bytesBuffer || instructionSize == 0) {
                std::cerr << "[TrampolineUtils::RestoreOriginalBytes] Invalid arguments." << std::endl;
                return false;
            }

            DWORD oldProtect;
            if (!VirtualProtect(targetAddress, instructionSize, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                 std::cerr << "[TrampolineUtils::RestoreOriginalBytes] VirtualProtect (Phase 1) failed. Error: " << GetLastError() << std::endl;
                return false;
            }

            memcpy(targetAddress, bytesBuffer, instructionSize);

            if (!VirtualProtect(targetAddress, instructionSize, oldProtect, &oldProtect)) {
                std::cerr << "[TrampolineUtils::RestoreOriginalBytes] VirtualProtect (Phase 2) failed. Error: " << GetLastError() << std::endl;
                return false;
            }

            FlushInstructionCache(GetCurrentProcess(), targetAddress, instructionSize);
            std::cout << "[TrampolineUtils::RestoreOriginalBytes] Bytes restored at " << targetAddress << std::endl;
            return true;
        }

    } // namespace TrampolineUtils
} // namespace UndownUnlock
