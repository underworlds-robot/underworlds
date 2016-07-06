#include <system_error>


#include <grpc++/grpc++.h>

#include "underworlds.grpc.pb.h"

#include "uwds.hpp"

#include<iostream>

using grpc::Channel;
using grpc::Status;

using namespace std;
using namespace uwds;

Scene::Scene(Context& ctxt) : _ctxt(ctxt),
                              nodes(ctxt) {}

void Scene::initialize(const std::string& world) {

    _world = world;
    nodes._scene = shared_from_this();

    ///////////////////////////////////////////////
    // First, get the list of existing nodes
    
    underworlds::Context request;
    request.set_client(_ctxt._myself.id());
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

        // As side-effect, fetch and add locally the nodes
        nodes[id];

    }

    ///////////////////////////////////////////////
    // Now, get the root node
    
    underworlds::Node reply2;

    grpc::ClientContext context2;

    // The actual RPC.
    status = _ctxt._server->getRootNode(&context2, request, &reply2);

    // Act upon its status.
    if (status.ok()) {
        _root = nodes._nodes.at(reply2.id());
    } else {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }

}

Node& Scene::mirror(const Node& source) {

    // The source node already exists in the current scene
    if (nodes.has(source)) return nodes[source.id()];

    // clone the source node
    auto node = source.clone();

    // have we previously mirrored this node?
    if (_mappings.count(source.id())) {
        // yes, reuse the original ID
        node._id = _mappings[source.id()];
    } else {
        // no, add this new mapping
        _mappings[source.id()] = node.id();
    }

    // do we already know about the parent? (ie, the parent has been mirrored)
    if (_mappings.count(source.parent().id())) {

        auto& parent = nodes[_mappings[source.parent().id()]];

        // yes, re-parent to the mirrored parent
        node.set_parent(parent);
        // ...and tell the parent we are one of its children
        parent.append_child(node);
        // push the change to the child to the server
        commit(parent);

    } else {
        // no parent for now
        node.clear_parent();
    }


    // erase all the children (that are refering to nodes in the source world)
    node._children.clear();

    for(auto& source_child : source.children()) {
        // do we already know about the child? (ie, the child has been mirrored)
        if (_mappings.count(source_child.get().id())) {
            auto& child = nodes[_mappings[source_child.get().id()]];
            // yes, add the child to our children
            node.append_child(child);
            // ...and tell the child we are its parent
            child.set_parent(node);
            // push the change to the child to the server
            commit(child);

        }
    }

    // push the node to the server
    commit(node);

    // loopback: queries back the server to retrieve the newly mirrored node
    return nodes[node.id()];



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
