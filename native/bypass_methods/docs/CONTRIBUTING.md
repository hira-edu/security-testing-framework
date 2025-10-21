# Contributing to UndownUnlock

Thank you for your interest in contributing to the UndownUnlock project! This document provides guidelines and information for contributors to help ensure a smooth and productive development process.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Environment Setup](#development-environment-setup)
3. [Coding Standards](#coding-standards)
4. [Testing Guidelines](#testing-guidelines)
5. [Pull Request Process](#pull-request-process)
6. [Issue Reporting](#issue-reporting)
7. [Code Review Guidelines](#code-review-guidelines)
8. [Release Process](#release-process)
9. [Security Guidelines](#security-guidelines)
10. [Documentation Guidelines](#documentation-guidelines)

## Getting Started

### Prerequisites
- Windows 10/11 (64-bit)
- Visual Studio 2019/2022 with C++ development tools
- Python 3.8+ with pip
- CMake 3.16+
- Git

### Quick Start
1. Fork the repository
2. Clone your fork locally
3. Set up the development environment (see below)
4. Create a feature branch
5. Make your changes
6. Run tests
7. Submit a pull request

## Development Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/bypass-methods.git
cd bypass-methods
```

### 2. Set Up C++ Development Environment
```bash
# Create build directory
mkdir build
cd build

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Debug

# Build the project
cmake --build . --config Debug

# Run tests
ctest --output-on-failure
```

### 3. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r python/requirements/requirements.txt
pip install -r python/requirements/requirements_accessibility.txt
```

### 4. IDE Configuration

#### Visual Studio
- Open the `CMakeLists.txt` file in Visual Studio
- Configure the project for your preferred build type
- Set up IntelliSense by configuring include paths

#### VS Code
- Install C/C++ extension
- Install CMake Tools extension
- Configure `c_cpp_properties.json` for proper IntelliSense

### 5. Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## Coding Standards

### C++ Coding Standards

#### General Principles
- Follow the [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- Use modern C++ features (C++17/20) when appropriate
- Prioritize readability and maintainability
- Write self-documenting code with clear variable and function names

#### Naming Conventions
```cpp
// Classes: PascalCase
class FrameExtractor { };

// Functions: camelCase
void extractFrameData() { }

// Variables: camelCase
int frameCount = 0;

// Constants: UPPER_SNAKE_CASE
const int MAX_FRAME_SIZE = 1920 * 1080;

// Member variables: trailing underscore
class MyClass {
private:
    int memberVariable_;
};
```

#### File Organization
```cpp
// Header file structure
#pragma once

// System includes
#include <windows.h>
#include <d3d11.h>

// Third-party includes
#include <gtest/gtest.h>

// Project includes
#include "utils/error_handler.h"

// Forward declarations
class FrameExtractor;

// Class definition
class MyClass {
public:
    // Public interface
private:
    // Private implementation
};
```

#### Error Handling
```cpp
// Use RAII and smart pointers
std::unique_ptr<FrameExtractor> extractor = std::make_unique<FrameExtractor>();

// Use exceptions for exceptional cases
if (!extractor->Initialize(device)) {
    throw std::runtime_error("Failed to initialize frame extractor");
}

// Use error codes for expected failures
ErrorCode result = ProcessFrame(frameData);
if (result != ErrorCode::SUCCESS) {
    // Handle expected error
    return result;
}
```

#### Memory Management
```cpp
// Use smart pointers instead of raw pointers
std::unique_ptr<ID3D11Texture2D> texture;
std::shared_ptr<FrameData> frameData;

// Use RAII wrappers for Windows handles
ScopedHandle fileHandle(CreateFile(...));

// Use COM interface wrappers
ComPtr<ID3D11Device> device;
```

### Python Coding Standards

#### General Principles
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

#### Code Style
```python
# Use snake_case for variables and functions
def extract_frame_data(frame_buffer):
    """Extract frame data from buffer.
    
    Args:
        frame_buffer: Raw frame buffer data
        
    Returns:
        Processed frame data or None if extraction failed
    """
    pass

# Use PascalCase for classes
class FrameProcessor:
    """Processes captured frames."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize frame processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
```

#### Error Handling
```python
# Use exceptions for exceptional cases
try:
    frame_data = extractor.extract_frame()
except ExtractionError as e:
    logger.error(f"Frame extraction failed: {e}")
    return None

# Use return values for expected failures
result = process_frame(frame_data)
if result.is_error():
    logger.warning(f"Frame processing failed: {result.error_message}")
    return result
```

## Testing Guidelines

### C++ Testing

#### Unit Tests
- Write unit tests for all public functions
- Use Google Test framework
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

```cpp
// Example unit test
TEST_F(FrameExtractorTest, ExtractFrame_ValidTexture_ReturnsSuccess) {
    // Arrange
    auto mockDevice = std::make_unique<MockD3D11Device>();
    auto mockTexture = std::make_unique<MockTexture2D>();
    FrameExtractor extractor;
    extractor.Initialize(mockDevice.get());
    
    // Act
    FrameData frameData;
    bool result = extractor.ExtractFrame(mockTexture.get(), frameData);
    
    // Assert
    EXPECT_TRUE(result);
    EXPECT_EQ(frameData.width, 1920);
    EXPECT_EQ(frameData.height, 1080);
}
```

#### Integration Tests
- Test component interactions
- Test end-to-end workflows
- Use real DirectX resources when possible

#### Performance Tests
- Benchmark critical paths
- Test memory usage patterns
- Validate performance requirements

### Python Testing

#### Unit Tests
```python
import unittest
from unittest.mock import Mock, patch

class TestFrameProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = FrameProcessor({})
        
    def test_process_frame_valid_data(self):
        # Arrange
        frame_data = create_test_frame_data()
        
        # Act
        result = self.processor.process_frame(frame_data)
        
        # Assert
        self.assertTrue(result.is_success())
        self.assertEqual(result.frame.width, 1920)
```

#### Integration Tests
```python
class TestCaptureIntegration(unittest.TestCase):
    def test_full_capture_workflow(self):
        # Test complete capture workflow
        capture = EnhancedCapture()
        capture.add_capture_method(WindowsGraphicsCapture())
        
        self.assertTrue(capture.start_capture())
        frame = capture.get_frame()
        self.assertIsNotNone(frame)
        capture.stop_capture()
```

### Test Coverage Requirements
- Minimum 80% code coverage for new code
- 100% coverage for critical paths
- All public APIs must have tests
- Performance tests for optimization changes

## Pull Request Process

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Write clear, focused commits
- Follow coding standards
- Add appropriate tests
- Update documentation

### 3. Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

**Examples:**
```
feat(capture): add Windows Graphics Capture support

Add support for Windows Graphics Capture API as primary capture method.
Includes fallback to DXGI Desktop Duplication.

Closes #123
```

### 4. Run Pre-commit Checks
```bash
# Run tests
ctest --output-on-failure

# Run Python tests
python -m pytest python/tests/

# Run static analysis
clang-tidy src/*.cpp

# Check code formatting
clang-format --dry-run src/*.cpp
```

### 5. Submit Pull Request
- Use the provided pull request template
- Include clear description of changes
- Reference related issues
- Add screenshots for UI changes
- Include performance impact analysis if applicable

### 6. Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Performance tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Performance impact assessed

## Related Issues
Closes #123
```

## Issue Reporting

### Bug Reports
When reporting bugs, please include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, version, etc.)
- Error messages and logs
- Screenshots if applicable

### Feature Requests
When requesting features, please include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation approach
- Impact on existing functionality

### Issue Template
```markdown
## Description
[Clear description of the issue]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- OS: [Windows version]
- UndownUnlock version: [version]
- Python version: [version]
- Visual Studio version: [version]

## Additional Information
[Any other relevant information]
```

## Code Review Guidelines

### Review Process
1. **Automated Checks**: All automated checks must pass
2. **Code Review**: At least one approval required
3. **Testing**: All tests must pass
4. **Documentation**: Documentation must be updated
5. **Performance**: Performance impact must be assessed

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are comprehensive and pass
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact is acceptable
- [ ] Error handling is appropriate
- [ ] Memory management is correct
- [ ] API design is consistent

### Review Comments
- Be constructive and specific
- Suggest improvements when possible
- Focus on code quality and maintainability
- Consider security implications
- Check for potential performance issues

## Release Process

### Version Numbering
Follow [Semantic Versioning](https://semver.org/):
- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

### Release Checklist
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Changelog is updated
- [ ] Version numbers are updated
- [ ] Release notes are written
- [ ] Binaries are built and tested
- [ ] Release is tagged in Git

### Release Steps
1. Update version numbers in all files
2. Update changelog
3. Create release branch
4. Run full test suite
5. Build release binaries
6. Create Git tag
7. Publish release notes
8. Deploy to distribution channels

## Security Guidelines

### Code Security
- Never commit sensitive information (API keys, passwords)
- Use secure coding practices
- Validate all inputs
- Handle errors securely
- Use appropriate access controls

### Security Review
- All security-related changes require security review
- Follow secure coding guidelines
- Test for common vulnerabilities
- Document security considerations

### Vulnerability Reporting
- Report security vulnerabilities privately
- Use secure communication channels
- Provide detailed reproduction steps
- Allow time for fix development

## Documentation Guidelines

### Code Documentation
- Document all public APIs
- Use clear, concise comments
- Include usage examples
- Document error conditions
- Keep documentation up to date

### Architecture Documentation
- Document system architecture
- Include component diagrams
- Describe data flow patterns
- Document design decisions
- Keep diagrams current

### User Documentation
- Write clear, step-by-step instructions
- Include troubleshooting guides
- Provide configuration examples
- Keep documentation user-friendly
- Include screenshots when helpful

## Getting Help

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code contributions and reviews

### Resources
- [Architecture Documentation](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Build System Guide](BUILD_SYSTEM_GUIDE.md)

### Code of Conduct
- Be respectful and inclusive
- Focus on technical discussions
- Help others learn and contribute
- Follow project guidelines
- Report inappropriate behavior

## Conclusion

Thank you for contributing to the UndownUnlock project! Your contributions help make this project better for everyone. If you have any questions or need clarification on any of these guidelines, please don't hesitate to ask.

Remember:
- Quality over quantity
- Test thoroughly
- Document your changes
- Follow the established patterns
- Be patient with the review process

Happy coding! 