# muse-v2 top-level build
# -----------------------------------------------------------------------------
# DDD-structured C++ project. Three layers (domain → application → infrastructure)
# plus apps/ for the composition root. Tests at every layer. Tested with
# Visual Studio 2022 Professional (toolset v143) on Windows x64.
#
# Build:
#   cmake -S . -B build -G "Visual Studio 17 2022" -A x64
#   cmake --build build --config Release
#
# Run all tests (after build):
#   ctest --test-dir build --build-config Release --output-on-failure
#
# Or run a specific test exe directly:
#   .\build\tests\Release\domain_tests.exe
# -----------------------------------------------------------------------------

cmake_minimum_required(VERSION 3.20)
project(muse-v2 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Treat warnings as useful signal, not noise.
if(MSVC)
    add_compile_options(/W4 /permissive-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

enable_testing()

# -----------------------------------------------------------------------------
# third_party — header-only test framework (doctest)
# -----------------------------------------------------------------------------
add_library(doctest INTERFACE)
target_include_directories(doctest INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/third_party)

# -----------------------------------------------------------------------------
# Include paths
# -----------------------------------------------------------------------------
# All layers share the top-level include/ so headers can be included as
# "domain/Foo.hpp", "application/Bar.hpp", "infrastructure/libmuse/Baz.hpp".
# This keeps the dependency direction visible at every #include site.
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# -----------------------------------------------------------------------------
# Domain layer
# -----------------------------------------------------------------------------
# Pure types. Header-only for now — no .cpp files yet because every domain
# type is small enough to be defined inline. When one grows, split it out
# into src/domain/ and add it to this target.
add_library(musev2_domain INTERFACE)
target_include_directories(musev2_domain INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# -----------------------------------------------------------------------------
# Application layer
# -----------------------------------------------------------------------------
# Depends only on domain. No libmuse, no liblsl.
# add_library(musev2_application ...) — added when we have source files
# For now the application layer is all pure interfaces (abstract ports)
# which don't need a compiled library.

# -----------------------------------------------------------------------------
# Infrastructure layer (disabled until liblsl + libmuse are wired)
# -----------------------------------------------------------------------------
# add_library(musev2_infrastructure_libmuse ...)
# add_library(musev2_infrastructure_liblsl  ...)
# (linked against libmuse-wrt.lib and liblsl.dll respectively)

# -----------------------------------------------------------------------------
# Application entry point (disabled until infrastructure is wired)
# -----------------------------------------------------------------------------
# add_executable(muse_sdk_bridge apps/muse_sdk_bridge/main.cpp)
# target_link_libraries(muse_sdk_bridge
#     PRIVATE musev2_application musev2_infrastructure_libmuse musev2_infrastructure_liblsl
# )

# -----------------------------------------------------------------------------
# Tests — domain
# -----------------------------------------------------------------------------
# Each test .cpp is a self-contained doctest executable with its own main().
# This keeps test compile times fast and test failures scoped to one file.
add_executable(domain_tests_packet_type
    tests/domain/PacketType_test.cpp
)
target_link_libraries(domain_tests_packet_type PRIVATE musev2_domain doctest)
add_test(NAME domain_PacketType COMMAND domain_tests_packet_type)

add_executable(domain_tests_channel_layout
    tests/domain/ChannelLayout_test.cpp
)
target_link_libraries(domain_tests_channel_layout PRIVATE musev2_domain doctest)
add_test(NAME domain_ChannelLayout COMMAND domain_tests_channel_layout)

add_executable(domain_tests_sample_packet
    tests/domain/SamplePacket_test.cpp
)
target_link_libraries(domain_tests_sample_packet PRIVATE musev2_domain doctest)
add_test(NAME domain_SamplePacket COMMAND domain_tests_sample_packet)

add_executable(domain_tests_device_identity
    tests/domain/DeviceIdentity_test.cpp
)
target_link_libraries(domain_tests_device_identity PRIVATE musev2_domain doctest)
add_test(NAME domain_DeviceIdentity COMMAND domain_tests_device_identity)

add_executable(domain_tests_session_state
    tests/domain/SessionState_test.cpp
)
target_link_libraries(domain_tests_session_state PRIVATE musev2_domain doctest)
add_test(NAME domain_SessionState COMMAND domain_tests_session_state)

# -----------------------------------------------------------------------------
# Tests — application
# -----------------------------------------------------------------------------
# Application layer depends on domain types plus its own abstract port
# interfaces. No libmuse, no liblsl — tests use mock port implementations
# defined in the test files themselves.

add_executable(application_tests_ports_compile
    tests/application/ports_compile_test.cpp
)
target_link_libraries(application_tests_ports_compile PRIVATE musev2_domain doctest)
add_test(NAME application_PortsCompile COMMAND application_tests_ports_compile)

# -----------------------------------------------------------------------------
# Tests — application (added when we have mock ports + StreamingSession)
# -----------------------------------------------------------------------------
# add_executable(application_tests tests/application/*.cpp ...)
# target_link_libraries(application_tests PRIVATE musev2_domain doctest)
# add_test(NAME application_tests COMMAND application_tests)

# -----------------------------------------------------------------------------
# Tests — infrastructure (may require hardware; added later)
# -----------------------------------------------------------------------------
# add_executable(infrastructure_tests tests/infrastructure/*.cpp ...)
# target_link_libraries(infrastructure_tests
#     PRIVATE musev2_infrastructure_libmuse musev2_infrastructure_liblsl doctest
# )
# add_test(NAME infrastructure_tests COMMAND infrastructure_tests --require-hardware)

# -----------------------------------------------------------------------------
# Summary output
# -----------------------------------------------------------------------------
message(STATUS "muse-v2 configuration:")
message(STATUS "  C++ standard:     ${CMAKE_CXX_STANDARD}")
message(STATUS "  Source dir:       ${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "  Include path:     ${CMAKE_CURRENT_SOURCE_DIR}/include")
message(STATUS "  doctest location: ${CMAKE_CURRENT_SOURCE_DIR}/third_party/doctest/doctest.h")
message(STATUS "  Build type:       ${CMAKE_BUILD_TYPE}")
