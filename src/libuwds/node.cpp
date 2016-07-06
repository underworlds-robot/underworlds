#include <chrono>
#include <system_error>

#include <boost/uuid/uuid_io.hpp>
#include <boost/uuid/uuid_generators.hpp>

#include "underworlds.pb.h"

#include "uwds.hpp"

using namespace std;
using namespace uwds;



Node::Node() : _id(boost::uuids::to_string(boost::uuids::random_generator()())) {};

Node::Node(const Node&& n) : _id(n._id),
                      _name(n._name),
                      _type(n._type),
                      _parent(n._parent),
                      _children(n._children),
                      _transform(n._transform),
                      _last_update(n._last_update) {}


Node Node::clone() const {

    auto node = Node();
    node.set_name(_name);
    node.set_type(_type);
    node.set_parent(_parent);
    node.set_children(_children);
    node.set_transform(_transform);

    return node;
}

underworlds::Node Node::serialize() const {

    underworlds::Node node;
    node.set_id(_id);
    node.set_name(_name);
    node.set_type((underworlds::Node_NodeType) _type);

    node.set_parent(_parent);

    for (const auto& child : _children) {
        node.add_children(child);
    }

    return node;
}


Node Node::deserialize(const underworlds::Node& remoteNode) {

    auto node = Node();
    node._id = remoteNode.id();
    node._name = remoteNode.name();
    node._type = (NodeType) remoteNode.type();
    
    node._parent = remoteNode.parent();

    for(int i = 0; i < remoteNode.children_size(); i++) {
        node._children.insert(remoteNode.children(i));

    }


    return node;
}

void Node::_update() {
    _is_locally_dirty = true;
    _last_update = chrono::system_clock::now();
}

std::ostream& operator<<(std::ostream& os, const uwds::Node& node)
{
    os << node.name() << " [" << node.id() << "]";
    return os;
}

