#include "../../include/frame_extractor.h"
#include "../../include/shared_memory_transport.h"
#include "../../include/hooks/com_interface_wrapper.h"
#include "../../include/raii_wrappers.h"
#include "../../include/error_handler.h"
#include "../../include/performance_monitor.h"
#include "../../include/memory_tracker.h"
#include <chrono>
#include <iostream>

namespace UndownUnlock {
namespace DXHook {

FrameExtractor::FrameExtractor()
    : m_device(nullptr)
    , m_deviceContext(nullptr)
    , m_currentWidth(0)
    , m_currentHeight(0)
    , m_currentFormat(DXGI_FORMAT_UNKNOWN)
    , m_sharedMemory(nullptr)
    , m_frameSequence(0) {
    
    // Set error context for this frame extractor instance
    ErrorContext context;
    context.set("component", "FrameExtractor");
    context.set("operation", "construction");
    ErrorHandler::GetInstance().set_error_context(context);
    
    ErrorHandler::GetInstance().info(
        "FrameExtractor created",
        ErrorCategory::GRAPHICS,
        __FUNCTION__, __FILE__, __LINE__
    );
}

FrameExtractor::~FrameExtractor() {
    // Start performance monitoring for cleanup
    auto cleanup_operation = PerformanceMonitor::GetInstance().start_operation("frame_extractor_cleanup");
    
    ErrorHandler::GetInstance().info(
        "Cleaning up FrameExtractor",
        ErrorCategory::GRAPHICS,
        __FUNCTION__, __FILE__, __LINE__
    );
    
    try {
        // RAII wrapper automatically releases the staging texture when it goes out of scope
        m_stagingTextureWrapper.Release();
        
        // We don't release the device or context as we don't own them
        
        ErrorHandler::GetInstance().info(
            "FrameExtractor cleanup complete",
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
    } catch (const std::exception& e) {
        ErrorHandler::GetInstance().error(
            "Exception during FrameExtractor cleanup: " + std::string(e.what()),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
    }
    
    // End performance monitoring
    PerformanceMonitor::GetInstance().end_operation(cleanup_operation);
    
    // Clear error context
    ErrorHandler::GetInstance().clear_error_context();
}

bool FrameExtractor::Initialize(ID3D11Device* device, ID3D11DeviceContext* context) {
    // Start performance monitoring for initialization
    auto init_operation = PerformanceMonitor::GetInstance().start_operation("frame_extractor_initialization");
    
    ErrorHandler::GetInstance().info(
        "Initializing FrameExtractor",
        ErrorCategory::GRAPHICS,
        __FUNCTION__, __FILE__, __LINE__
    );
    
    try {
        if (!device || !context) {
            ErrorHandler::GetInstance().error(
                "Invalid device or context",
                ErrorCategory::GRAPHICS,
                __FUNCTION__, __FILE__, __LINE__
            );
            PerformanceMonitor::GetInstance().end_operation(init_operation);
            return false;
        }
        
        m_device = device;
        m_deviceContext = context;
        m_frameSequence = 0;
        
        ErrorHandler::GetInstance().info(
            "Frame extractor initialized successfully",
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring
        PerformanceMonitor::GetInstance().end_operation(init_operation);
        
        return true;
        
    } catch (const std::exception& e) {
        ErrorHandler::GetInstance().error(
            "Exception during FrameExtractor initialization: " + std::string(e.what()),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring on error
        PerformanceMonitor::GetInstance().end_operation(init_operation);
        
        return false;
    }
}

bool FrameExtractor::CreateOrResizeStagingTexture(uint32_t width, uint32_t height, DXGI_FORMAT format) {
    // Start performance monitoring for texture creation
    auto texture_operation = PerformanceMonitor::GetInstance().start_operation("staging_texture_creation");
    
    // Track memory allocation for the texture
    auto& memory_tracker = MemoryTracker::GetInstance();
    
    try {
        // If we already have a staging texture with the right size and format, reuse it
        if (m_stagingTextureWrapper && m_currentWidth == width && m_currentHeight == height && m_currentFormat == format) {
            PerformanceMonitor::GetInstance().end_operation(texture_operation);
            return true;
        }
        
        // Release the old texture if it exists
        m_stagingTextureWrapper.Release();
        
        // Create a new staging texture
        D3D11_TEXTURE2D_DESC desc = {};
        desc.Width = width;
        desc.Height = height;
        desc.MipLevels = 1;
        desc.ArraySize = 1;
        desc.Format = format;
        desc.SampleDesc.Count = 1;
        desc.Usage = D3D11_USAGE_STAGING;
        desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
        
        ID3D11Texture2D* stagingTexture = nullptr;
        HRESULT hr = m_device->CreateTexture2D(&desc, nullptr, &stagingTexture);
        if (FAILED(hr)) {
            ErrorHandler::GetInstance().error(
                "Failed to create staging texture: 0x" + std::to_string(hr),
                ErrorCategory::GRAPHICS,
                __FUNCTION__, __FILE__, __LINE__, hr
            );
            PerformanceMonitor::GetInstance().end_operation(texture_operation);
            return false;
        }
        
        // Track memory allocation
        size_t texture_size = width * height * 4; // Approximate size for RGBA
        auto allocation_id = memory_tracker.TrackAllocation(
            "staging_texture", texture_size, MemoryCategory::GRAPHICS
        );
        
        // Wrap the texture with RAII
        m_stagingTextureWrapper.Reset(stagingTexture, true);
        
        // Store the new dimensions and format
        m_currentWidth = width;
        m_currentHeight = height;
        m_currentFormat = format;
        
        ErrorHandler::GetInstance().info(
            "Created staging texture: " + std::to_string(width) + "x" + std::to_string(height) + 
            ", format: " + std::to_string(format),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring
        PerformanceMonitor::GetInstance().end_operation(texture_operation);
        
        return true;
        
    } catch (const std::exception& e) {
        ErrorHandler::GetInstance().error(
            "Exception during staging texture creation: " + std::string(e.what()),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring on error
        PerformanceMonitor::GetInstance().end_operation(texture_operation);
        
        return false;
    }
}

bool FrameExtractor::ExtractFrame(IDXGISwapChain* pSwapChain) {
    // Start performance monitoring for frame extraction
    auto extract_operation = PerformanceMonitor::GetInstance().start_operation("frame_extraction");
    
    // Set error context for frame extraction
    ErrorContext context;
    context.set("operation", "frame_extraction");
    context.set("component", "FrameExtractor");
    context.set("frame_sequence", std::to_string(m_frameSequence));
    ErrorHandler::GetInstance().set_error_context(context);
    
    if (!pSwapChain || !m_device || !m_deviceContext) {
        ErrorHandler::GetInstance().error(
            "Invalid swap chain, device, or context for frame extraction",
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        PerformanceMonitor::GetInstance().end_operation(extract_operation);
        return false;
    }
    
    try {
        // Get the back buffer from the swap chain
        ID3D11Texture2D* backBuffer = nullptr;
        HRESULT hr = pSwapChain->GetBuffer(0, __uuidof(ID3D11Texture2D), reinterpret_cast<void**>(&backBuffer));
        
        if (FAILED(hr) || !backBuffer) {
            ErrorHandler::GetInstance().error(
                "Failed to get back buffer from swap chain: 0x" + std::to_string(hr),
                ErrorCategory::GRAPHICS,
                __FUNCTION__, __FILE__, __LINE__, hr
            );
            PerformanceMonitor::GetInstance().end_operation(extract_operation);
            return false;
        }
        
        // Get the backbuffer description
        D3D11_TEXTURE2D_DESC backBufferDesc;
        backBuffer->GetDesc(&backBufferDesc);
        
        // Create or resize the staging texture if needed
        if (!CreateOrResizeStagingTexture(backBufferDesc.Width, backBufferDesc.Height, backBufferDesc.Format)) {
            backBuffer->Release();
            PerformanceMonitor::GetInstance().end_operation(extract_operation);
            return false;
        }
        
        // Copy the back buffer to the staging texture
        m_deviceContext->CopyResource(m_stagingTextureWrapper.Get(), backBuffer);
        
        // We're done with the back buffer
        backBuffer->Release();
        
        // Map the staging texture to get access to its data
        D3D11_MAPPED_SUBRESOURCE mappedResource;
        hr = m_deviceContext->Map(m_stagingTextureWrapper.Get(), 0, D3D11_MAP_READ, 0, &mappedResource);
        
        if (FAILED(hr)) {
            ErrorHandler::GetInstance().error(
                "Failed to map staging texture: 0x" + std::to_string(hr),
                ErrorCategory::GRAPHICS,
                __FUNCTION__, __FILE__, __LINE__, hr
            );
            PerformanceMonitor::GetInstance().end_operation(extract_operation);
            return false;
        }
        
        // Create the frame data structure
        FrameData frameData;
        frameData.width = m_currentWidth;
        frameData.height = m_currentHeight;
        frameData.stride = mappedResource.RowPitch;
        frameData.format = m_currentFormat;
        frameData.timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count();
        frameData.sequence = m_frameSequence++;
        
        // Track memory allocation for frame data
        auto& memory_tracker = MemoryTracker::GetInstance();
        size_t totalSize = frameData.height * frameData.stride;
        auto frame_allocation = memory_tracker.TrackAllocation(
            "frame_data", totalSize, MemoryCategory::GRAPHICS
        );
        
        // Copy the data
        const uint8_t* src = static_cast<const uint8_t*>(mappedResource.pData);
        frameData.data.resize(totalSize);
        memcpy(frameData.data.data(), src, totalSize);
        
        // Unmap the texture
        m_deviceContext->Unmap(m_stagingTextureWrapper.Get(), 0);
        
        ErrorHandler::GetInstance().debug(
            "Frame data extracted: " + std::to_string(frameData.width) + "x" + std::to_string(frameData.height) + 
            ", size: " + std::to_string(totalSize) + " bytes",
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // Convert the frame format if needed
        FrameData convertedData;
        bool needsConversion = ConvertFrameFormat(frameData, convertedData);
        
        // Use the callback if set
        if (m_frameCallback) {
            m_frameCallback(needsConversion ? convertedData : frameData);
        }
        
        // Write to shared memory if available
        if (m_sharedMemory) {
            m_sharedMemory->WriteFrame(needsConversion ? convertedData : frameData);
        }
        
        ErrorHandler::GetInstance().info(
            "Frame extraction completed successfully, sequence: " + std::to_string(frameData.sequence),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring
        PerformanceMonitor::GetInstance().end_operation(extract_operation);
        
        // Clear error context
        ErrorHandler::GetInstance().clear_error_context();
        
        return true;
    }
    catch (const std::exception& e) {
        ErrorHandler::GetInstance().error(
            "Exception in ExtractFrame: " + std::string(e.what()),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring on error
        PerformanceMonitor::GetInstance().end_operation(extract_operation);
        
        // Clear error context
        ErrorHandler::GetInstance().clear_error_context();
        
        return false;
    }
}

bool FrameExtractor::ConvertFrameFormat(const FrameData& sourceData, FrameData& convertedData) {
    // Start performance monitoring for format conversion
    auto conversion_operation = PerformanceMonitor::GetInstance().start_operation("frame_format_conversion");
    
    try {
        // Currently, we only support direct pass-through
        // Future implementations will add format conversion for non-standard formats
        
        // For now, we'll just check if the format is one we can easily handle
        switch (sourceData.format) {
            case DXGI_FORMAT_R8G8B8A8_UNORM:
            case DXGI_FORMAT_B8G8R8A8_UNORM:
            case DXGI_FORMAT_R8G8B8A8_TYPELESS:
            case DXGI_FORMAT_B8G8R8A8_TYPELESS:
            case DXGI_FORMAT_R8G8B8A8_UNORM_SRGB:
            case DXGI_FORMAT_B8G8R8A8_UNORM_SRGB:
                // These formats are already compatible, no conversion needed
                PerformanceMonitor::GetInstance().end_operation(conversion_operation);
                return false;
            
            default:
                // For unsupported formats, we'd implement conversion here
                // For now, just return false to indicate no conversion was done
                ErrorHandler::GetInstance().warning(
                    "Unsupported frame format: " + std::to_string(sourceData.format),
                    ErrorCategory::GRAPHICS,
                    __FUNCTION__, __FILE__, __LINE__
                );
                PerformanceMonitor::GetInstance().end_operation(conversion_operation);
                return false;
        }
        
    } catch (const std::exception& e) {
        ErrorHandler::GetInstance().error(
            "Exception during frame format conversion: " + std::string(e.what()),
            ErrorCategory::GRAPHICS,
            __FUNCTION__, __FILE__, __LINE__
        );
        
        // End performance monitoring on error
        PerformanceMonitor::GetInstance().end_operation(conversion_operation);
        
        return false;
    }
}

void FrameExtractor::SetFrameCallback(std::function<void(const FrameData&)> callback) {
    m_frameCallback = callback;
    
    ErrorHandler::GetInstance().debug(
        "Frame callback set",
        ErrorCategory::GRAPHICS,
        __FUNCTION__, __FILE__, __LINE__
    );
}

void FrameExtractor::SetSharedMemoryTransport(SharedMemoryTransport* sharedMemory) {
    m_sharedMemory = sharedMemory;
    
    ErrorHandler::GetInstance().debug(
        "Shared memory transport set",
        ErrorCategory::GRAPHICS,
        __FUNCTION__, __FILE__, __LINE__
    );
}

} // namespace DXHook
} // namespace UndownUnlock 



