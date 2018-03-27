import uuid
import copy
import json
import time

import logging
logger = logging.getLogger("underworlds.core")

import numpy

import underworlds.underworlds_pb2 as gRPC

from underworlds.errors import *

# Clients types
READER = gRPC.ClientInteraction.READER
PROVIDER = gRPC.ClientInteraction.PROVIDER
MONITOR = gRPC.ClientInteraction.MONITOR
FILTER = gRPC.ClientInteraction.FILTER

CLIENTTYPE_NAMES = {READER:'reader',
                    PROVIDER:'provider',
                    MONITOR:'monitor',
                    FILTER:'filter'
                   }

# Node types
UNDEFINED = gRPC.Node.UNDEFINED
# Entities are abstract nodes. They can represent non-physical objects (like a
# reference frame) or groups of other objects.
ENTITY = gRPC.Node.ENTITY
MESH = gRPC.Node.MESH
CAMERA = gRPC.Node.CAMERA

NODETYPE_NAMES = {UNDEFINED:'undefined',
                  ENTITY:'entity',
                  MESH:'mesh',
                  CAMERA:'camera'
                 }
# Situation types
GENERIC = gRPC.Situation.GENERIC
MOTION = gRPC.Situation.MOTION
EVT_MODELLOAD = gRPC.Situation.EVT_MODELLOAD

SITUATIONTYPE_NAMES = {GENERIC: "generic situation",
                       MOTION: "motion",
                       EVT_MODELLOAD: "model loading"
                      }

# Invalidation types
NEW = gRPC.Invalidation.NEW
UPDATE = gRPC.Invalidation.UPDATE
DELETE = gRPC.Invalidation.DELETE

INVALIDATIONTYPE_NAMES = {NEW: "new",
                          UPDATE: "update",
                          DELETE: "delete"
                         }

class Node(object):
    def __init__(self, name = "", type = UNDEFINED):

        if type == UNDEFINED:
            logger.warning("Node is an abstract class. Instantiate "
                           "instead one of its concrete subclass like"
                           " Mesh or Camera")

        ################################################################
        ##                     START OF THE API                       ##
        ################################################################
        self.id = str(uuid.uuid4())
        self.name = name
        self._type = type #one of the node constant defined in types.py -- THIS IS READ-ONLY
        self.parent = None # the parent node id

        self._children = [] # the children nodes id. READ-ONLY
        

        # 4x4 transformation matrix, relative to parent. Stored as a numpy 4x4
        # matrix. Translation units are meters.
        self.transformation = numpy.identity(4, dtype=numpy.float32)

        self.last_update = time.time()

        # empty property list for the abstract Node class. Concrete subclasses
        # might define their own required properties
        self.properties = {}

        ################################################################
        ##                     END OF THE API                         ##
        ################################################################

    # getters for read-only properties
    @property
    def children(self):
        return self._children
    @property
    def type(self):
        return self._type


    def __repr__(self):
        return self.id + (" (" + self.name + ")" if self.name else "")
    
    
    def __str__(self):
        return self.name if self.name else self.id + " (" + NODETYPE_NAMES[self.type] + ")"

    def __lt__(self, node):
        return self.id < node.id

    def __eq__(self, node):
        return hasattr(node, "id") and self.id == node.id

    def __hash__(self):
        return hash(self.id)

    def translate(self, vector):
        """ Translates the node by a vector. The change is not propagated
        automatically (you must call nodes.update(...)).
        """
        self.transformation[0,3] = vector[0]
        self.transformation[1,3] = vector[1]
        self.transformation[2,3] = vector[2]

    def translation(self):
        """

        :returns: a numpy vector (x, y, z) representing the current translation of the node wrt to its parent.
        """
        return self.transformation[0:3,3]

    def copy(self):
        """ Performs a deep-copy of myself, and return the copy.
        The copy *has a new, different, unique ID* (ie, the ID & children are not copied).
        """

        import copy
        node = copy.deepcopy(self)
        node.id = str(uuid.uuid4())
        node._children = [] # clean children when copying to let uwds fill it

        return node

    def serialize(self, NodeType):
        """Outputs a protobuf encoding of the node

        The NodeType (underworlds_pb2.Node) needs to be passed as parameter
        to prevent the creation of a 2nd instance of the underworlds_pb2 that
        crashes the gRPC. Not sure why...
        Similar to http://stackoverflow.com/questions/32010905/unbound-method-must-be-called-with-x-instance-as-first-argument-got-x-instance
        """


        node = NodeType()
        node.id = self.id
        node.name = self.name
        node.type = self._type
        node.parent = self.parent if self.parent is not None else ""

        for c in self.children:
            node.children.append(c)

        for v in self.transformation.flatten().tolist():
            node.transformation.append(v)

        node.last_update = self.last_update

        for k, v in self.properties.items():
            if v is None:
                raise UnderworldsError("Property %s is required but not set (and has no default value)" % k)
            
            node.properties[k] = json.dumps(v)


        return node

    @staticmethod
    def deserialize(data):
        """Creates a node from a protobuf encoding.
        """

        if data.type == UNDEFINED:
            node = Node()
        elif data.type == ENTITY:
            node = Entity()
        elif data.type == MESH:
            node = Mesh()
        elif data.type == CAMERA:
            node = Camera()
        else:
            raise UnderworldsError("Unknown node type %s while deserializing a gRPC node" % data.type)

        node.id = data.id
        node.name = data.name
        node.parent = data.parent if data.parent else None # convert empty string to None if needed

        for c in data.children:
            node._children.append(c)

        node.transformation = [v for v in data.transformation]

        # Convert the transformation into a proper numpy array.
        # The type (float32) ensures OpenGL compatibilty on 64bit platforms
        node.transformation = numpy.array(node.transformation, dtype=numpy.float32).reshape(4,4)

        node.last_update = data.last_update

        for k, v in data.properties.items():
            node.properties[k] = json.loads(v)

        return node

