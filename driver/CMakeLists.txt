cmake_minimum_required(VERSION 3.10)
project(driver)

SET(CMAKE_C_STANDARD 99)

include_directories(${OPAE_INCLUDE_DIR}
  ${OPAE_SDK_SOURCE}/libopae/src
  ${PROJECT_SOURCE_DIR})

add_library(driver SHARED
  buffer.c
  fpga.c)
target_link_libraries(driver
  ${libjson-c_LIBRARIES}
  uuid
  hugetlbfs
  ${CMAKE_THREAD_LIBS_INIT}
  opae-c)
