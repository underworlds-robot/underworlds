#ifndef BASE_TYPE_HPP
#define BASE_TYPE_HPP

#include<string>
#include<array>
#include<chrono>
#include<vector>
#include<set>

#include <opencv2/core/core.hpp> // for transformation matrices

namespace uwds {

/////////////////////////////////////////////////////////////////////////
///////////  GENERAL TYPES

typedef cv::Matx44d Transformation;

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

}

#endif
