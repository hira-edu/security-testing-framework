cmake_minimum_required(VERSION 3.16)
project(BypassMethodsNative VERSION 1.0.0 LANGUAGES CXX)

if(NOT WIN32)
    message(WARNING "Bypass-methods native build is Windows-only; skipping target generation.")
    return()
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(BYPASS_METHODS_ROOT ${CMAKE_CURRENT_LIST_DIR})
set(BYPASS_METHODS_SRC_DIR ${BYPASS_METHODS_ROOT}/src)
set(BYPASS_METHODS_INCLUDE_DIR ${BYPASS_METHODS_ROOT}/include)

include(${BYPASS_METHODS_ROOT}/cmake/dependencies.cmake)

configure_dependency_options()
validate_build_environment()
validate_dependencies()
setup_dependency_targets()

set(DLL_HOOKS_SOURCES
    ${BYPASS_METHODS_SRC_DIR}/dllmain.cpp
    ${BYPASS_METHODS_SRC_DIR}/com_hooks/factory_hooks.cpp
    ${BYPASS_METHODS_SRC_DIR}/frame/frame_extractor.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/dx_hook_core.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/new_dx_hook_core.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/new_swap_chain_hook.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/swap_chain_hook.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/windows_api/hook_utils.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/windows_api/hooked_functions.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/windows_api/keyboard_hook.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/windows_api/new_hook_system.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/windows_api/trampoline_utils.cpp
    ${BYPASS_METHODS_SRC_DIR}/hooks/windows_api/windows_api_hooks.cpp
    ${BYPASS_METHODS_SRC_DIR}/memory/memory_scanner.cpp
    ${BYPASS_METHODS_SRC_DIR}/memory/pattern_scanner.cpp
    ${BYPASS_METHODS_SRC_DIR}/optimization/memory_pool.cpp
    ${BYPASS_METHODS_SRC_DIR}/optimization/performance_optimizer.cpp
    ${BYPASS_METHODS_SRC_DIR}/optimization/thread_pool.cpp
    ${BYPASS_METHODS_SRC_DIR}/shared/new_shared_memory_transport.cpp
    ${BYPASS_METHODS_SRC_DIR}/shared/shared_memory_transport.cpp
    ${BYPASS_METHODS_SRC_DIR}/signatures/dx_signatures.cpp
    ${BYPASS_METHODS_SRC_DIR}/signatures/lockdown_signatures.cpp
    ${BYPASS_METHODS_SRC_DIR}/signatures/new_lockdown_signatures.cpp
    ${BYPASS_METHODS_SRC_DIR}/utils/crash_reporter.cpp
    ${BYPASS_METHODS_SRC_DIR}/utils/error_handler.cpp
    ${BYPASS_METHODS_SRC_DIR}/utils/memory_tracker.cpp
    ${BYPASS_METHODS_SRC_DIR}/utils/performance_monitor.cpp
    ${BYPASS_METHODS_SRC_DIR}/utils/raii_wrappers.cpp
)

add_library(UndownUnlockDXHook SHARED ${DLL_HOOKS_SOURCES})

set_target_properties(UndownUnlockDXHook PROPERTIES
    OUTPUT_NAME "UndownUnlockDXHook"
)

target_include_directories(UndownUnlockDXHook
    PRIVATE
        ${BYPASS_METHODS_INCLUDE_DIR}
)

target_link_libraries(UndownUnlockDXHook
    PRIVATE
        UndownUnlockDependencies
)

set(STAGING_DIR ${BYPASS_METHODS_ROOT}/dll)

add_custom_command(TARGET UndownUnlockDXHook POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${STAGING_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:UndownUnlockDXHook>
        ${STAGING_DIR}/$<TARGET_FILE_NAME:UndownUnlockDXHook>
    COMMENT "Staging bypass-methods DLL into native/bypass_methods/dll"
)

if(MSVC)
    add_custom_command(TARGET UndownUnlockDXHook POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_PDB_FILE:UndownUnlockDXHook>
            ${STAGING_DIR}/$<TARGET_FILE_BASE_NAME:UndownUnlockDXHook>.pdb
        COMMENT "Staging PDB alongside bypass-methods DLL"
    )
endif()

install(TARGETS UndownUnlockDXHook
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION bin
    ARCHIVE DESTINATION lib
)

set(TEST_CLIENT_SOURCES
    ${BYPASS_METHODS_SRC_DIR}/test_client.cpp
)

add_executable(UndownUnlockTestClient ${TEST_CLIENT_SOURCES})

target_include_directories(UndownUnlockTestClient
    PRIVATE
        ${BYPASS_METHODS_INCLUDE_DIR}
)

target_link_libraries(UndownUnlockTestClient
    PRIVATE
        UndownUnlockDependencies
)

print_dependency_summary()
