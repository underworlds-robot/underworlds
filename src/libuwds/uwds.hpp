#ifndef UWDS_HPP
#define UWDS_HPP

#include <memory>
#include <thread>
#include <string>
#include <chrono>
#include <map>
#include <set>
#include <vector>
#include <array>
#include <iostream>

#include "base_types.hpp"

namespace uwds {

class Scene;
class Worlds;
class Context;

class World {
    friend class Worlds; // give Worlds access to our private constructor

public:

    std::string name() const {return _name;}

    Scene& scene() {return *_scene;}

private:
    // only class Worlds (friend) can create a new world
    World(Context& ctxt, const std::string& name);

    std::shared_ptr<Scene> _scene;

    std::string _name;
    Context& _ctxt;
};

class Worlds {
    friend class Context; // give Context access to our private constructor

public:
    World& operator[](const std::string& world);

    size_t size() {return _worlds.size();}

private:
    Worlds(Context& ctxt);
    Context& _ctxt;

    std::map<std::string, std::shared_ptr<World>> _worlds;
};

class Context {

    friend class World; // World can access _server
    friend class Scene; // Scene can access _server
    friend class Nodes; // Scene can access _server

public:
    Context(const std::string& name, const std::string& address="localhost:50051");

    std::string name() const {return _name;}
    std::string id() const {return _myself.id();}

    std::chrono::duration<double> uptime();
    Topology topology();


    Worlds worlds;

    /** Resets Underworlds
     *
     * All the worlds are destroyed on the server.
     */
    void reset();


private:
    std::string helo(const std::string& name);

    std::string _name;
    std::string _id;
    std::unique_ptr<underworlds::Underworlds::Stub> _server;
    underworlds::Client _myself;
};


}

std::ostream& operator<<(std::ostream& os, const uwds::Topology& topo);

#endif


