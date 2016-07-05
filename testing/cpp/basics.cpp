#include <chrono>

#include "gtest/gtest.h"

#include "uwds.hpp"

using namespace std;

TEST (UnderworldsBasics, Uptime) {

        uwds::Context ctxt("test client", "localhost:50051");

        auto uptime = chrono::duration_cast<chrono::milliseconds>(ctxt.uptime()).count();
        EXPECT_GT (uptime, 0.);

        auto uptime2 = chrono::duration_cast<chrono::milliseconds>(ctxt.uptime()).count();

        EXPECT_GT (uptime2, uptime);

}

int main(int argc, char **argv) {
      ::testing::InitGoogleTest(&argc, argv);
        return RUN_ALL_TESTS();
}
