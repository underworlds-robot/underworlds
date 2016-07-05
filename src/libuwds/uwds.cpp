#include <system_error>
#include <algorithm>

#include <grpc++/grpc++.h>

#include "underworlds.grpc.pb.h"

#include "uwds.hpp"

using grpc::Channel;
using grpc::Status;

using namespace std;
using namespace uwds;

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

void Context::reset() {

    grpc::ClientContext context;
    underworlds::Empty reply;

    Status status = _server->reset(&context, _myself, &reply);

    if (!status.ok()) {
        throw system_error(error_code(status.error_code(),generic_category()), status.error_message());
    }
}

World::World(Context& ctxt, const std::string& name) : _ctxt(ctxt), 
                                                       _name(name),
                                                       scene(Scene(ctxt, name))
{
    

}

Worlds::Worlds(Context& ctxt): _ctxt(ctxt) {}

World& Worlds::operator[](const string& name) {

    if (_worlds.count(name) == 0) {
        // create a new world (note that make_shared does not work here because
        // we are only 'friends' of World's private constructor)
        _worlds[name] = shared_ptr<World>(new World(_ctxt, name)); 
    }
    
    return *_worlds.at(name);

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

