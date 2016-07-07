#ifndef SCENE_HPP
#define SCENE_HPP

//#include <memory>
//#include <thread>
//#include <iterator>
//#include <string>
//#include <chrono>
//#include <set>
//#include <vector>
//#include <array>
//#include <iostream>

#include "underworlds.grpc.pb.h"

#include "base_types.hpp"
#include "node.hpp"
#include "nodes.hpp"


namespace uwds {

class Nodes;
class World;

class Scene : public std::enable_shared_from_this<Scene> {
    friend class World; // give World access to our private constructor
    friend class Nodes; // give Nodes access to _world

public:

    // no copies! move only
    Scene(const Scene&) = delete;
    Scene(Scene&&) = default;

    NodePtr root() const {return _root;}
    Nodes nodes;

    /** Creates a new, empty node, adds it to the scene, and returns it.
     */
    NodePtr new_node();

    /** Mirrors a node coming from a different scene to the current scene.
     *
     * If the source node already exists in the current scene, returns it
     * immediately (the node is not modified).
     *
     * Otherwise, a copy of the source node is created in the current scene
     * (mirrored node).
     *
     * The mirrored node is not an exact copy:
     *  - the mirrored node has its own unique ID 
     *  - the parent and children of the node are the mirrors of the
     *    source parent/children in the current scene.
     *
     * If the parent/children have not been mirrored in the current scene, they
     * are left out of the mirrored node (the parenting is however restored if
     * the source parent/children are mirrored at a later stage).
     *
     * The mapping between the source node and the mirrored node is saved: if
     * Scene::mirror is called again with the same source node, the previously
     * mirrored node will be updated instead of newly created.
     */
    NodePtr mirror(ConstNodePtr source);


    /** Commits the changes operated on a node to the underworlds server.
     *
     * If the node has never been committed before, the node is created on the server.
     *
     * The changes performed on the node are only visible to the other
     * underworlds clients after Scene::commit has been called (note that
     * the propagation to all the client may take up to 100ms, depending on the
     * network)
     */
    //void commit(ConstNodePtr node);

private:
    // only class World (friend) can create a new world
    // Scene::initialize should be call immediately
    // after Scene is constructed.
    Scene(Context& ctxt);
    void initialize(const std::string& world);

    Context& _ctxt;
    std::string _world;

    NodePtr _root;

    /** Holds the node ID mappings needed by Scene::mirror
     */
    std::map<std::string, std::string> _mappings;

};

}

#endif