class Entity(Node):

    def __init__(self, name = ""):
        super(Entity, self).__init__(name, ENTITY)

        # TODO: generate that list automatically from properties-registry.rst
        self.properties = {}

class Mesh(Node):

    def __init__(self, name = ""):
        super(Mesh, self).__init__(name, MESH)

        # TODO: generate that list automatically from properties-registry.rst
        self.properties = {
                "mesh_ids": None,
                "physics": False # no physics applied by default
            }

class Camera(Node):

    def __init__(self, name = ""):
        super(Camera, self).__init__(name, CAMERA)

        # TODO: generate that list automatically from properties-registry.rst
        self.properties = {
                "aspect": None,
                "horizontalfov": None,
            }

class MeshData(object):

    def __init__(self, vertices, faces, normals, diffuse=(1,1,1,1)):

        self.id = ""
        self.vertices = vertices
        self.faces = faces
        self.normals = normals
        self.diffuse = tuple(diffuse) # diffuse color, white by default
        if len(self.diffuse) == 3: self.diffuse += (1,)

        self.id = str(hash(str(self.serialize(gRPC.Mesh))))

    def __hash__(self):
        m = (self.vertices, \
             self.faces, \
             self.normals, \
             self.diffuse)
        return hash(str(m))

    def serialize(self, MeshType):
        """Outputs a protobuf encoding of the mesh

        The MeshType (underworlds_pb2.Mesh) needs to be passed as parameter
        to prevent the creation of a 2nd instance of the underworlds_pb2 that
        crashes the gRPC. Not sure why...
        Similar to http://stackoverflow.com/questions/32010905/unbound-method-must-be-called-with-x-instance-as-first-argument-got-x-instance
        """
        starttime = time.time()

        mesh = MeshType()
        mesh.id = self.id

        for vertex in self.vertices:
            point = mesh.vertices.add()
            point.x, point.y, point.z = vertex

        for f in self.faces:
            face = mesh.faces.add()
            face.x, face.y, face.z = f

        for normal in self.normals:
            point = mesh.normals.add()
            point.x, point.y, point.z = normal

        mesh.diffuse.r, mesh.diffuse.g, mesh.diffuse.b, mesh.diffuse.a = self.diffuse

        logger.info("Serialized mesh %s in %.2fsec" % (self.id, time.time()-starttime))
        return mesh


    @staticmethod
    def deserialize(data):
        """Creates a Python mesh object from a protobuf encoding.
        """

        mesh = MeshData(vertices=[(p.x,p.y,p.z) for p in data.vertices],
                    faces = [(f.x,f.y,f.z) for f in data.faces],
                    normals = [(n.x,n.y,n.z) for n in data.normals],
                    diffuse = (data.diffuse.r, data.diffuse.g, data.diffuse.b, data.diffuse.a))

        #if mesh.id != data.id:
        #    raise RuntimeError("Can not verify mesh integrity!")

        return mesh

class Scene(object):
    """An Underworlds scene
    """

    def __init__(self):

        self.rootnode = Entity("root")
        self.rootnode.transformation = numpy.identity(4, dtype=numpy.float32)

        self.nodes = []

        self.nodes.append(self.rootnode)

    def list_entities(self):
        """ Returns the list of entities contained in the scene.
        """
        raise NotImplementedError

    def node(self, id):
        """ Returns a node from its ID (or None if the node does not exist)
        """
        for n in self.nodes:
            if n.id == id:
                return n

    def nodebyname(self, name):
        """ Returns a list of node that have the given name (or [] if no node has this name)
        """
        nodes = []
        for n in self.nodes:
            if n.name == name:
                nodes.append(n)
        return nodes

