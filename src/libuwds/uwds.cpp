#include <system_error>

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

