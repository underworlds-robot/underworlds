#include <chrono>
#include <thread>

#include "gtest/gtest.h"

#include "uwds.hpp"

using namespace std;

#define WAIT_FOR_PROPAGATION std::this_thread::sleep_for(std::chrono::milliseconds(200))

template<typename T, typename V> bool isIn(const T& container, const V& value) {

    for (const V& v : container) {
        if (v == value) return true;
    }
    return false;
}

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

TEST_F(UnderworldsTest, Nodes) {

    auto& scene = ctxt.worlds["base"].scene();

    auto n1 = scene.new_node();

    WAIT_FOR_PROPAGATION;

    ASSERT_TRUE(isIn(scene.nodes, n1));

}

TEST_F(UnderworldsTest, NodesMultiContext) {

    auto& scene = ctxt.worlds["base"].scene();

    uwds::Context ctxt2("test2 client", "localhost:50051");
    auto& scene2 = ctxt2.worlds["base"].scene();

    ASSERT_EQ(scene.root(), scene2.root());

    auto n1 = scene.new_node();

    WAIT_FOR_PROPAGATION;

    
    ASSERT_TRUE(isIn(scene.nodes, n1));
    ASSERT_TRUE(isIn(scene2.nodes, n1));
}


TEST_F(UnderworldsTest, Hierarchy) {

    auto& scene = ctxt.worlds["base"].scene();

    auto n1 = scene.new_node();
    n1.set_parent(scene.root());
    
    ASSERT_TRUE(isIn(scene.root().children(), n1));

}

TEST_F(UnderworldsTest, HierarchyMultiContext) {

    auto& scene = ctxt.worlds["base"].scene();

    auto n1 = scene.new_node();
    n1.set_parent(scene.root());
    
    ASSERT_TRUE(isIn(scene.root().children(), n1));
    ASSERT_FALSE(isIn(n1.children(), scene.root()));

    uwds::Context ctxt2("test2 client", "localhost:50051");
    auto& scene2 = ctxt2.worlds["base"].scene();

    ASSERT_TRUE(isIn(scene2.root().children(), n1));
    ASSERT_FALSE(isIn(n1.children(), scene2.root()));

}



int main(int argc, char **argv) {
      ::testing::InitGoogleTest(&argc, argv);
        return RUN_ALL_TESTS();
}
