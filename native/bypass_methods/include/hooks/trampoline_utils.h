#pragma once

#include <windows.h>
#include <vector> // For potential use in more advanced disassembly, not strictly here

namespace UndownUnlock {
    namespace TrampolineUtils {

        // Simplified: Returns a fixed minimum size or a slightly larger size if very basic relative jumps are detected early.
        // A proper implementation requires a disassembler.
        // For this iteration, it will just return minBytesToCopy ensuring it's at least 5.
        SIZE_T CalculateMinimumPrologueSize(LPCVOID functionAddress, SIZE_T minBytesToCopy = 5);

        // Allocates an executable trampoline.
        // 1. Reads 'prologueSize' bytes from 'targetFunction' into 'copiedPrologueBytes' buffer (caller allocates this buffer).
        // 2. Allocates executable memory for the trampoline.
        // 3. Writes the 'copiedPrologueBytes' to the start of the trampoline.
        // 4. Appends a 64-bit absolute JMP from the trampoline to (targetFunction + prologueSize).
        //    (Note: A 32-bit build would use a 5-byte relative JMP if target is close, or 5-byte abs JMP via register,
        //     but for simplicity and wider address space compatibility, an absolute 64-bit JMP sequence is often used for trampolines.)
        //    For x86 (32-bit), this will be a 5-byte JMP rel32.
        // Sets 'trampolineAddress' to the address of the allocated trampoline.
        bool AllocateTrampoline(
            LPCVOID targetFunction,
            SIZE_T prologueSize,
            PBYTE copiedPrologueBytes, // Buffer to be filled with bytes from targetFunction
            LPVOID& trampolineAddress  // Out: Address of the allocated trampoline
        );

        // Frees memory allocated for a trampoline.
        bool FreeTrampoline(LPVOID trampolineAddress);

        // Writes an absolute JMP from 'sourceAddress' to 'destinationAddress'.
        // 'originalBytesBuffer' stores the bytes overwritten at 'sourceAddress'.
        // 'jumpInstructionSize' is typically 5 for x86 JMP rel32.
        bool WriteAbsoluteJump(
            LPVOID sourceAddress,       // Address to write the JMP instruction
            LPVOID destinationAddress,  // Address the JMP will go to
            PBYTE originalBytesBuffer,  // Buffer to store the overwritten bytes
            SIZE_T jumpInstructionSize  // Size of the JMP instruction (e.g., 5 for x86 JMP rel32)
        );

        // Restores 'instructionSize' bytes from 'bytesBuffer' to 'targetAddress'.
        bool RestoreOriginalBytes(
            LPVOID targetAddress,
            PBYTE bytesBuffer,
            SIZE_T instructionSize
        );

    } // namespace TrampolineUtils
} // namespace UndownUnlock
