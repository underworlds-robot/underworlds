#ifndef NODE_HPP
#define NODE_HPP

#include <memory>
#include <string>
#include <array>
#include <set>
#include <iostream>

#include "underworlds.pb.h"

#include "base_types.hpp"


namespace uwds {

/* This macro conveniently lock and dereference a weak_ptr<Node>
 * 'Locking' a weak_ptr<Node> implies that the node will not be modified
 * by remote underworlds updates until the lock is released.
 *
 * Example:
 *  {
 *    auto& node = LOCK(scene.root());
 *    cout << node.name() << endl;
 *  }
 *
 * The lock is released when the reference leaves the scope.
 */
#define NODELOCK(N) (*(N.lock()))


enum NodeType {
    UNDEFINED = 0,
    ENTITY,
    MESH,
    CAMERA
};
static const std::array<std::string,4> NodeTypeName{"undefined", "entity", "mesh", "camera"};

struct Node;

typedef std::weak_ptr<Node> NodePtr;
typedef const std::weak_ptr<const Node> ConstNodePtr;

class Scene;

struct Node : public std::enable_shared_from_this<Node> {
    friend class Scene; // give Scene access to my constructor and Scene::mirror access to _id


private:
    /** Make the copy-constructor private
     *
     * Prevents the copy to another node, as it would break the invariant
     * that nodes are unique (unique ID)
     *
     * (we still need to privately copy in Node::clone, so th ecopy constructor is private
     * instead of simply deleted)
     */
    Node(const Node&) = default;

public:
    /** Moves are ok
     */
    Node(Node&&) = default;

    bool operator==(const Node& n) const {return n._id == _id;}
    
    // Creates a new node that is identical to this one, except for the ID
    NodePtr clone() const;
    underworlds::Node serialize() const;
    static Node deserialize(const underworlds::Node&, std::weak_ptr<Scene>);

    //////////////////////
    // ACCESSORS
    std::string id() const {return _id;}

    std::string name() const {return _name;}
    void set_name(const std::string& name) {_name=name;_update();}

    NodeType type() const {return _type;}
    void set_type(NodeType type) {_type=type;_update();}

    NodePtr parent();
    ConstNodePtr parent() const;

    /** Sets the given node to be my parent. Adds myself to the parent's children
     * (the given Node is modified).
     */
    void set_parent(NodePtr);
    void clear_parent();

    std::set<NodePtr> children();
    const std::set<std::weak_ptr<const Node>> children() const;
    /** Adds the given node to my children. Set myself as the parent of the
     * given node (the given Node is modified).
     */
    void append_child(NodePtr);
    void remove_child(NodePtr);

    const Transformation& transform() const {return _transform;}
    void set_transform(Transformation transform) {_transform=transform;_update();}

    std::chrono::system_clock::time_point last_update() const {return _last_update;}
    ///////////////////
    
private:

    Node(std::weak_ptr<Scene> scene);

    std::string _id;
    std::string _name;
    NodeType _type;
    std::string _parent;
    std::set<std::string> _children;
    Transformation _transform;
    std::chrono::system_clock::time_point _last_update;

    /** True if the node has been updated on the server, but not yet locally
     */
    bool _is_remotely_dirty;
    void _update();

    std::weak_ptr<Scene> _scene;
};

// needed to store weak_ptr<Node> in sets
// TODO: incorrect: lock() may return a null pointer if the underlying shared_ptr is gone
// but note that we *need* value comparison (for correct behaviour in
// ConcurrentSet::insert)
inline bool operator<(ConstNodePtr n1, ConstNodePtr n2) {return n1.lock()->id()
    < n2.lock()->id();}

inline bool operator==(ConstNodePtr n1, ConstNodePtr n2) {
    if (n1.expired() || n2.expired()) return false;
    // TODO: not entierly correct, as n1 or n2 may expire between those two lines
    return *(n1.lock()) == *(n2.lock());
}

}

std::ostream& operator<<(std::ostream& os, const uwds::Node& node);
std::ostream& operator<<(std::ostream& os, const std::weak_ptr<const uwds::Node> node);

#endif


