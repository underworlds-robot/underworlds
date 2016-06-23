#include <iostream>
#include <string>

#include "uwds.hpp"

using namespace std;

int main(int argc, char** argv) {

    uwds::Context ctxt("cpp client", "localhost:50051");

        string name("cpp client");
    auto uptime = ctxt.uptime();
    cout << "Server running since: " << chrono::duration_cast<chrono::minutes>(uptime).count() << "min" << endl;

    auto topo = ctxt.topology();

    cout << "Topology:" << endl << topo << endl;
    return 0;
}
