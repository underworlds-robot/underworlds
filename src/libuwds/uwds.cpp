#include <system_error>
#include <algorithm>

#include <boost/uuid/uuid_io.hpp>
#include <boost/uuid/uuid_generators.hpp>

#include <grpc++/grpc++.h>

#include "underworlds.grpc.pb.h"

#include "uwds.hpp"

using grpc::Channel;
using grpc::Status;

using namespace std;
using namespace uwds;

Node Node::deserialize(const underworlds::Node& remoteNode, shared_ptr<Scene> scene) {

    auto node = Node(scene);
    node.id = remoteNode.id();
    node.name = remoteNode.name();
    node.type = (NodeType) remoteNode.type();
    
    node.parent = scene->node(remoteNode.parent());

    for(int i = 0; i < remoteNode.children_size(); i++) {
        node.children.insert(scene->node(remoteNode.children(i)));

    }


    return node;
}

Node::Node(std::shared_ptr<Scene> scene) : id(boost::uuids::to_string(boost::uuids::random_generator()())),
                                     _scene(scene) {};

Node::Node(const Node& n) : id(boost::uuids::to_string(boost::uuids::random_generator()())),
                      name(n.name),
                      type(n.type),
                      parent(n.parent),
                      children(n.children),
                      transform(n.transform),
                      last_update(n.last_update),
                      _scene(n._scene) {}


Context::Context(const string& name, const string& address)
                   : _name(name),
                     _server(underworlds::Underworlds::NewStub(
                               grpc::CreateChannel(address,
                                                   grpc::InsecureChannelCredentials())
                                                 )
                             ),
                     worlds(*this) {
    helo(_name);
}

string Context::helo(const std::string& name) {

    underworlds::Name request;
    request.set_name(name);

    grpc::ClientContext context;

    // The actual RPC.
    Status status = _server->helo(&context, request, &_myself);

    // Act upon its status.
    if (status.ok()) {
        return _myself.id();
    } else {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }
}

chrono::duration<double> Context::uptime() {

    grpc::ClientContext context;
    underworlds::Time reply;

    Status status = _server->uptime(&context, _myself, &reply);

    if (status.ok()) {
        return chrono::duration<double>(reply.time());
    } else {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }
}

Topology Context::topology() {

    grpc::ClientContext context;
    underworlds::Topology reply;

    Status status = _server->topology(&context, _myself, &reply);

    if (!status.ok()) {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }
    
    Topology topo;
    for(size_t i = 0; i < reply.worlds_size(); i++) {
        topo.worlds.insert(reply.worlds(i));
    }

    for(size_t i = 0; i < reply.clients_size(); i++) {
        auto remoteClient = reply.clients(i);
        Client client;
        client.id = remoteClient.id();
        client.name = remoteClient.name();

        for(size_t j = 0; j < remoteClient.links_size(); j++) {
            auto remoteLink = remoteClient.links(j);
            Interaction link;
            link.world = remoteLink.world();
            link.type = (InteractionType) remoteLink.type();
            link.last_activity = chrono::system_clock::time_point(
                                            chrono::duration_cast<chrono::milliseconds>(
                                                chrono::duration<double>(
                                                    remoteLink.last_activity().time()
                                                    )
                                                )
                                            );

            client.links.push_back(link);
        }

        topo.clients.insert(client);
    }

    return topo;
}


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

        // node() has as a side effect to retrieve the node from the server and
        // to add it to _nodes if necessary.
        node(id);
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

shared_ptr<Node> Scene::node(const std::string& id) {


    for (const auto node : _nodes) {
        if (node->id == id) return node;
    }

    // -> the node does not exist locally: query the server
    
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


World::World(Context& ctxt, const std::string& name) : _ctxt(ctxt), 
                                                       _name(name),
                                                       scene(Scene(ctxt, name))
{
    

}

Worlds::Worlds(Context& ctxt): _ctxt(ctxt) {}

shared_ptr<World> Worlds::operator[](const string& name) {

    if (_worlds.count(name) == 0) {
        // create a new world (note that make_shared does not work here because
        // we are only 'friends' of World's private constructor)
        _worlds[name] = shared_ptr<World>(new World(_ctxt, name)); 
    }
    
    return _worlds[name];

}

std::ostream& operator<<(std::ostream& os, const uwds::Topology& topo)
{
    os << "worlds: " << std::endl;
    if (topo.worlds.size() > 0) {
        for (const auto& world : topo.worlds) os << " - " << world  << std::endl;
    } else {
        os << " none" << std::endl;
    }
    os << "clients: " << std::endl;
    for (const auto& client : topo.clients) {
        os << " - " << client.name << " [" << client.id << "]" << std::endl;
        if (client.links.size() > 0) {
            for (const auto& link : client.links) {
                os << "     - link with world <" << link.world << "> (" << uwds::InteractionTypeName[link.type] << ")" << std::endl;
            }
        }
    }

    return os;
}

std::ostream& operator<<(std::ostream& os, const uwds::Node& node)
{
    os << node.name << " [" << node.id << "]";
    return os;
}
