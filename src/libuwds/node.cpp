#include <chrono>
#include <system_error>

#include <boost/uuid/uuid_io.hpp>
#include <boost/uuid/uuid_generators.hpp>

#include "underworlds.pb.h"

#include "uwds.hpp"

using namespace std;
using namespace uwds;



Node::Node() : id(boost::uuids::to_string(boost::uuids::random_generator()())) {};

Node::Node(const Node&& n) : id(n.id),
                      name(n.name),
                      type(n.type),
                      parent(n.parent),
                      children(n.children),
                      transform(n.transform),
                      last_update(n.last_update) {}


Node Node::clone() const {

    auto node = Node();
    node.name = name;
    node.type = type;
    node.parent = parent;
    node.children = children;
    node.transform = transform;
    node.last_update = chrono::system_clock::now();

    return node;
}

underworlds::Node Node::serialize() const {

    underworlds::Node node;
    node.set_id(id);
    node.set_name(name);
    node.set_type((underworlds::Node_NodeType) type);

    node.set_parent(parent);

    for (const auto& child : children) {
        node.add_children(child);
    }

    return node;
}


Node Node::deserialize(const underworlds::Node& remoteNode) {

    auto node = Node();
    node.id = remoteNode.id();
    node.name = remoteNode.name();
    node.type = (NodeType) remoteNode.type();
    
    node.parent = remoteNode.parent();

    for(int i = 0; i < remoteNode.children_size(); i++) {
        node.children.insert(remoteNode.children(i));

    }


    return node;
}


std::ostream& operator<<(std::ostream& os, const uwds::Node& node)
{
    os << node.name << " [" << node.id << "]";
    return os;
}

