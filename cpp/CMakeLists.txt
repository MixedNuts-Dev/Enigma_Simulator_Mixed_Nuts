cmake_minimum_required(VERSION 3.16)
project(EnigmaSimulator)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

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
)

set(CORE_HEADERS
    src/core/Rotor.h
    src/core/Reflector.h
    src/core/Plugboard.h
    src/core/EnigmaMachine.h
    src/core/RotorConfig.h
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
add_executable(enigma_console
    src/main_console.cpp
    ${CORE_SOURCES}
    ${CORE_HEADERS}
)

target_link_libraries(enigma_console 
    PRIVATE 
    Threads::Threads
    nlohmann_json::nlohmann_json
)

if(OpenMP_CXX_FOUND)
    target_link_libraries(enigma_console PRIVATE OpenMP::OpenMP_CXX)
endif()

# Include directories
target_include_directories(enigma_console PRIVATE src)

# Enable compiler optimizations for console app
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(enigma_console PRIVATE -O3)
elseif(MSVC)
    target_compile_options(enigma_console PRIVATE 
        $<$<CONFIG:Debug>:/Od /RTC1>
        $<$<CONFIG:Release>:/O2>
        /Zc:__cplusplus
        /utf-8
    )
endif()

# Build GUI application only if Qt6 is found
if(Qt6_FOUND)
    # Enigma GUI application
    add_executable(enigma_gui
        src/main_gui.cpp
        ${CORE_SOURCES}
        ${CORE_HEADERS}
        ${GUI_SOURCES}
        ${GUI_HEADERS}
    )

    target_link_libraries(enigma_gui 
        PRIVATE 
        Qt6::Core
        Qt6::Widgets
        Threads::Threads
        nlohmann_json::nlohmann_json
    )

    if(OpenMP_CXX_FOUND)
        target_link_libraries(enigma_gui PRIVATE OpenMP::OpenMP_CXX)
    endif()

    # Include directories
    target_include_directories(enigma_gui PRIVATE src)

    # Enable compiler optimizations
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(enigma_gui PRIVATE -O3)
    elseif(MSVC)
        # Use generator expressions to set different options for Debug and Release
        target_compile_options(enigma_gui PRIVATE 
            $<$<CONFIG:Debug>:/Od /RTC1>
            $<$<CONFIG:Release>:/O2>
            /Zc:__cplusplus 
            /permissive-
            /utf-8
        )
    endif()

    # Set Windows subsystem for GUI app
    if(WIN32)
        set_target_properties(enigma_gui PROPERTIES
            WIN32_EXECUTABLE TRUE
        )
    endif()
    
    message(STATUS "Qt6 found - GUI application will be built")
else()
    message(STATUS "Qt6 not found - Only console application will be built")
endif()