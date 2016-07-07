#include <chrono>
#include <utility> // std::move
#include <system_error>

#include <boost/uuid/uuid_io.hpp>
#include <boost/uuid/uuid_generators.hpp>

#include "node.hpp"
#include "scene.hpp"

using namespace std;
using namespace uwds;

Node::Node(weak_ptr<Scene> scene) : _id(boost::uuids::to_string(boost::uuids::random_generator()())),
                                    _scene(scene){};

weak_ptr<Node> Node::clone() const {

    // make an exact copy of myself
    auto node = shared_ptr<Node>(new Node(*this));
    // generate a new id
    node->_id = boost::uuids::to_string(boost::uuids::random_generator()());

    // mark the new node as dirty and update the 'last_update' timestamp
    node->_update();

    _scene.lock()->_add_node(node);

    // returns a weak_ptr pointing to the node as stored in Scene::nodes
    return _scene.lock()->nodes[node->id()]; 
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

ConstNodePtr Node::parent() const {
    return _scene.lock()->nodes[_parent];
}

NodePtr Node::parent() {
    return _scene.lock()->nodes[_parent];
}

void Node::set_parent(NodePtr parent_ptr) {

    auto& parent = NODELOCK(parent_ptr);

    _parent=parent.id();
    parent.append_child(shared_from_this());
    _update();
}

void Node::clear_parent() {
    parent().lock()->remove_child(shared_from_this());
    _parent="";
    _update();
}

set<weak_ptr<Node>> Node::children() {

    set<weak_ptr<Node>> children;

    for (const auto& child : _children) {
        children.insert(_scene.lock()->nodes[child]);
    }
    return children;
}

const set<weak_ptr<const Node>> Node::children() const {

    set<weak_ptr<const Node>> children;

    for (const auto& child : _children) {
        children.insert(_scene.lock()->nodes[child]);
    }
    return children;
}

void Node::append_child(NodePtr child_ptr) {

    auto& child = NODELOCK(child_ptr);

    // check if the child was not already there while inserting
    if(_children.insert(child.id()).second) {
        child.set_parent(shared_from_this());
        _update();
    }
}

void Node::remove_child(NodePtr child_ptr) {

    auto& child = NODELOCK(child_ptr);

    child.clear_parent();
    _children.erase(child.id());
    _update();
}


void Node::_update() {
    _is_locally_dirty = true;
    _last_update = chrono::system_clock::now();
}

std::ostream& operator<<(std::ostream& os, const Node& node)
{
    os << node.name() << " [" << node.id() << "]";
    return os;
}

std::ostream& operator<<(std::ostream& os, const weak_ptr<const Node> node)
{
    auto nodePtr = node.lock();
    os << nodePtr->name() << " [" << nodePtr->id() << "]";
    return os;
}

