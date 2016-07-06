#include <stdexcept>
#include <system_error>

#include <boost/range/adaptor/map.hpp>

#include <grpc++/grpc++.h>

#include "underworlds.grpc.pb.h"


#include "uwds.hpp"

using grpc::Channel;
using grpc::Status;


using namespace std;
using namespace uwds;

Nodes::Nodes(Context& ctxt):_ctxt(ctxt) {}

const Node& Nodes::operator[](const string& id) const {

    if (!has(id)) {
        auto node = _fetch(id); // side-effect: adds the node to _nodes
        if (!node) throw out_of_range("No such node " + id);
    }
    
    return at(id);

}

Node& Nodes::operator[](const string& id) {

    // cast away the const qualifiers -- see http://stackoverflow.com/questions/856542/elegant-solution-to-duplicate-const-and-non-const-getters
    return const_cast<Node&>(static_cast<const Nodes*>(this)->operator[](id));
}


set<reference_wrapper<Node>> Nodes::from_name(const string& name) {

    set<reference_wrapper<Node>> result;

    for (const auto& kv : _nodes) {
        if (kv.second->name() == name) result.insert(*kv.second);
    }

    return result;
}

const shared_ptr<const Node> Nodes::_fetch(const string& id) const {

    cout << "Fetching node " << id << endl;
    underworlds::NodeInContext request;
    request.mutable_context()->set_client(_ctxt._myself.id());
    request.mutable_context()->set_world(_scene.lock()->_world);
    request.mutable_node()->set_id(id);

    underworlds::Node reply;

    grpc::ClientContext context;

    // The actual RPC.
    Status status = _ctxt._server->getNode(&context, request, &reply);

    // Act upon its status.
    if (status.ok()) {

        auto node = make_shared<Node>(Node::deserialize(reply, _scene));
        _nodes[node->id()] = node;
        return node;

    } else {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }

}

shared_ptr<Node> Nodes::_fetch(const string& id) {

    cout << "Fetching node " << id << endl;
    underworlds::NodeInContext request;
    request.mutable_context()->set_client(_ctxt._myself.id());
    request.mutable_context()->set_world(_scene.lock()->_world);
    request.mutable_node()->set_id(id);

    underworlds::Node reply;

    grpc::ClientContext context;

    // The actual RPC.
    Status status = _ctxt._server->getNode(&context, request, &reply);

    // Act upon its status.
    if (status.ok()) {

        auto node = make_shared<Node>(Node::deserialize(reply, _scene));
        _nodes[node->id()] = node;
        return node;

    } else {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }

}
