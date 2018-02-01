libunderworlds APIs
===================

Except otherwise noted, all units follow SI. In particular, length are in metres 
and angles in radians.

Node API
--------

node

 * <id> node.id
 * <string> node.name
 * <enum> type: type of the node
 * <node> node.parent
 * <node> node.entity: if the node belongs to a group  (like a complex object), 
   the node that represent this entity.
 * <matrix4x4f> node.transformation: transformation matrix, relative to parent
 * <dict<string, json string>> node.properties

Possible properties are defined in the `properties-registry`.

Currently defined node types:

 * MESH
 * ENTITY: an entity has no mesh directly attached to it. It represents a logical group of nodes
 * CAMERA

Scene API
---------

Low-level API
+++++++++++++

<node> gennode(): generate a new empty node, with its own unique ID.

add(node)
del(node)
update(node): node is an updated copy of an existing node. Only non-blank fields 
    are updated.

<id> pushmesh(<vec3f*> vertices, <vec3f*> normals, <vec3i*> faces): adds a 
    mesh to the meshes repository. Faces must be triangles.
delmesh(id): delete a mesh from the meshes repository.

High-level API
++++++++++++++

<node> get(name): returns a node by its name
<node*> get(<vec3f, vec3f> roi): returns all node whose bounding boxes are included in the ROI
<node*> getentity(name): returns all nodes belonging to the entity called 'name'.


