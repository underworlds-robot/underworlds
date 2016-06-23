cmake_minimum_required(VERSION 2.8)

project(underworlds)

SET(CMAKE_CXX_FLAGS "-std=c++11")

find_package(PkgConfig)
pkg_check_modules(PROTOBUF protobuf)
include_directories(${PROTOBUF_INCLUDE_DIRS})
pkg_check_modules(GRPC grpc++)
include_directories(${GRPC_INCLUDE_DIRS})
link_directories(${GRPC_LIBRARY_DIRS})


file(GLOB uwds_pb_src src/libuwds/*pb.cc)
add_library(libuwds SHARED src/libuwds/uwds.cpp ${uwds_pb_src})

add_executable( uwds_test src/libuwds/uwds_client.cpp )
target_link_libraries( uwds_test libuwds ${PROTOBUF_LIBRARIES} ${GRPC_LIBRARIES} )

install (TARGETS libuwds
         RUNTIME DESTINATION bin
         LIBRARY DESTINATION lib)

