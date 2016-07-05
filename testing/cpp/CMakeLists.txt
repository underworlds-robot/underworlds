find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

add_executable(basics basics.cpp)
target_link_libraries(basics 
                        libuwds 
                        ${GTEST_BOTH_LIBRARIES}
                        ${PROTOBUF_LIBRARIES}
                        ${GRPC_LIBRARIES} )

add_test(AllTestsInUnderworlds basics)
