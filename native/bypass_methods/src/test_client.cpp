#include <Windows.h>
#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <memory>
#include "../include/frame_extractor.h"
#include "../include/shared_memory_transport.h"

// Define the bitmap file header structure
#pragma pack(push, 1)
struct BitmapFileHeader {
    uint16_t bfType;
    uint32_t bfSize;
    uint16_t bfReserved1;
    uint16_t bfReserved2;
    uint32_t bfOffBits;
};

// Define the bitmap info header structure
struct BitmapInfoHeader {
    uint32_t biSize;
    int32_t  biWidth;
    int32_t  biHeight;
    uint16_t biPlanes;
    uint16_t biBitCount;
    uint32_t biCompression;
    uint32_t biSizeImage;
    int32_t  biXPelsPerMeter;
    int32_t  biYPelsPerMeter;
    uint32_t biClrUsed;
    uint32_t biClrImportant;
};
#pragma pack(pop)

// Function to save a frame as a bitmap file
bool SaveFrameAsBitmap(const UndownUnlock::DXHook::FrameData& frameData, const std::string& filename) {
    // Open the file for writing
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Failed to open file for writing: " << filename << std::endl;
        return false;
    }
    
    // Calculate some values for the headers
    uint32_t imageSize = frameData.height * frameData.stride;
    uint32_t fileSize = sizeof(BitmapFileHeader) + sizeof(BitmapInfoHeader) + imageSize;
    
    // Create the bitmap file header
    BitmapFileHeader fileHeader = {};
    fileHeader.bfType = 0x4D42;  // "BM"
    fileHeader.bfSize = fileSize;
    fileHeader.bfReserved1 = 0;
    fileHeader.bfReserved2 = 0;
    fileHeader.bfOffBits = sizeof(BitmapFileHeader) + sizeof(BitmapInfoHeader);
    
    // Create the bitmap info header
    BitmapInfoHeader infoHeader = {};
    infoHeader.biSize = sizeof(BitmapInfoHeader);
    infoHeader.biWidth = frameData.width;
    infoHeader.biHeight = -static_cast<int32_t>(frameData.height);  // Negative height means top-down
    infoHeader.biPlanes = 1;
    infoHeader.biBitCount = 32;  // BGRA
    infoHeader.biCompression = 0;  // BI_RGB
    infoHeader.biSizeImage = imageSize;
    infoHeader.biXPelsPerMeter = 0;
    infoHeader.biYPelsPerMeter = 0;
    infoHeader.biClrUsed = 0;
    infoHeader.biClrImportant = 0;
    
    // Write the headers to the file
    file.write(reinterpret_cast<const char*>(&fileHeader), sizeof(fileHeader));
    file.write(reinterpret_cast<const char*>(&infoHeader), sizeof(infoHeader));
    
    // Write the image data to the file
    file.write(reinterpret_cast<const char*>(frameData.data.data()), frameData.data.size());
    
    return true;
}

int main(int argc, char* argv[]) {
    std::cout << "UndownUnlock DirectX Hook Client" << std::endl;
    std::cout << "===============================" << std::endl;
    
    // Create the output directory if it doesn't exist
    CreateDirectoryA("captured_frames", nullptr);
    
    // Connect to shared memory
    std::unique_ptr<UndownUnlock::DXHook::SharedMemoryTransport> sharedMemory =
        std::make_unique<UndownUnlock::DXHook::SharedMemoryTransport>("UndownUnlockFrameData");
    
    if (!sharedMemory->Initialize()) {
        std::cerr << "Failed to initialize shared memory. Is the DLL injected?" << std::endl;
        return 1;
    }
    
    std::cout << "Connected to shared memory" << std::endl;
    std::cout << "Waiting for frames... Press Ctrl+C to exit" << std::endl;
    
    // Main loop - read frames from shared memory and save them as images
    int frameCount = 0;
    try {
        while (true) {
            // Wait for a new frame
            if (sharedMemory->WaitForFrame(1000)) {
                // Read the frame
                UndownUnlock::DXHook::FrameData frameData;
                if (sharedMemory->ReadFrame(frameData)) {
                    // Generate a filename
                    std::string filename = "captured_frames/frame_" + std::to_string(frameCount++) + ".bmp";
                    
                    // Save the frame as a bitmap
                    if (SaveFrameAsBitmap(frameData, filename)) {
                        std::cout << "Saved frame to " << filename 
                                 << " (" << frameData.width << "x" << frameData.height << ")" << std::endl;
                    }
                    else {
                        std::cerr << "Failed to save frame" << std::endl;
                    }
                }
                else {
                    std::cerr << "Failed to read frame from shared memory" << std::endl;
                }
            }
        }
    }
    catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
    }
    
    return 0;
} 