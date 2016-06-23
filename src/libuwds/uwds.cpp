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
                             ) {
    helo(_name);
}

string Context::helo(const std::string& name) {

    underworlds::Name request;
    request.set_name(name);

    underworlds::Client reply;

    grpc::ClientContext context;

    // The actual RPC.
    Status status = _server->helo(&context, request, &_myself);

    // Act upon its status.
    if (status.ok()) {
        return reply.id();
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


