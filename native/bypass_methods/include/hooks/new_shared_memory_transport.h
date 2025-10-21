#pragma once

#include <Windows.h>
#include <string>
#include <vector>
#include <atomic>
#include <stdexcept> // For std::runtime_error

// Define a basic FrameData struct if not available from elsewhere
// This is often project-specific.
namespace UndownUnlock {
namespace DXHook { // Using the same namespace, but will use a new class name

struct FrameData {
    std::vector<BYTE> data;
    uint32_t width = 0;
    uint32_t height = 0;
    uint32_t stride = 0;
    UINT format = 0; // Or specific DXGI_FORMAT if used
    uint64_t timestamp = 0;
    uint32_t sequence = 0;
    // Add other necessary fields as per project's needs
};

/**
 * @brief Shared memory frame buffer header (Modified for NewSharedMemoryTransport)
 */
struct NewSharedMemoryHeader { // Renamed to avoid ODR issues if old is still compiled
    uint32_t magic;
    uint32_t version;
    uint32_t bufferSize;
    uint32_t frameDataOffset;
    std::atomic<uint32_t> producerIndex;
    std::atomic<uint32_t> consumerIndex;
    uint32_t maxFrames;
    uint32_t frameSize; // Size of each slot (FrameSlotHeader + data capacity)
    std::atomic<uint32_t> sequence;
    // SRWLOCK srwLock; // Removed
    std::atomic<bool> isFullyInitializedByCreator; // Flag to ensure creator finishes init
};

/**
 * @brief Frame slot header in shared memory (Can remain the same name if structure is identical)
 */
struct FrameSlotHeader {
    uint32_t sequence;
    uint32_t width;
    uint32_t height;
    uint32_t stride;
    uint32_t format;
    uint64_t timestamp;
    uint32_t dataSize; // Actual size of pixel data in this slot
    uint32_t flags;
};

/**
 * @brief New class for transporting frame data via shared memory using Named Mutex
 */
class NewSharedMemoryTransport {
public:
    NewSharedMemoryTransport(const std::string& name, size_t initialSize = 64 * 1024 * 1024);
    ~NewSharedMemoryTransport();

    bool Initialize();
    void Shutdown(); // Explicit shutdown method

    // Default timeout for mutex acquisition (e.g., 100ms)
    static const DWORD DEFAULT_MUTEX_TIMEOUT = 100;

    bool WriteFrame(const FrameData& frameData, DWORD timeoutMs = DEFAULT_MUTEX_TIMEOUT);
    bool ReadFrame(FrameData& frameData, DWORD timeoutMs = DEFAULT_MUTEX_TIMEOUT);

    bool WaitForFrame(DWORD timeoutMs = 1000); // For new frame event

    bool IsConnected() const { return m_mappedAddress != nullptr && m_header != nullptr && m_hNamedMutex != NULL; }
    bool IsCreator() const { return m_isCreator; }

private:
    std::string m_baseName;            // Base name for shared memory objects
    HANDLE m_sharedMemoryHandle;
    void* m_mappedAddress;
    NewSharedMemoryHeader* m_header;   // Using the new header type
    size_t m_currentSize;              // Current size of the shared memory buffer (can change if resize is implemented)

    HANDLE m_newFrameEvent;
    HANDLE m_hNamedMutex;              // Named mutex for synchronization

    std::string m_sharedMemoryName;
    std::string m_mutexName;
    std::string m_eventName;

    bool m_isCreator;                  // True if this instance created the shared memory

    void* GetFrameSlotAddress(uint32_t index);
    void Cleanup(); // Helper for destructor and Shutdown
};

} // namespace DXHook
} // namespace UndownUnlock
