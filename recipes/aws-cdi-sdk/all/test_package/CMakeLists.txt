cmake_minimum_required(VERSION 3.15)
project(test_package C)

include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
conan_basic_setup(TARGETS)

find_package(aws-cdi-sdk REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} AWS::aws-cdi-sdk)
