#include "../../include/hooks/new_shared_memory_transport.h" // Our new header
#include <iostream>
#include <sstream> // For constructing names
#include <limits>  // For std::numeric_limits

// Define constants from the original .cpp, ensure they are compatible with NewSharedMemoryHeader
namespace UndownUnlock {
namespace DXHook {

// Constants
constexpr uint32_t NEW_SHARED_MEMORY_MAGIC = 0x554E444F; // "UNDO"
constexpr uint32_t NEW_SHARED_MEMORY_VERSION = 1;
constexpr uint32_t NEW_DEFAULT_MAX_FRAMES = 4; // Default if not otherwise specified by size
constexpr uint32_t NEW_HEADER_SIZE = sizeof(NewSharedMemoryHeader);
constexpr uint32_t NEW_SLOT_HEADER_SIZE = sizeof(FrameSlotHeader);


NewSharedMemoryTransport::NewSharedMemoryTransport(const std::string& name, size_t initialSize)
    : m_baseName(name),
      m_sharedMemoryHandle(NULL), // Use NULL for HANDLEs
      m_mappedAddress(nullptr),
      m_header(nullptr),
      m_currentSize(initialSize), // Store initialSize as currentSize
      m_newFrameEvent(NULL),
      m_hNamedMutex(NULL),
      m_isCreator(false) {

    // Construct names for system objects
    m_sharedMemoryName = m_baseName + "_NewSharedMem";
    m_mutexName = m_baseName + "_NewMutex";
    m_eventName = m_baseName + "_NewEvent";

    std::cout << "[NewSharedMemoryTransport] Constructor for base name: " << m_baseName << std::endl;
}

void NewSharedMemoryTransport::Cleanup() {
    if (m_mappedAddress) {
        if (m_header && m_isCreator && m_header->isFullyInitializedByCreator.load(std::memory_order_acquire)) {
            // Optional: Mark as uninitialized if this instance was the creator and is shutting down.
            // This depends on desired behavior if another process tries to connect later.
            // For now, leave it as initialized.
        }
        UnmapViewOfFile(m_mappedAddress);
        m_mappedAddress = nullptr;
        m_header = nullptr;
    }

    if (m_sharedMemoryHandle) {
        CloseHandle(m_sharedMemoryHandle);
        m_sharedMemoryHandle = NULL;
    }

    if (m_newFrameEvent) {
        CloseHandle(m_newFrameEvent);
        m_newFrameEvent = NULL;
    }

    if (m_hNamedMutex) {
        // Release the mutex if this thread/process owns it, though CloseHandle should suffice.
        // ReleaseMutex(m_hNamedMutex); // Be careful if not owned.
        CloseHandle(m_hNamedMutex);
        m_hNamedMutex = NULL;
    }
    std::cout << "[NewSharedMemoryTransport] Cleanup completed for: " << m_baseName << std::endl;
}

NewSharedMemoryTransport::~NewSharedMemoryTransport() {
    std::cout << "[NewSharedMemoryTransport] Destructor for: " << m_baseName << std::endl;
    Shutdown(); // Call explicit Shutdown which calls Cleanup
}

void NewSharedMemoryTransport::Shutdown() {
    std::cout << "[NewSharedMemoryTransport] Shutdown called for: " << m_baseName << std::endl;
    Cleanup();
}

bool NewSharedMemoryTransport::Initialize() {
    std::cout << "[NewSharedMemoryTransport] Initializing for: " << m_baseName << std::endl;

    // 1. Create/Open Named Mutex
    m_hNamedMutex = CreateMutexA(nullptr, FALSE, m_mutexName.c_str());
    if (!m_hNamedMutex) {
        std::cerr << "[NewSharedMemoryTransport] Failed to create/open named mutex '" << m_mutexName << "'. Error: " << GetLastError() << std::endl;
        return false;
    }
    // If GetLastError() == ERROR_ALREADY_EXISTS, we opened an existing mutex.

    // 2. Create/Open Event
    m_newFrameEvent = CreateEventA(nullptr, FALSE, FALSE, m_eventName.c_str()); // Auto-reset, initially non-signaled
    if (!m_newFrameEvent) {
        std::cerr << "[NewSharedMemoryTransport] Failed to create/open event '" << m_eventName << "'. Error: " << GetLastError() << std::endl;
        CloseHandle(m_hNamedMutex); m_hNamedMutex = NULL;
        return false;
    }

    // 3. Create/Open Shared Memory File Mapping
    m_sharedMemoryHandle = OpenFileMappingA(FILE_MAP_ALL_ACCESS, FALSE, m_sharedMemoryName.c_str());

    if (!m_sharedMemoryHandle) { // Doesn't exist, try to create
        m_isCreator = true;
        std::cout << "[NewSharedMemoryTransport] Shared memory '" << m_sharedMemoryName << "' not found. Attempting to create." << std::endl;
        m_sharedMemoryHandle = CreateFileMappingA(
            INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE,
            0, (DWORD)m_currentSize, m_sharedMemoryName.c_str()
        );
        if (!m_sharedMemoryHandle) {
            std::cerr << "[NewSharedMemoryTransport] Failed to create shared memory mapping '" << m_sharedMemoryName << "'. Error: " << GetLastError() << std::endl;
            Cleanup(); // Clean up mutex and event
            return false;
        }
    } else {
        m_isCreator = false;
        std::cout << "[NewSharedMemoryTransport] Opened existing shared memory mapping '" << m_sharedMemoryName << "'." << std::endl;
    }

    // 4. Map View of File
    m_mappedAddress = MapViewOfFile(m_sharedMemoryHandle, FILE_MAP_ALL_ACCESS, 0, 0, m_isCreator ? m_currentSize : 0);
    if (!m_mappedAddress) {
        std::cerr << "[NewSharedMemoryTransport] Failed to map view of shared memory. Error: " << GetLastError() << std::endl;
        Cleanup();
        return false;
    }
    m_header = static_cast<NewSharedMemoryHeader*>(m_mappedAddress);

    // 5. Initialize Header if creator, or validate if opener
    if (m_isCreator) {
        std::cout << "[NewSharedMemoryTransport] Initializing shared memory header as creator." << std::endl;
        m_header->magic = NEW_SHARED_MEMORY_MAGIC;
        m_header->version = NEW_SHARED_MEMORY_VERSION;
        m_header->bufferSize = (uint32_t)m_currentSize;
        m_header->frameDataOffset = NEW_HEADER_SIZE;
        m_header->producerIndex.store(0, std::memory_order_relaxed);
        m_header->consumerIndex.store(0, std::memory_order_relaxed);

        // Calculate maxFrames and frameSize (ensure frameSize calculation is robust)
        if (m_currentSize < NEW_HEADER_SIZE + NEW_SLOT_HEADER_SIZE) { // Ensure there's space for at least header and one slot header
             std::cerr << "[NewSharedMemoryTransport] Initial size too small for header and one frame slot." << std::endl;
             Cleanup();
             return false;
        }
        // Example: Default to 1080p RGBA frame capacity if initial size allows, else calculate based on available space
        uint32_t frameDataCapacity = 1920 * 1080 * 4;
        m_header->frameSize = NEW_SLOT_HEADER_SIZE + frameDataCapacity;

        uint32_t availableBufferForFrames = m_currentSize - NEW_HEADER_SIZE;
        m_header->maxFrames = availableBufferForFrames / m_header->frameSize;
        if (m_header->maxFrames == 0 && availableBufferForFrames >= NEW_SLOT_HEADER_SIZE + 1) { // At least space for header and 1 byte data
            m_header->maxFrames = 1; // Can fit at least one frame, even if small
            m_header->frameSize = availableBufferForFrames; // Use all available space for that one frame
        } else if (m_header->maxFrames == 0) {
            std::cerr << "[NewSharedMemoryTransport] Buffer too small for even one minimal frame slot." << std::endl;
            Cleanup();
            return false;
        }

        m_header->sequence.store(0, std::memory_order_relaxed);
        m_header->isFullyInitializedByCreator.store(true, std::memory_order_release); // Signal initialization complete
        std::cout << "[NewSharedMemoryTransport] Created shared memory. Size: " << m_currentSize
                  << ", Max Frames: " << m_header->maxFrames << ", Frame Slot Size: " << m_header->frameSize << std::endl;

    } else { // Opener: Validate header
        std::cout << "[NewSharedMemoryTransport] Validating existing shared memory header..." << std::endl;
        // Basic spin wait for creator to finish initializing the header.
        // A more robust solution might use another named event.
        int retries = 100; // Wait up to 1 second (100 * 10ms)
        while (!m_header->isFullyInitializedByCreator.load(std::memory_order_acquire) && retries-- > 0) {
            Sleep(10);
        }
        if (!m_header->isFullyInitializedByCreator.load(std::memory_order_relaxed)) {
            std::cerr << "[NewSharedMemoryTransport] Timeout waiting for creator to initialize shared memory header." << std::endl;
            Cleanup();
            return false;
        }

        if (m_header->magic != NEW_SHARED_MEMORY_MAGIC || m_header->version != NEW_SHARED_MEMORY_VERSION) {
            std::cerr << "[NewSharedMemoryTransport] Shared memory magic/version mismatch. "
                      << "Expected Magic: " << NEW_SHARED_MEMORY_MAGIC << " Got: " << m_header->magic
                      << " Expected Version: " << NEW_SHARED_MEMORY_VERSION << " Got: " << m_header->version << std::endl;
            Cleanup();
            return false;
        }
        // Update m_currentSize if we mapped an existing segment of different size
        m_currentSize = m_header->bufferSize;
        std::cout << "[NewSharedMemoryTransport] Successfully connected to existing shared memory. Size: " << m_currentSize
                  << ", Max Frames: " << m_header->maxFrames << ", Frame Slot Size: " << m_header->frameSize << std::endl;
    }

    return true;
}


void* NewSharedMemoryTransport::GetFrameSlotAddress(uint32_t index) {
    if (!m_mappedAddress || !m_header || index >= m_header->maxFrames) {
        return nullptr;
    }
    uint32_t offset = m_header->frameDataOffset + (index * m_header->frameSize);
    if (offset + m_header->frameSize > m_currentSize) { // Check against actual mapped size
        return nullptr;
    }
    return static_cast<BYTE*>(m_mappedAddress) + offset;
}

bool NewSharedMemoryTransport::WriteFrame(const FrameData& frameData, DWORD timeoutMs) {
    if (!IsConnected()) {
        std::cerr << "[NewSharedMemoryTransport::WriteFrame] Not connected." << std::endl;
        return false;
    }

    DWORD waitResult = WaitForSingleObject(m_hNamedMutex, timeoutMs);
    if (waitResult == WAIT_TIMEOUT) {
        std::cerr << "[NewSharedMemoryTransport::WriteFrame] Timeout acquiring mutex." << std::endl;
        return false;
    }
    if (waitResult == WAIT_ABANDONED) {
        std::cerr << "[NewSharedMemoryTransport::WriteFrame] Acquired abandoned mutex. Shared memory might be inconsistent." << std::endl;
        // For now, proceed, but a robust handler might re-initialize or flag error.
    } else if (waitResult != WAIT_OBJECT_0) {
        std::cerr << "[NewSharedMemoryTransport::WriteFrame] Failed to acquire mutex. Error: " << GetLastError() << std::endl;
        return false;
    }

    bool success = false;
    try {
        uint32_t currentProducerIdx = m_header->producerIndex.load(std::memory_order_acquire);
        uint32_t currentConsumerIdx = m_header->consumerIndex.load(std::memory_order_acquire);

        if ((currentProducerIdx + 1) % m_header->maxFrames == currentConsumerIdx) {
            std::cerr << "[NewSharedMemoryTransport::WriteFrame] Buffer is full. Producer: " << currentProducerIdx
                      << ", Consumer: " << currentConsumerIdx << std::endl;
            // Do NOT advance consumerIndex. Return error as per subtask requirement.
            // success = false; // already false
        } else {
            uint32_t slotIndex = currentProducerIdx;
            void* slotAddress = GetFrameSlotAddress(slotIndex);

            if (!slotAddress) {
                std::cerr << "[NewSharedMemoryTransport::WriteFrame] Failed to get frame slot address for index: " << slotIndex << std::endl;
            } else {
                FrameSlotHeader* slotHeader = static_cast<FrameSlotHeader*>(slotAddress);
                uint32_t frameDataBytes = static_cast<uint32_t>(frameData.data.size());

                if (NEW_SLOT_HEADER_SIZE + frameDataBytes > m_header->frameSize) {
                     std::cerr << "[NewSharedMemoryTransport::WriteFrame] Frame data size (" << frameDataBytes
                               << ") exceeds slot capacity (" << (m_header->frameSize - NEW_SLOT_HEADER_SIZE) << ")." << std::endl;
                } else {
                    slotHeader->sequence = m_header->sequence.fetch_add(1, std::memory_order_relaxed) + 1; // fetch_add returns old value
                    slotHeader->width = frameData.width;
                    slotHeader->height = frameData.height;
                    slotHeader->stride = frameData.stride;
                    slotHeader->format = frameData.format; // Assuming DXGI_FORMAT or compatible enum
                    slotHeader->timestamp = frameData.timestamp;
                    slotHeader->dataSize = frameDataBytes;
                    slotHeader->flags = 0; // Reset flags

                    BYTE* dataPtr = static_cast<BYTE*>(slotAddress) + NEW_SLOT_HEADER_SIZE;
                    memcpy(dataPtr, frameData.data.data(), frameDataBytes);

                    m_header->producerIndex.store((slotIndex + 1) % m_header->maxFrames, std::memory_order_release);
                    SetEvent(m_newFrameEvent); // Signal that a new frame is available
                    success = true;
                }
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "[NewSharedMemoryTransport::WriteFrame] Exception: " << e.what() << std::endl;
        success = false;
    } catch (...) {
        std::cerr << "[NewSharedMemoryTransport::WriteFrame] Unknown exception." << std::endl;
        success = false;
    }

    ReleaseMutex(m_hNamedMutex);
    return success;
}

bool NewSharedMemoryTransport::ReadFrame(FrameData& frameData, DWORD timeoutMs) {
    if (!IsConnected()) {
         std::cerr << "[NewSharedMemoryTransport::ReadFrame] Not connected." << std::endl;
        return false;
    }

    DWORD waitResult = WaitForSingleObject(m_hNamedMutex, timeoutMs);
    if (waitResult == WAIT_TIMEOUT) {
        // This is not an error, just means no data if mutex is held by writer for too long
        // std::cout << "[NewSharedMemoryTransport::ReadFrame] Timeout acquiring mutex." << std::endl;
        return false;
    }
    if (waitResult == WAIT_ABANDONED) {
        std::cerr << "[NewSharedMemoryTransport::ReadFrame] Acquired abandoned mutex. Shared memory might be inconsistent." << std::endl;
        // Proceed with caution or re-initialize.
    } else if (waitResult != WAIT_OBJECT_0) {
        std::cerr << "[NewSharedMemoryTransport::ReadFrame] Failed to acquire mutex. Error: " << GetLastError() << std::endl;
        return false;
    }

    bool success = false;
    try {
        uint32_t currentProducerIdx = m_header->producerIndex.load(std::memory_order_acquire);
        uint32_t currentConsumerIdx = m_header->consumerIndex.load(std::memory_order_acquire);

        if (currentProducerIdx == currentConsumerIdx) {
            // Buffer is empty
            // success = false; // already false
        } else {
            uint32_t slotIndex = currentConsumerIdx;
            void* slotAddress = GetFrameSlotAddress(slotIndex);

            if (!slotAddress) {
                std::cerr << "[NewSharedMemoryTransport::ReadFrame] Failed to get frame slot address for index: " << slotIndex << std::endl;
            } else {
                FrameSlotHeader* slotHeader = static_cast<FrameSlotHeader*>(slotAddress);

                // Basic validation, e.g. if dataSize is plausible
                if (slotHeader->dataSize > (m_header->frameSize - NEW_SLOT_HEADER_SIZE)) {
                    std::cerr << "[NewSharedMemoryTransport::ReadFrame] Invalid data size in slot header: " << slotHeader->dataSize << std::endl;
                } else {
                    frameData.width = slotHeader->width;
                    frameData.height = slotHeader->height;
                    frameData.stride = slotHeader->stride;
                    frameData.format = slotHeader->format; // Assuming DXGI_FORMAT or compatible
                    frameData.timestamp = slotHeader->timestamp;
                    frameData.sequence = slotHeader->sequence;

                    frameData.data.resize(slotHeader->dataSize);
                    BYTE* dataPtr = static_cast<BYTE*>(slotAddress) + NEW_SLOT_HEADER_SIZE;
                    memcpy(frameData.data.data(), dataPtr, slotHeader->dataSize);

                    m_header->consumerIndex.store((slotIndex + 1) % m_header->maxFrames, std::memory_order_release);
                    success = true;
                }
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "[NewSharedMemoryTransport::ReadFrame] Exception: " << e.what() << std::endl;
        success = false;
    } catch (...) {
        std::cerr << "[NewSharedMemoryTransport::ReadFrame] Unknown exception." << std::endl;
        success = false;
    }

    ReleaseMutex(m_hNamedMutex);
    return success;
}

bool NewSharedMemoryTransport::WaitForFrame(DWORD timeoutMs) {
    if (!m_newFrameEvent) {
        std::cerr << "[NewSharedMemoryTransport::WaitForFrame] Event handle is null." << std::endl;
        return false;
    }
    DWORD result = WaitForSingleObject(m_newFrameEvent, timeoutMs);
    return result == WAIT_OBJECT_0;
}

} // namespace DXHook
} // namespace UndownUnlock
