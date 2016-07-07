#include <iostream>
#include <string>
#include <chrono>
#include <thread>

#include "uwds.hpp"

#define WAIT_FOR_PROPAGATION std::this_thread::sleep_for(std::chrono::milliseconds(200))

using namespace std;
using namespace uwds;

void walk(uwds::Scene& scene, const weak_ptr<uwds::Node> node, string ident = " ") {
    cout << ident << "- " << node << endl;
    for (const auto child : NODELOCK(node).children()) {
        walk(scene, child, ident + " ");
    }
}

int main(int argc, char** argv) {

    uwds::Context ctxt("cpp client", "localhost:50051");

    auto uptime = ctxt.uptime();
    cout << "Server running since: " << chrono::duration_cast<chrono::minutes>(uptime).count() << "min" << endl;

    auto topo = ctxt.topology();

    cout << "Topology:" << endl << topo << endl;

    for (const auto& world : topo.worlds) {
        auto& scene = ctxt.worlds[world].scene();
        cout << "World <" << world << "> has root node " << scene.root() << endl;
        cout << "Nodes: " << endl;
        walk(scene, scene.root());

    }



    auto& scene = ctxt.worlds["base"].scene();

    cout << "Creating new node" << endl;
    auto node = scene.new_node();

    WAIT_FOR_PROPAGATION;

    cout << "Setting name -- should propagate immediately" << endl;
    node.lock()->set_name("test");
    WAIT_FOR_PROPAGATION;
    
    {
    cout << "Re-setting name -- should not propagate immediately" << endl;
    auto node_shared = node.lock();
    node_shared->set_name("test2");
    WAIT_FOR_PROPAGATION;
    cout << "Should propagate now" << endl;
    }

    WAIT_FOR_PROPAGATION;
    return 0;
}
