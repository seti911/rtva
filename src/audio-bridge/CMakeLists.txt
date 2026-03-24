cmake_minimum_required(VERSION 3.10)
project(audio_bridge)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find ALSA
find_package(PkgConfig REQUIRED)
pkg_check_modules(ALSA REQUIRED alsa)

include_directories(${ALSA_INCLUDE_DIRS})
link_directories(${ALSA_LIBRARY_DIRS})

# Source files
set(SOURCES
    src/audio_bridge.cpp
)

add_executable(audio_bridge ${SOURCES})

target_link_libraries(audio_bridge
    ${ALSA_LIBRARIES}
    pthread
)

# Installation
install(TARGETS audio_bridge DESTINATION bin)
