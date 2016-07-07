#ifndef NODES_HPP
#define NODES_HPP

#include "underworlds.grpc.pb.h"
#include "concurrent_set.hpp"

namespace uwds {

class Context;
class Scene;
class Node;

class Nodes {
    friend class Scene; // give Scene access to our private constructor
    friend class Node; // give Node access to _add_node and _locally_dirty_nodes

public:
    typedef std::map<std::string, std::shared_ptr<Node>> NodeMap;
    
    // no copies! move only
    Nodes(const Nodes&) = delete;
    Nodes(Nodes&&) = default;

    ~Nodes();

    // Returns a node from its ID. If the node is not available, throws an
    // out_of_range exception.
    //
    // As a side-effect, if the node is not locally available, queries the remote
    // server for possible new nodes.
    //
    // See Nodes::at for a version that does not attempt to query the remote
    // server.
    NodePtr operator[](const std::string& id);
    ConstNodePtr operator[](const std::string& id) const;

    // Returns a node from its ID. If the node is not available, throws an
    // out_of_range exception.
    //
    // This method does not attempt to fetch new nodes from the server. Use
    // Node::operator[] instead.
    NodePtr at(const std::string& id) {return _nodes.at(id);}
    ConstNodePtr at(const std::string& id) const {return _nodes.at(id);}

    /** Returns all the nodes whose name matches the argument.
     */
    std::set<NodePtr> from_name(const std::string& name);

    // Returns true if the node exists
    bool has(const std::string& id) const {return _nodes.count(id) != 0;}
    bool has(ConstNodePtr node) const {return has(node.lock()->id());}

    // Returns the number of existing nodes
    size_t size() const {return _nodes.size();}

private:
    class Iterator {

        NodeMap::iterator _it_map;

        public:
            Iterator(NodeMap::iterator it_map):_it_map(it_map) {}

            NodePtr operator*() { return (*_it_map).second; }
            Iterator& operator++() { ++_it_map; return *this; }
            bool operator!=(const Iterator& it) const { return _it_map != it._it_map; }
    };

    class ConstIterator {

        NodeMap::const_iterator _it_map;

        public:
            ConstIterator(NodeMap::const_iterator it_map):_it_map(it_map) {}

            ConstNodePtr operator*() const { return (*_it_map).second; }
            ConstIterator& operator++() { ++_it_map; return *this; }
            bool operator!=(const ConstIterator& it) const { return _it_map != it._it_map; }
    };

public:
    Iterator begin() {return {_nodes.begin()};}
    Iterator end() {return {_nodes.end()};}

    ConstIterator begin() const {return {_nodes.begin()};}
    ConstIterator end() const {return {_nodes.end()};}

private:
    Nodes(Context& ctxt);
    Context& _ctxt;
    std::weak_ptr<Scene> _scene;

    // _fetch does modify _nodes by fetching nodes from the server,
    // but I consider it 'semantically' const as it is purely internal
    // from the persepective of the API user
    const std::shared_ptr<const Node> _fetch(const std::string&) const;

    // the non-const version allows for modification to the returned Node
    std::shared_ptr<Node> _fetch(const std::string&);

    // the _nodes map might be modified by updates from the server
    // without changing the apparent 'semantic' constness of methods
    mutable NodeMap _nodes;

    /** Adds the node to my list of nodes
     */
    void _add_node(std::shared_ptr<Node> node);


    // This is the concurrent queue used to store the nodes that need to be
    // sent to the server
    ConcurrentNodeSet _locally_dirty_nodes;

    void _remote_communication();
    bool _remote_communication_running;
    std::thread _remote_communication_thread;
};

}

#endif
