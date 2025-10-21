# Usage Examples

This directory contains practical examples demonstrating how to use the UndownUnlock framework for various scenarios.

## Example Categories

### 1. Basic Examples
- **Simple frame capture**
- **Basic hook installation**
- **Process monitoring**
- **Window control**

### 2. Advanced Examples
- **Custom hook development**
- **Performance optimization**
- **Security features**
- **Integration patterns**

### 3. Real-world Scenarios
- **Game frame capture**
- **Application monitoring**
- **Security analysis**
- **Performance profiling**

### 4. Integration Examples
- **Python integration**
- **C++ integration**
- **API usage patterns**
- **Error handling**

## Example Structure

Each example includes:
- **Complete source code**
- **Step-by-step instructions**
- **Configuration files**
- **Expected output**
- **Troubleshooting tips**

## Running Examples

### Prerequisites
1. **Install UndownUnlock** (see main README)
2. **Set up development environment**
3. **Build the project**
4. **Install Python dependencies**

### Basic Usage
```bash
# Navigate to example directory
cd docs/examples/basic_frame_capture

# Run the example
python frame_capture_example.py

# Or run with specific configuration
python frame_capture_example.py --config config.json
```

### Example Categories

#### Basic Examples
- **frame_capture_basic.py** - Simple frame capture
- **hook_installation.py** - Basic hook installation
- **process_monitoring.py** - Process monitoring
- **window_control.py** - Window management

#### Advanced Examples
- **custom_hooks.py** - Custom hook development
- **performance_optimization.py** - Performance tuning
- **security_features.py** - Security implementation
- **memory_management.py** - Memory optimization

#### Integration Examples
- **python_integration.py** - Python API usage
- **cpp_integration.cpp** - C++ API usage
- **api_patterns.py** - Common API patterns
- **error_handling.py** - Error handling examples

## Example Descriptions

### Basic Frame Capture
Demonstrates how to capture frames from a DirectX application using the Windows Graphics Capture API.

**Features:**
- Simple frame capture setup
- Basic configuration
- Frame saving to files
- Error handling

**Use Cases:**
- Screen recording
- Frame analysis
- Performance monitoring
- Debugging

### Custom Hook Development
Shows how to create custom hooks for specific DirectX or Windows API functions.

**Features:**
- Custom hook implementation
- Function interception
- Data modification
- Hook management

**Use Cases:**
- API monitoring
- Data interception
- Behavior modification
- Security analysis

### Performance Optimization
Demonstrates techniques for optimizing frame capture and processing performance.

**Features:**
- Memory pool usage
- Thread pool optimization
- Hardware acceleration
- Performance monitoring

**Use Cases:**
- High-performance capture
- Real-time processing
- Resource optimization
- System monitoring

### Security Features
Shows how to implement anti-detection and security features.

**Features:**
- Anti-detection mechanisms
- Code obfuscation
- Integrity checking
- Secure communication

**Use Cases:**
- Stealth operations
- Security testing
- Penetration testing
- Research purposes

## Configuration Examples

### Basic Configuration
```json
{
    "capture": {
        "method": "windows_graphics_capture",
        "frame_rate": 30,
        "quality": "medium"
    },
    "hooks": {
        "directx": true,
        "windows_api": false
    }
}
```

### Advanced Configuration
```json
{
    "capture": {
        "method": "enhanced_capture",
        "frame_rate": 60,
        "quality": "high",
        "compression": true,
        "hardware_acceleration": true
    },
    "hooks": {
        "directx": {
            "enabled": true,
            "versions": ["11", "12"]
        },
        "windows_api": {
            "enabled": true,
            "functions": ["CreateProcess", "SetForegroundWindow"]
        }
    },
    "security": {
        "anti_detection": true,
        "obfuscation": true
    }
}
```

## Example Output

### Frame Capture Output
```
Starting frame capture...
Target application: target_app.exe
Capture method: Windows Graphics Capture
Frame rate: 30 FPS
Quality: Medium

Captured 150 frames in 5.0 seconds
Average frame time: 33.3ms
Memory usage: 45.2MB
CPU usage: 12.3%

Frame capture completed successfully
```

### Hook Installation Output
```
Installing hooks...
DirectX hooks: ✓ Installed
Windows API hooks: ✓ Installed
Keyboard hooks: ✗ Disabled
Process hooks: ✓ Installed

Hook installation completed
Active hooks: 3
Memory overhead: 2.1MB
Performance impact: <1%
```

## Troubleshooting Examples

### Common Issues
1. **Permission denied**: Run as administrator
2. **Target not found**: Check process name
3. **Hook failure**: Verify target architecture
4. **Performance issues**: Adjust configuration

### Debug Mode
```bash
# Run with debug output
python example.py --debug --log-level verbose

# Enable performance monitoring
python example.py --monitor --output performance.log

# Enable memory tracking
python example.py --memory-tracking --leak-report
```

## Contributing Examples

### Guidelines
1. **Keep examples simple** and focused
2. **Include clear documentation**
3. **Provide working code**
4. **Add error handling**
5. **Include configuration examples**

### Submission Process
1. Create example in appropriate directory
2. Include README with description
3. Add configuration files
4. Test thoroughly
5. Submit pull request

### Example Template
```python
#!/usr/bin/env python3
"""
Example: Basic Frame Capture
Description: Demonstrates simple frame capture functionality
Author: Your Name
Date: 2024-01-01
"""

import sys
import time
from capture.enhanced_capture import EnhancedCapture

def main():
    """Main function demonstrating frame capture."""
    print("Starting basic frame capture example...")
    
    # Initialize capture
    capture = EnhancedCapture()
    
    # Configure capture
    config = {
        'method': 'windows_graphics_capture',
        'frame_rate': 30,
        'quality': 'medium'
    }
    capture.set_configuration(config)
    
    # Start capture
    if not capture.start_capture():
        print("Failed to start capture")
        return 1
    
    print("Capture started successfully")
    
    # Capture frames
    frame_count = 0
    start_time = time.time()
    
    try:
        while frame_count < 100:  # Capture 100 frames
            frame = capture.get_frame()
            if frame:
                print(f"Captured frame {frame_count + 1}")
                frame_count += 1
            time.sleep(1/30)  # 30 FPS
            
    except KeyboardInterrupt:
        print("Capture interrupted by user")
    
    finally:
        capture.stop_capture()
        elapsed = time.time() - start_time
        print(f"Capture completed: {frame_count} frames in {elapsed:.1f}s")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Resources

### Documentation
- [API Reference](../API_REFERENCE.md)
- [Architecture Documentation](../ARCHITECTURE.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [User Guide](../USER_GUIDE.md)

### Community
- **GitHub Issues**: Report example problems
- **GitHub Discussions**: Ask questions about examples
- **Pull Requests**: Submit new examples
- **Wiki**: Community-maintained examples

### Learning Resources
- **Tutorials**: Step-by-step guides
- **Video Guides**: Visual demonstrations
- **Code Samples**: Additional examples
- **Best Practices**: Recommended approaches

## License

Examples are licensed under the same terms as the main project. 