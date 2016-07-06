#include <chrono>

#include "gtest/gtest.h"

#include "uwds.hpp"

using namespace std;

class UnderworldsTest : public ::testing::Test {

public:
    uwds::Context ctxt;

    UnderworldsTest():ctxt("test client", "localhost:50051") {}

  virtual void SetUp() {
    ctxt.reset();
  }

  // virtual void TearDown() {}

};

TEST_F(UnderworldsTest, Uptime) {

    auto uptime = chrono::duration_cast<chrono::milliseconds>(ctxt.uptime()).count();
    EXPECT_GT (uptime, 0.);

    auto uptime2 = chrono::duration_cast<chrono::milliseconds>(ctxt.uptime()).count();

    EXPECT_GT (uptime2, uptime);

}

///////////// WORLDS

TEST_F(UnderworldsTest, Worlds) {

    auto worlds = ctxt.worlds;

    ASSERT_EQ (worlds.size(), 0);

    auto world1 = worlds["base"];

    EXPECT_EQ (worlds.size(), 1);

    auto world2 = worlds["test"];

    EXPECT_EQ (worlds.size(), 2);

    EXPECT_EQ(world1.name(), "base");

}

TEST_F(UnderworldsTest, WorldsMultiContext) {

    auto worlds = ctxt.worlds;

    ASSERT_EQ (worlds.size(), 0);

    uwds::Context ctxt2("test2 client", "localhost:50051");

    auto worlds2 = ctxt2.worlds;

    ASSERT_EQ (worlds2.size(), 0);

    auto world1 = worlds["base"];

    ASSERT_EQ (worlds.size(), 1);
    ASSERT_EQ (worlds2.size(), 1);
}

///////////// SCENES

TEST_F(UnderworldsTest, Scene) {

    auto world = ctxt.worlds["base"];

    ASSERT_EQ(world.scene().nodes.size(), 1); // only the root node

}

TEST_F(UnderworldsTest, NodeMirroring) {

    auto& scene = ctxt.worlds["world"].scene();
    auto& scene2 = ctxt.worlds["world2"].scene();

    auto n1 = scene.new_node();
    n1.set_parent(scene.root());

    ASSERT_EQ(scene.nodes.size(), 1); // only the root node

}

///////////// NODES

TEST_F(UnderworldsTest, RootNode) {

    auto& scene = ctxt.worlds["base"].scene();

    auto& root = scene.root();

    ASSERT_EQ(root, scene.nodes[root.id()]);

}

int main(int argc, char **argv) {
      ::testing::InitGoogleTest(&argc, argv);
        return RUN_ALL_TESTS();
}
