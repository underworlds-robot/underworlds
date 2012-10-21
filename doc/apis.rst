libunderworlds APIs
===================

Except otherwise noted, all units follow SI. In particular, length are in meters and angles in radians.

Node API
--------

node

 * <id> node.id
 * <string> node.name
 * <node> node.parent
 * <node> node.entity: if the node belongs to a group  (like a complex object), the node that represent this entity.
 * <matrix4x4f> node.transformation: transformation matrix, relative to parent
 * <dict<string, ?>> node.properties

Base set of properties (these properties are guaranteed to exist):

 * <string> type: type of the node

Currently existing types:

 * MESH
 * ENTITY: an entity has no mesh directly attached to it. It represents a logical group of nodes
 * CAMERA

Type specific properties:
 * MESH
   * <vec3f, vec3f> aabb: axis-aligned bounding box
   * <vec3f, vec3f, vec3f, vec3f> bb: bounding box
   * <id> cad: if available, the mesh ID of a CAD model associated to the node
   * <id> highres: a high resolution mesh representing the node
   * <id> lowres: a low resolution mesh representing the node
   * <id> collision: a mesh suited for collision detection
   * [?] <id*> meshes: a list of mesh IDs
   * <float> mass
   * <vec3f> centerofmass: if defined, in the node frame. By default, the node origin.
   * <vec3f> lookat: if defined, the direction vector of the object. Meaningful only for objects that have a well identified face.

 * ENTITY
   * <vec3f, vec3f> aabb: axis-aligned bounding box of the whole entity
   * <vec3f, vec3f, vec3f, vec3f> bb: bounding box of the whole entity
 
 * CAMERA
   * <vec3f> lookat: the camera direction vector (ie, a 3D point in the camera frame, that is looked at by the camera)
   * [TDB] camera frustrum and other features 

Scene API
---------

Low-level API
+++++++++++++

<node> gennode(): generate a new empty node, with its own unique ID.

add(node)
del(node)
update(node): node is an updated copy of an existing node. Only non-blank fields are updated.

<id> pushmesh(<vec3f*> vertices, <vec3f*> normals, <vec3i*> faces): adds a mesh to the meshes repository. Faces must be triangles.
delmesh(id): delete a mesh from the meshes repository.

High-level API
++++++++++++++

<node> get(name): returns a node by its name
<node*> get(<vec3f, vec3f> roi): returns all node whose bounding boxes are included in the ROI
<node*> getentity(name): returns all nodes belonging to the entity called 'name'.



Monitors
--------

Monitors are processes that are attached to a specific world. They monitor the geometric scene, and produce events added to the world's timeline.

Examples include:
* visibility_monitor: signal when a given entity or node is visible from a given camera
* touch_monitor: signal when two entities touch each other
* motion_monitor: signal when an entity is moving
* collision_monitor: signal when two entities are colliding [or about to collide?] 

Filters
-------

