cmake_minimum_required(VERSION 3.20)

if(POLICY CMP0135)
    cmake_policy(SET CMP0135 NEW)
endif()
if(POLICY CMP0169)
    cmake_policy(SET CMP0169 OLD)
endif()

project(StorageVisualizer_Native CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

# 1. Fetch nlohmann/json single header with proper directory layout
FetchContent_Declare(
    json_repo
    URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp
    DOWNLOAD_NO_EXTRACT TRUE
)
FetchContent_MakeAvailable(json_repo)

set(JSON_INCLUDE_DIR "${json_repo_SOURCE_DIR}/include")
file(MAKE_DIRECTORY "${JSON_INCLUDE_DIR}/nlohmann")
file(COPY "${json_repo_SOURCE_DIR}/json.hpp" DESTINATION "${JSON_INCLUDE_DIR}/nlohmann")

# 2. Fetch Microsoft WIL (Headers only)
FetchContent_Declare(
    wil
    URL https://github.com/microsoft/wil/archive/refs/tags/v1.0.240803.1.zip
)
FetchContent_GetProperties(wil)
if(NOT wil_POPULATED)
    FetchContent_Populate(wil)
endif()

# 3. Fetch Microsoft WebView2 Native SDK
FetchContent_Declare(
    webview2_sdk
    URL https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/1.0.2903.40
)
FetchContent_GetProperties(webview2_sdk)
if(NOT webview2_sdk_POPULATED)
    FetchContent_Populate(webview2_sdk)
endif()

if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set(WEBVIEW2_ARCH x64)
else()
    set(WEBVIEW2_ARCH x86)
endif()

# Main Application Executable
add_executable(StorageVisualizer WIN32
    src/main.cpp
)

# Include Directories
target_include_directories(StorageVisualizer PRIVATE
    ${JSON_INCLUDE_DIR}
    ${wil_SOURCE_DIR}/include
    ${webview2_sdk_SOURCE_DIR}/build/native/include
)

# Link WebView2 Loader Library
target_link_libraries(StorageVisualizer PRIVATE
    ${webview2_sdk_SOURCE_DIR}/build/native/${WEBVIEW2_ARCH}/WebView2Loader.dll.lib
)

# Copy WebView2Loader.dll into target executable output folder after build
add_custom_command(TARGET StorageVisualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    "${webview2_sdk_SOURCE_DIR}/build/native/${WEBVIEW2_ARCH}/WebView2Loader.dll"
    "$<TARGET_FILE_DIR:StorageVisualizer>"
)

# Copy 'web' folder (index.html, JS, CSS) to the build output directory
add_custom_command(TARGET StorageVisualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    "${CMAKE_CURRENT_SOURCE_DIR}/web"
    "$<TARGET_FILE_DIR:StorageVisualizer>/web"
)