class Timeline(object):
    """ Stores 'situations' (ie, either events -- temporal objects
    without duration -- or static situations -- temporal objects
    with a non-null duration).

    A timeline also exposes an API to find for temporal patterns.

    TODO: situations are currently stored as a flat array, which
    is certainly not the most efficient way!
    """

    def __init__(self):

        self.origin = time.time()

        self.situations = {}

    def on(self, event):
        """
        Creates a new EventMonitor to watch a given event model.

        Typical use is:
        
        >>> t = Timeline()
        >>> e = Event(...)
        >>>
        >>> def onevt(evt):
        >>>    print(evt)
        >>>
        >>> t.on(e).call(onevt)

        :returns: a new instance of EventMonitor for this event.
        """
        return EventMonitor(event)


    def start(self):
        """ Asserts a situation has started.

        Note that in the special case of events, the situation ends
        immediately.

        :returns: The newly created situation
        """
        situation = Situation()
        situation.starttime = time.time()
        self.situations[situation.id] = situation
        return situation

    def end(self, situation):
        """ Asserts the end of a situation.

        Note that in the special case of events, this method a no effect.
        """
        if situation.isevent():
            return situation
        self.situations[situation.id].endtime = time.time()
        return self.situations[situation.id]

    def event(self):
        """ Asserts a new event occured in this timeline.

        :returns: the newly created event.
        """
        event = self.start()
        event.endtime = event.starttime
        return event

    def append(self, situation):
        """ Adds the given situation to the timeline.

        If a situation with the same ID already exists, it replaces it.

        :returns: True if the situation has been added, False if it has simply updated an existing situation
        """
        return not self.update(situation)

    def update(self, situation):
        """ Update (ie, replace) an existing situation with the
        given one.
        
        If the situations does not exist, simply add it to the timeline.

        :returns: True if the situation has been updated, False if it has been simply added (new situation)
        """
        isnew = situation.id in self.situations
        self.situations[situation.id] = situation
        return not isnew

    def remove(self, situation):
        """ Deletes an existing situation.
        """
        del self.situations[situation.id]

    def situation(self, id):
        if id in self.situations:
            return self.situations[id]
        else:
            return None


class EventMonitor(object):

    def __init__(self, evt):
        self.evt = evt

    def call(self, cb):
        self.cb = cb

    def make_call(self):
        self.cb(self.evt)

    def wait(self, timeout = 0):
        """ Blocks until an event occurs, or the timeout expires.
        """
        raise NotImplementedError

class World(object):

    def __init__(self, name):

        self.name = name
        self.scene = Scene()
        self.timeline = Timeline()

    def __repr__(self):
        return "world " + self.name

    def deepcopy(self, world):
        self.scene = copy.copy(world.scene)
        self.timeline = copy.copy(world.timeline)


class Situation(object):
    """ A situation represents a generic temporal object.

    It has two subclasses:
     - events, which are instantaneous situations (null duration)
     - static situations, that have a duration.

     """

    def __init__(self, desc="", type = GENERIC):

        self.id = str(uuid.uuid4())
        self.type = type
        self.desc = desc

        self.last_update = time.time()

        # Start|Endtime are in seconds (float)
        self.starttime = 0 # convention for situations that are not yet started
        self.endtime = 0 # convention for situations that are not terminated

    def isevent(self):
        return self.endtime == self.starttime

    def __repr__(self):
        return self.id + " (" + SITUATIONTYPE_NAMES[self.type] + ")"

    def __str__(self):
        if self.desc:
            return "Situation %s -- %s: %s" % (self.id, SITUATIONTYPE_NAMES[self.type], self.desc)
        else:
            return "Situation %s -- %s" % (self.id, SITUATIONTYPE_NAMES[self.type])

    def __cmp__(self, sit):
        # TODO: check here other values equality, and raise exception if any differ? may be costly, though...
         return cmp(self.id, sit.id)

    def __hash__(self):
        return hash(self.id)

    def copy(self):
        """ Performs a deep-copy of myself, and return the copy.
        The copy *has a new, different, unique ID* (ie, the ID & children are not copied).
        """

        import copy
        situation = copy.deepcopy(self)
        situation.id = str(uuid.uuid4())

        return situation

    def serialize(self, SituationType):
        """Outputs a protobuf encoding of the situation

        The SituationType (underworlds_pb2.Situation) needs to be passed as parameter
        to prevent the creation of a 2nd instance of the underworlds_pb2 that
        crashes the gRPC. Not sure why...
        Similar to http://stackoverflow.com/questions/32010905/unbound-method-must-be-called-with-x-instance-as-first-argument-got-x-instance
        """
        sit = gRPC.Situation()

        sit.id = self.id
        sit.type = self.type
        sit.description = self.desc
        sit.last_update = self.last_update
        sit.start.time = self.starttime
        sit.end.time = self.endtime


        return sit


    @staticmethod
    def deserialize(data):
        """Creates a situation from a protobuf encoding.
        """
        sit = Situation()

        sit.id = data.id
        sit.type = data.type
        sit.desc = data.description
        sit.last_update = data.last_update
        sit.starttime = data.start.time
        sit.endtime = data.end.time

        return sit


