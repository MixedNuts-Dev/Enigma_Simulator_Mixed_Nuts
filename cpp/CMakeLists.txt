cmake_minimum_required(VERSION 3.16)
project(EnigmaSimulatorCpp VERSION 1.0.0 DESCRIPTION "Enigma Machine Simulator - C++ Version")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

# Option for static runtime
option(USE_STATIC_RUNTIME "Use static runtime libraries" OFF)

# Set runtime library for MSVC
if(MSVC AND USE_STATIC_RUNTIME)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

# Find packages
find_package(Threads REQUIRED)
# Make Qt6 optional
find_package(Qt6 COMPONENTS Core Widgets QUIET)

# Download and setup nlohmann/json
include(FetchContent)
FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
)
FetchContent_MakeAvailable(json)

# Enable OpenMP for parallel processing
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
endif()

set(CORE_SOURCES
    src/core/Rotor.cpp
    src/core/Reflector.cpp
    src/core/Plugboard.cpp
    src/core/EnigmaMachine.cpp
    src/core/BombeAttack.cpp
    src/core/DiagonalBoard.cpp
)

set(CORE_HEADERS
    src/core/Rotor.h
    src/core/Reflector.h
    src/core/Plugboard.h
    src/core/EnigmaMachine.h
    src/core/RotorConfig.h
    src/core/BombeAttack.h
    src/core/DiagonalBoard.h
)

set(GUI_SOURCES
    src/gui/EnigmaMainWindow.cpp
    src/gui/BombeWindow.cpp
)

set(GUI_HEADERS
    src/gui/EnigmaMainWindow.h
    src/gui/BombeWindow.h
)

# Enigma console application
add_executable(enigma_console_cpp
    src/main_console.cpp
    ${CORE_SOURCES}
    ${CORE_HEADERS}
)

# Set output name
set_target_properties(enigma_console_cpp PROPERTIES
    OUTPUT_NAME "EnigmaSimulatorCpp"
    RUNTIME_OUTPUT_NAME "EnigmaSimulatorCpp"
)

target_link_libraries(enigma_console_cpp 
    PRIVATE 
    Threads::Threads
    nlohmann_json::nlohmann_json
)

if(OpenMP_CXX_FOUND)
    target_link_libraries(enigma_console_cpp PRIVATE OpenMP::OpenMP_CXX)
endif()

# Include directories
target_include_directories(enigma_console_cpp PRIVATE src)

# Enable compiler optimizations for console app
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(enigma_console_cpp PRIVATE -O3)
elseif(MSVC)
    target_compile_options(enigma_console_cpp PRIVATE 
        $<$<CONFIG:Debug>:/Od /RTC1>
        $<$<CONFIG:Release>:/O2>
        /Zc:__cplusplus
        /utf-8
    )
endif()

# Build GUI application only if Qt6 is found
if(Qt6_FOUND)
    # Enigma GUI application
    add_executable(enigma_gui_cpp
        src/main_gui.cpp
        ${CORE_SOURCES}
        ${CORE_HEADERS}
        ${GUI_SOURCES}
        ${GUI_HEADERS}
    )

    # Set output name for GUI
    set_target_properties(enigma_gui_cpp PROPERTIES
        OUTPUT_NAME "EnigmaSimulatorCppGUI"
        RUNTIME_OUTPUT_NAME "EnigmaSimulatorCppGUI"
    )

    target_link_libraries(enigma_gui_cpp 
        PRIVATE 
        Qt6::Core
        Qt6::Widgets
        Threads::Threads
        nlohmann_json::nlohmann_json
    )

    if(OpenMP_CXX_FOUND)
        target_link_libraries(enigma_gui_cpp PRIVATE OpenMP::OpenMP_CXX)
    endif()

    # Include directories
    target_include_directories(enigma_gui_cpp PRIVATE src)

    # Enable compiler optimizations
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(enigma_gui_cpp PRIVATE -O3)
    elseif(MSVC)
        # Use generator expressions to set different options for Debug and Release
        target_compile_options(enigma_gui_cpp PRIVATE 
            $<$<CONFIG:Debug>:/Od /RTC1>
            $<$<CONFIG:Release>:/O2>
            /Zc:__cplusplus 
            /permissive-
            /utf-8
        )
    endif()

    # Set Windows subsystem for GUI app
    if(WIN32)
        set_target_properties(enigma_gui_cpp PROPERTIES
            WIN32_EXECUTABLE TRUE
        )
    endif()
    
    message(STATUS "Qt6 found - GUI application will be built")
else()
    message(STATUS "Qt6 not found - Only console application will be built")
endif()

# Installation settings
install(TARGETS enigma_console_cpp
    RUNTIME DESTINATION bin
    COMPONENT runtime
)

if(Qt6_FOUND)
    install(TARGETS enigma_gui_cpp
        RUNTIME DESTINATION bin
        COMPONENT runtime
    )
endif()

# Set installation paths
set(CMAKE_INSTALL_PREFIX "C:/Program Files/Enigma Simulator Cpp" CACHE PATH "Installation directory")

# CPack settings for creating installers
set(CPACK_GENERATOR "NSIS")
set(CPACK_PACKAGE_NAME "Enigma Simulator Cpp")
set(CPACK_PACKAGE_VENDOR "MixedNuts tukasa")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Enigma Machine Simulator - C++ Version")
set(CPACK_PACKAGE_VERSION_MAJOR "1")
set(CPACK_PACKAGE_VERSION_MINOR "0")
set(CPACK_PACKAGE_VERSION_PATCH "0")
set(CPACK_PACKAGE_INSTALL_DIRECTORY "Enigma Simulator Cpp")
set(CPACK_NSIS_DISPLAY_NAME "Enigma Simulator C++")
set(CPACK_NSIS_MODIFY_PATH ON)

include(CPack)