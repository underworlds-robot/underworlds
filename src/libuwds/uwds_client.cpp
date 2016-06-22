#include <iostream>
#include <memory>
#include <string>

#include <grpc++/grpc++.h>

#include "underworlds.grpc.pb.h"

using grpc::Channel;
using grpc::Status;

using namespace underworlds;

class UnderworldsClient {
 public:
  UnderworldsClient(std::shared_ptr<Channel> channel)
                   : stub_(Underworlds::NewStub(channel)) {}

  std::string helo(const std::string& name) {

    Name request;
    request.set_name(name);

    Client reply;

    grpc::ClientContext context;

    // The actual RPC.
    Status status = stub_->helo(&context, request, &reply);

    // Act upon its status.
    if (status.ok()) {
      return reply.id();
    } else {
      return "RPC failed";
    }
  }

 private:
  std::unique_ptr<Underworlds::Stub> stub_;
};

int main(int argc, char** argv) {

  UnderworldsClient uwds(grpc::CreateChannel("localhost:50051", 
                                             grpc::InsecureChannelCredentials()));
  std::string name("cpp client");
  std::string reply = uwds.helo(name);
  std::cout << "uwds received: " << reply << std::endl;

  return 0;
}
