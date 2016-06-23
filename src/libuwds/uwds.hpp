#include <iostream>
#include <memory>
#include <string>
#ifndef UWDS_HPP
#define UWDS_HPP

#include <memory>
#include <string>
#include <chrono>

#include "underworlds.grpc.pb.h"

namespace uwds {

class Context {

public:
        Context(const std::string& name, const std::string& address="localhost:50051");

        std::string name() const {return _name;}
        std::string id() const {return _myself.id();}

        std::chrono::duration<double> uptime();

private:
        std::string helo(const std::string& name);

        std::string _name;
        std::string _id;
        std::unique_ptr<underworlds::Underworlds::Stub> _server;
        underworlds::Client _myself;
};

}

#endif


