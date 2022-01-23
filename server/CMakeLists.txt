cmake_minimum_required(VERSION 3.1)
project(server)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(THREADS_PREFER_PTHREAD_FLAG ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -lsqlite3")

find_package(Threads REQUIRED)
find_package(OpenCV REQUIRED)
find_package(SQLite3 REQUIRED)

include_directories( ${OpenCV_INCLUDE_DIRS} ${SQLITE3_INCLUDE_DIRS} src)

add_executable(server main.cpp)

target_link_libraries(server PRIVATE Threads::Threads ${OpenCV_LIBS} stdc++fs ${SQLITE3_LIBRARIES})