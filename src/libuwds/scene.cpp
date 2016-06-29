#include <system_error>

#include <grpc++/grpc++.h>

#include "underworlds.grpc.pb.h"

#include "uwds.hpp"

#include<iostream>

using grpc::Channel;
using grpc::Status;

using namespace std;
using namespace uwds;

Scene::Scene(Context& ctxt, const std::string& world) : _ctxt(ctxt), _world(world) {


    ///////////////////////////////////////////////
    // First, get the list of existing nodes
    
    underworlds::Context request;
    request.set_client(ctxt._myself.id());
    request.set_world(world);

    underworlds::Nodes reply;

    grpc::ClientContext context;

    // The actual RPC.
    Status status = _ctxt._server->getNodesIds(&context, request, &reply);

    if (!status.ok()) {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }

    for (int i = 0; i < reply.ids_size(); i++) {

        auto id = reply.ids(i);
        this->node(id);

    }

    ///////////////////////////////////////////////
    // Now, get the root node
    
    underworlds::Node reply2;

    grpc::ClientContext context2;

    // The actual RPC.
    status = _ctxt._server->getRootNode(&context2, request, &reply2);

    // Act upon its status.
    if (status.ok()) {
        root = node(reply2.id());
    } else {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }

}

shared_ptr<Node> Scene::node(const std::string& id, bool no_fetch) {


    for (const auto node : _nodes) {
        if (node->id == id) return node;
    }

    // -> the node does not exist locally: query the server

    if (no_fetch) {
        cout << "Node does not exist, but not fetching it: " << id << endl;
        return nullptr;
    }

    _fetchNode(id);
}

shared_ptr<Node> Scene::_fetchNode(const string& id) {

    cout << "Fetching node " << id << endl;
    underworlds::NodeInContext request;
    request.mutable_context()->set_client(_ctxt._myself.id());
    request.mutable_context()->set_world(_world);
    request.mutable_node()->set_id(id);

    underworlds::Node reply;

    grpc::ClientContext context;

    // The actual RPC.
    Status status = _ctxt._server->getNode(&context, request, &reply);

    // Act upon its status.
    if (status.ok()) {

        auto node = make_shared<Node>(Node::deserialize(reply, shared_ptr<Scene>(this)));
        _nodes.insert(node);
        return node;

    } else {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }

}

shared_ptr<Node> Scene::mirror(const shared_ptr<Node> source) {

    for (const auto node : _nodes) {
        if (node == source) return node;
    }

    // copy the source node
    auto node = make_shared<Node>(*source);

    // have we previously mirrored this node?
    if (_mappings.count(source->id)) {
        // yes, reuse the original ID
        node->id = _mappings[source->id];
    } else {
        // no, add this new mapping
        _mappings[source->id] = node->id;
    }

    // do we already know about the parent? (ie, the parent has been mirrored)
    if (_mappings.count(source->parent)) {
        auto parent = _mappings[source->parent];
        // yes, re-parent to the mirrored parent
        node->parent = parent;
        // ...and tell the parent we are one of its children
        this->node(parent)->children.insert(node->id);
        // push the change to the child to the server
        commit(*this->node(parent));
    } else {
        // no parent for now
        node->parent = nullptr;
    }

    // erase all the children (that are refering to nodes in the source world)
    node->children.clear();

    for(auto source_child : source->children) {
        // do we already know about the child? (ie, the child has been mirrored)
        if (_mappings.count(source_child)) {
            auto child = _mappings[source_child];
            // yes, add the child to our children
            node->children.insert(child);
            // ...and tell the child we are its parent
            this->node(child)->parent = node->id;
            // push the change to the child to the server
            commit(*this->node(child));

        } else {
        }
    }

    // push the node to the server
    commit(*node);



}

set<shared_ptr<Node>> Scene::nodeByName(const string& name) {

    set<shared_ptr<Node>> result;

    for (const auto node : _nodes) {
        if (node->name == name) result.insert(node);
    }

    return result;
}


void Scene::commit(const Node& node) {

    underworlds::NodeInContext request;
    request.mutable_context()->set_client(_ctxt._myself.id());
    request.mutable_context()->set_world(_world);

    auto gRPCNode = node.serialize();
    request.set_allocated_node(&gRPCNode);

    underworlds::Empty reply;

    grpc::ClientContext context;

    // The actual RPC.
    Status status = _ctxt._server->updateNode(&context, request, &reply);

    if (!status.ok()) {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }

}
