#ifndef UWDS_HPP
#define UWDS_HPP

#include <memory>
#include <string>
#include <chrono>
#include <set>
#include <vector>
#include <array>
#include <iostream>
#include <opencv2/core/core.hpp> // for transformation matrices

#include "underworlds.grpc.pb.h"


namespace uwds {

/////////////////////////////////////////////////////////////////////////
///////////  GENERAL TYPES

typedef cv::Matx44d Transformation;

enum InteractionType {
    READER = 0,
    PROVIDER,
    MONITOR,
    FILTER
};
static const std::array<std::string,4> InteractionTypeName{"reader", "provider", "monitor", "filter"};

struct Interaction {
    std::string world;
    InteractionType type;
    std::chrono::system_clock::time_point last_activity;
};

struct Client {
    std::string id;
    std::string name;
    std::vector<Interaction> links;

    bool operator<(Client other) const
    {
        return id > other.id;
    }
};

struct Topology {
    std::set<std::string> worlds;
    std::set<Client> clients;

};

/////////////////////////////////////////////////////////////////////////
///////////  NODES TYPES

enum NodeType {
    UNDEFINED = 0,
    ENTITY,
    MESH,
    CAMERA
};
static const std::array<std::string,4> NodeTypeName{"undefined", "entity", "mesh", "camera"};

class Scene;

struct Node {

    Node(std::shared_ptr<Scene> scene) : _scene(scene) {};

    std::string id;
    std::string name;
    NodeType type;
    std::shared_ptr<Node> parent;
    std::set<std::shared_ptr<Node>> children;
    Transformation transform;
    std::chrono::system_clock::time_point last_update;

    underworlds::Node serialize() const;
    static Node deserialize(const underworlds::Node&, std::shared_ptr<Scene> scene);

private:
    std::shared_ptr<Scene> _scene;
};

/////////////////////////////////////////////////////////////////////////
///////////  API

class Context;
class Worlds;
class World;

class Scene {
    friend class World; // give World access to our private constructor

public:
    std::shared_ptr<Node> root;
    std::set<std::shared_ptr<Node>> nodes() {return _nodes;}

    // Returns a node from its ID. If the node is not locally available, queries the
    // server.
    std::shared_ptr<Node> node(const std::string& id);

private:
    // only class World (friend) can create a new world
    Scene(Context& ctxt, const std::string& world);

    Context& _ctxt;
    std::string _world;

    std::set<std::shared_ptr<Node>> _nodes;

};


class World {
    friend class Worlds; // give Worlds access to our private constructor

public:

    std::string name() const {return _name;}

    Scene scene;

private:
    // only class Worlds (friend) can create a new world
    World(Context& ctxt, const std::string& name);

    std::string _name;
    Context& _ctxt;
};

class Worlds {
    friend class Context; // give Context access to our private constructor

public:
    std::shared_ptr<World> operator[](const std::string& world);

private:
    Worlds(Context& ctxt);
    Context& _ctxt;

    std::map<std::string, std::shared_ptr<World>> _worlds;
};

class Context {

    friend class World; // World can access _server
    friend class Scene; // Scene can access _server

public:
    Context(const std::string& name, const std::string& address="localhost:50051");

    std::string name() const {return _name;}
    std::string id() const {return _myself.id();}

    std::chrono::duration<double> uptime();
    Topology topology();


    Worlds worlds;


private:
    std::string helo(const std::string& name);

    std::string _name;
    std::string _id;
    std::unique_ptr<underworlds::Underworlds::Stub> _server;
    underworlds::Client _myself;
};


}

std::ostream& operator<<(std::ostream& os, const uwds::Topology& topo);
std::ostream& operator<<(std::ostream& os, const uwds::Node& topo);

#endif


