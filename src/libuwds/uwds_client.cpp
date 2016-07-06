#include <iostream>
#include <string>

#include "uwds.hpp"

using namespace std;

void walk(uwds::Scene& scene, const uwds::Node& node, string ident = " ") {
    cout << ident << "- " << node << endl;
    for (const auto child : node.children()) {
        walk(scene, scene.nodes[child], ident + " ");
    }
}

int main(int argc, char** argv) {

    uwds::Context ctxt("cpp client", "localhost:50051");

    auto uptime = ctxt.uptime();
    cout << "Server running since: " << chrono::duration_cast<chrono::minutes>(uptime).count() << "min" << endl;

    auto topo = ctxt.topology();

    cout << "Topology:" << endl << topo << endl;


    for (const auto& world : topo.worlds) {
        auto scene = ctxt.worlds[world].scene;
        cout << "World <" << world << "> has root node " << scene.root() << endl;
        cout << "Nodes: " << endl;
        walk(scene, scene.root());

    }

    return 0;
}
