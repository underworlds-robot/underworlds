#ifndef UWDS_HPP
#define UWDS_HPP

#include <memory>
#include <string>
#include <chrono>
#include <set>
#include <vector>
#include <array>
#include <iostream>

#include "underworlds.grpc.pb.h"

namespace uwds {

enum InteractionType {
    READER = 0,
    PROVIDER,
    MONITOR,
    FILTER
};
static const std::array<std::string,4> InteractionTypeName{"reader", "provider", "monitor", "filter"};

struct Interaction {
    std::string world;
    InteractionType type;
    std::chrono::system_clock::time_point last_activity;
};

struct Client {
    std::string id;
    std::string name;
    std::vector<Interaction> links;

    bool operator<(Client other) const
    {
        return id > other.id;
    }
};

struct Topology {
    std::set<std::string> worlds;
    std::set<Client> clients;

};

class Context {

public:
        Context(const std::string& name, const std::string& address="localhost:50051");

        std::string name() const {return _name;}
        std::string id() const {return _myself.id();}

        std::chrono::duration<double> uptime();
        Topology topology();

private:
        std::string helo(const std::string& name);

        std::string _name;
        std::string _id;
        std::unique_ptr<underworlds::Underworlds::Stub> _server;
        underworlds::Client _myself;
};

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
#endif


