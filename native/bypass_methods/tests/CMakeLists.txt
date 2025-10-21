cmake_minimum_required(VERSION 3.12)
project(UndownUnlockTests VERSION 1.0.0 LANGUAGES CXX)

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/include
)

# Use Google Test framework (managed by parent CMakeLists.txt)
if(NOT TARGET gtest)
    message(FATAL_ERROR "Google Test not available. Please ensure BUILD_TESTING is enabled.")
endif()

# Define test source files
set(TEST_SOURCES
    test_pattern_scanner.cpp
    test_hooked_functions.cpp
    test_com_interface_wrapper.cpp
    test_raii_wrappers.cpp
    test_error_handler.cpp
    test_dx_hook_core.cpp
    test_shared_memory_transport.cpp
    test_frame_extractor.cpp
    test_new_dx_hook_core.cpp
    test_swap_chain_hook.cpp
    test_windows_api_hooks.cpp
    # Priority 2 test files
    test_keyboard_hook.cpp
    test_dx_signatures.cpp
    test_lockdown_signatures.cpp
    # Performance optimization tests
    performance/test_optimizations.cpp
)

# Create test executable
add_executable(undownunlock_tests ${TEST_SOURCES})

# Link against test dependencies and our library
target_link_libraries(undownunlock_tests PRIVATE
    UndownUnlockTestDependencies
    UndownUnlockDXHook
)

# Register tests with CTest
add_test(NAME undownunlock_tests COMMAND undownunlock_tests)

# Set working directory for tests
set_tests_properties(undownunlock_tests PROPERTIES
    WORKING_DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}
) 
