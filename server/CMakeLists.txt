cmake_minimum_required(VERSION 3.1)
project(server)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(THREADS_PREFER_PTHREAD_FLAG ON)

find_package(Threads REQUIRED)
find_package( OpenCV REQUIRED )

include_directories( ${OpenCV_INCLUDE_DIRS} )

add_executable(server main.cpp)

target_link_libraries(server PRIVATE Threads::Threads ${OpenCV_LIBS} stdc++fs)