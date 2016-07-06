#ifndef UWDS_HPP
#define UWDS_HPP

#include <memory>
#include <iterator>
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
    friend class Scene; // give Scene access to my constructor and Scene::mirror access to _id


    /** Delete copy-constructor
     *
     * Prevents the copy to another node, as it would break the invariant
     * that nodes are unique (unique ID)
     */
    Node(const Node&) = delete;
    Node(Node&&) = default;

    bool operator==(const Node& n) const {return n._id == _id;}
    
    // Creates a new node that is identical to this one, except for the ID
    Node clone() const;
    underworlds::Node serialize() const;
    static Node deserialize(const underworlds::Node&, std::weak_ptr<Scene>);

    //////////////////////
    // ACCESSORS
    std::string id() const {return _id;}

    std::string name() const {return _name;}
    void set_name(const std::string& name) {_name=name;_update();}

    NodeType type() const {return _type;}
    void set_type(NodeType type) {_type=type;_update();}

    Node& parent();
    const Node& parent() const;

    /** Sets the given node to be my parent. Adds myself to the parent's children
     * (the given Node is modified).
     */
    void set_parent(Node&);
    void clear_parent();

    std::set<std::reference_wrapper<Node>> children();
    const std::set<std::reference_wrapper<const Node>> children() const;
    /** Adds the given node to my children. Set myself as the parent of the
     * given node (the given Node is modified).
     */
    void append_child(Node&);
    void remove_child(Node&);

    const Transformation& transform() const {return _transform;}
    void set_transform(Transformation transform) {_transform=transform;_update();}

    std::chrono::system_clock::time_point last_update() const {return _last_update;}
    ///////////////////
    
private:

    Node(std::weak_ptr<Scene> scene);

    std::string _id;
    std::string _name;
    NodeType _type;
    std::string _parent;
    std::set<std::string> _children;
    Transformation _transform;
    std::chrono::system_clock::time_point _last_update;

    /** True if the node has been updated on the server, but not yet locally
     */
    bool _is_remotely_dirty;
    /** True if the node has been updated locally, but not yet synchronized with the server
     */
    bool _is_locally_dirty;
    void _update();

    std::weak_ptr<Scene> _scene;
};

// make less-than operator a non-member for implicit conversions on from
// std::reference_wrapper<T> (when storing ref to Node in sets for instance)
inline bool operator<(const Node& n1, const Node& n2) {return n1.id() < n2.id();}

/////////////////////////////////////////////////////////////////////////
///////////  API

class Context;
class Worlds;
class World;

class Nodes {
    friend class Scene; // give Scene access to our private constructor

public:
    typedef std::map<std::string, std::shared_ptr<Node>> NodeMap;
    
    // no copies! move only
    Nodes(const Nodes&) = delete;
    Nodes(Nodes&&) = default;


    // Returns a node from its ID. If the node is not available, throws an
    // out_of_range exception.
    //
    // As a side-effect, if the node is not locally available, queries the remote
    // server for possible new nodes.
    //
    // See Nodes::at for a version that does not attempt to query the remote
    // server.
    Node& operator[](const std::string& id);
    const Node& operator[](const std::string& id) const;

    // Returns a node from its ID. If the node is not available, throws an
    // out_of_range exception.
    //
    // This method does not attempt to fetch new nodes from the server. Use
    // Node::operator[] instead.
    Node& at(const std::string& id) {return *_nodes.at(id);}
    const Node& at(const std::string& id) const {return *_nodes.at(id);}

    /** Returns all the nodes whose name matches the argument.
     */
    std::set<std::reference_wrapper<Node>> from_name(const std::string& name);

    // Returns true if the node exists
    bool has(const std::string& id) const {return _nodes.count(id) != 0;}
    bool has(const Node& node) const {return has(node.id());}

    // Returns the number of existing nodes
    size_t size() const {return _nodes.size();}

    class Iterator {

        NodeMap::const_iterator _it_map;

        public:
            Iterator(NodeMap::const_iterator it_map):_it_map(it_map) {}

            const Node& operator*() { return *(*_it_map).second; }
            Iterator& operator++() { ++_it_map; return *this; }
            bool operator!=(const Iterator& it) const { return _it_map != it._it_map; }
    };

    Iterator begin() {return {_nodes.begin()};}
    Iterator end() {return {_nodes.end()};}

private:
    Nodes(Context& ctxt);
    Context& _ctxt;
    std::weak_ptr<Scene> _scene;

    std::shared_ptr<Node> _fetch(const std::string&);
    const std::shared_ptr<const Node> _fetch(const std::string&) const;

    // the _nodes map might be modified by updates from the server
    // without changing the apparent 'semantic' constness of methods
    mutable NodeMap _nodes;
};

class Scene : public std::enable_shared_from_this<Scene> {
    friend class World; // give World access to our private constructor
    friend class Nodes; // give Nodes access to _world

public:

    // no copies! move only
    Scene(const Scene&) = delete;
    Scene(Scene&&) = default;

    Node& root() const {return *_root.lock();}
    Nodes nodes;

    Node new_node() {return Node(shared_from_this());}

    /** Mirrors a node coming from a different scene to the current scene.
     *
     * If the source node already exists in the current scene, returns it
     * immediately (the node is not modified).
     *
     * Otherwise, a copy of the source node is created in the current scene
     * (mirrored node).
     *
     * The mirrored node is not an exact copy:
     *  - the mirrored node has its own unique ID 
     *  - the parent and children of the node are the mirrors of the
     *    source parent/children in the current scene.
     *
     * If the parent/children have not been mirrored in the current scene, they
     * are left out of the mirrored node (the parenting is however restored if
     * the source parent/children are mirrored at a later stage).
     *
     * The mapping between the source node and the mirrored node is saved: if
     * Scene::mirror is called again with the same source node, the previously
     * mirrored node will be updated instead of newly created.
     */
    Node& mirror(const Node& source);


    /** Commits the changes operated on a node to the underworlds server.
     *
     * If the node has never been committed before, the node is created on the server.
     *
     * The changes performed on the node are only visible to the other
     * underworlds clients after Scene::commit has been called (note that
     * the propagation to all the client may take up to 100ms, depending on the
     * network)
     */
    void commit(const Node& node);

    /** alias for commit
     */
    void append(const Node& node) {return commit(node);}

private:
    // only class World (friend) can create a new world
    // Scene::initialize should be call immediately
    // after Scene is constructed.
    Scene(Context& ctxt);
    void initialize(const std::string& world);

    Context& _ctxt;
    std::string _world;

    std::weak_ptr<Node> _root;

    /** Holds the node ID mappings needed by Scene::mirror
     */
    std::map<std::string, std::string> _mappings;

};


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
std::ostream& operator<<(std::ostream& os, const uwds::Node& topo);

#endif


