#include <system_error>
#include<iostream>


#include <grpc++/grpc++.h>

#include "underworlds.grpc.pb.h"

#include "uwds.hpp"
#include "scene.hpp"


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

weak_ptr<Node> Scene::new_node() {
    auto node = shared_ptr<Node>(new Node(shared_from_this()));
    node->_update();
    _add_node(node);

    return nodes[node->id()];

}

weak_ptr<Node> Scene::mirror(const weak_ptr<const Node> source_ptr) {

    auto& source = *(source_ptr.lock());

    // The source node already exists in the current scene. Returns it via
    // Nodes[] to de-constify it.
    if (nodes.has(source_ptr)) return nodes[source.id()];

    // clone the source node -- as a side effect, adds the newly created clone
    // to scene.nodes
    auto node_ptr = source.clone(); auto& node = *(node_ptr.lock());

    // have we previously mirrored this node?
    if (_mappings.count(source.id())) {
        // yes, reuse the original ID
        node._id = _mappings[source.id()];
    } else {
        // no, add this new mapping
        _mappings[source.id()] = node.id();
    }

    auto& parent = *(source.parent().lock());
    // do we already know about the parent? (ie, the parent has been mirrored)
    if (_mappings.count(parent.id())) {

        auto mirror_parent = nodes[_mappings[parent.id()]];

        // yes, re-parent to the mirrored parent
        node.set_parent(mirror_parent);
        // ...and tell the parent we are one of its children
        mirror_parent.lock()->append_child(node_ptr);

    } else {
        // no parent for now
        node.clear_parent();
    }


    // erase all the children (that are refering to nodes in the source world)
    node._children.clear();

    for(auto child_ptr : source.children()) {
        auto& child = *(child_ptr.lock());
        // do we already know about the child? (ie, the child has been mirrored)
        if (_mappings.count(child.id())) {
            auto mirror_child = nodes[_mappings[child.id()]];
            // yes, add the child to our children
            node.append_child(mirror_child);
            // ...and tell the child we are its parent
            mirror_child.lock()->set_parent(node_ptr);
        }
    }

    return node_ptr;
    // Note that at this point, the newly mirrored node is not yet sent to the server.
    // This will append at the next sync round.

}

void Scene::commit(ConstNodePtr node) {

    underworlds::NodeInContext request;
    request.mutable_context()->set_client(_ctxt._myself.id());
    request.mutable_context()->set_world(_world);

    auto gRPCNode = node.lock()->serialize();
    request.set_allocated_node(&gRPCNode);

    underworlds::Empty reply;

    grpc::ClientContext context;

    // The actual RPC.
    Status status = _ctxt._server->updateNode(&context, request, &reply);

    if (!status.ok()) {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }

}


void Scene::_add_node(shared_ptr<Node> node) {
    nodes._nodes[node->id()] = node;
}
