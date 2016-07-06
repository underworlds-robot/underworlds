#include <chrono>
#include <utility> // std::move
#include <system_error>

#include <boost/uuid/uuid_io.hpp>
#include <boost/uuid/uuid_generators.hpp>

#include "underworlds.pb.h"

#include "uwds.hpp"

using namespace std;
using namespace uwds;



Node::Node(weak_ptr<Scene> scene) : _id(boost::uuids::to_string(boost::uuids::random_generator()())),
                                    _scene(scene){};

Node Node::clone() const {

    auto node = Node(_scene);
    node._name = _name;
    node._type = _type;
    node._parent = _parent;
    node._children = _children;
    node._transform = _transform;

    node._update();

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


Node Node::deserialize(const underworlds::Node& remoteNode, weak_ptr<Scene> scene) {

    auto node = Node(scene);
    node._id = remoteNode.id();
    node._name = remoteNode.name();
    node._type = (NodeType) remoteNode.type();
    
    node._parent = remoteNode.parent();

    for(int i = 0; i < remoteNode.children_size(); i++) {
        node._children.insert(remoteNode.children(i));

    }


    return node;
}

const Node& Node::parent() const {
    return _scene.lock()->nodes[_parent];
}

Node& Node::parent() {
    return _scene.lock()->nodes[_parent];
}

void Node::set_parent(Node& parent) {
    _parent=parent.id();
    parent.append_child(*this);
    _update();
}

void Node::clear_parent() {
    _scene.lock()->nodes[_parent].remove_child(*this);
    _parent="";
    _update();
}

set<reference_wrapper<Node>> Node::children() {

    set<reference_wrapper<Node>> children;

    for (const auto& child : _children) {
        children.insert(_scene.lock()->nodes[child]);
    }
    return children;
}

const set<reference_wrapper<const Node>> Node::children() const {

    set<reference_wrapper<const Node>> children;

    for (const auto& child : _children) {
        children.insert(_scene.lock()->nodes[child]);
    }
    return children;
}

void Node::append_child(Node& child) {

    // check if the child was not already there while inserting
    if(_children.insert(child.id()).second) {
        child.set_parent(*this);
        _update();
    }
}

void Node::remove_child(Node& child) {
    child.clear_parent();
    _children.erase(child.id());
    _update();
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

