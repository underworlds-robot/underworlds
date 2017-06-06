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

class Node(object):
    def __init__(self, name = "", type = UNDEFINED):

        ################################################################
        ##                     START OF THE API                       ##
        ################################################################
        self.id = str(uuid.uuid4())
        self.name = name
        self.type = type #one of the node constant defined in types.py
        self.parent = None # the parent node id
        #TODO: make children read-only with @property
        self.children = [] # the children nodes id. READ-ONLY
        

        # 4x4 transformation matrix, relative to parent. Stored as a numpy 4x4
        # matrix. Translation units are meters.
        self.transformation = numpy.identity(4, dtype=numpy.float32)

        self.last_update = time.time()

        self.lowres = []
        self.hires = []
        self.cad = []
        self.aabb = []

        self.properties = {
                "physics": False # no physics applied by default
            }

        self.clipplanenear = 0
        self.clipplanefar = 0
        self.aspect = 0
        self.horizontalfov = 0

        ################################################################
        ##                     END OF THE API                         ##
        ################################################################

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

    def copy(self):
        """ Performs a deep-copy of myself, and return the copy.
        The copy *has a new, different, unique ID* (ie, the ID is not copied).
        """

        import copy
        node = copy.deepcopy(self)
        node.id = str(uuid.uuid4())

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
        node.type = self.type
        node.parent = self.parent if self.parent is not None else ""

        for c in self.children:
            node.children.append(c)

        for v in self.transformation.flatten().tolist():
            node.transformation.append(v)

        node.last_update = self.last_update


        for m in self.lowres: node.lowres.append(m)
        for m in self.hires: node.hires.append(m)
        for m in self.cad: node.cad.append(m)

        for p in self.aabb:
            point = node.aabb.add()
            point.x, point.y, point.z = p

        node.physics = self.properties["physics"]

        node.clipplanenear = self.clipplanenear
        node.clipplanefar =  self.clipplanefar
        node.aspect =        self.aspect
        node.horizontalfov = self.horizontalfov

        return node

    @staticmethod
    def deserialize(data):
        """Creates a node from a protobuf encoding.
        """
        node = Node()

        node.id = data.id
        node.name = data.name
        node.type = data.type
        node.parent = data.parent if data.parent else None # convert empty string to None if needed

        for c in data.children:
            node.children.append(c)

        node.transformation = [v for v in data.transformation]

        # Convert the transformation into a proper numpy array.
        # The type (float32) ensures OpenGL compatibilty on 64bit platforms
        node.transformation = numpy.array(node.transformation, dtype=numpy.float32).reshape(4,4)

        node.last_update = data.last_update


        node.lowres = [m for m in data.lowres]
        node.hires = [m for m in data.hires]
        node.cad = [m for m in data.cad]

        node.aabb = [(p.x,p.y,p.z) for p in data.aabb]
        if node.aabb and len(node.aabb) != 2:
            raise RuntimeError("Received a node with an invalid bounding-box!")

        node.properties["physics"] = data.physics

        node.clipplanenear = data.clipplanenear
        node.clipplanefar =  data.clipplanefar
        node.aspect =        data.aspect
        node.horizontalfov = data.horizontalfov

        return node

class Mesh(object):

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

        mesh = Mesh(vertices=[(p.x,p.y,p.z) for p in data.vertices],
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

        self.rootnode = Node("root", ENTITY)
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

        self.situations = []

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


    def start(self, situation):
        """ Asserts a situation has started to exist.

        Note that in the special case of events, the situation ends
        immediately.
        """
        situation.starttime = time.time()
        self.situations.append(situation)

    def end(self, situation):
        """ Asserts the end of a situation.

        Note that in the special case of events, this method a no effect.
        """
        situation.endtime = time.time()

    def event(self, event):
        """ Asserts a new event occured in this timeline
        at time 'time.time()'.
        """
        self.start(event)
        event.endtime = event.starttime

    def situation(self, id):
        for sit in self.situations:
            if sit.id == id:
                return sit


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

        # Start|Endtime are in seconds (float)
        self.starttime = 0 # convention for situations that are not yet started
        self.endtime = 0 # convention for situations that are not terminated

    def isevent(self):
        return self.endtime == self.starttime

    def __repr__(self):
        return self.id + " (" + self.type + ")"

    def __str__(self):
        if self.desc:
            return self.desc
        else:
            return self.type

    def __cmp__(self, sit):
        # TODO: check here other values equality, and raise exception if any differ? may be costly, though...
         return cmp(self.id, sit.id)

    def __hash__(self):
        return hash(self.id)

    def serialize(self, SituationType):
        """Outputs a protobuf encoding of the situation

        The SituationType (underworlds_pb2.Node) needs to be passed as parameter
        to prevent the creation of a 2nd instance of the underworlds_pb2 that
        crashes the gRPC. Not sure why...
        Similar to http://stackoverflow.com/questions/32010905/unbound-method-must-be-called-with-x-instance-as-first-argument-got-x-instance
        """
        sit = gRPC.Situation()

        sit.id = self.id
        sit.type = self.type
        sit.description = self.desc
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
        sit.starttime = data.start.time
        sit.endtime = data.end.time

        return sit


def createevent():
    """ An event is a (immediate) change of the world. It has no
    duration, contrary to a StaticSituation that has a non-null duration.

    This function creates and returns such a instantaneous situation.

    :sees: situations.py for a set of standard events types
    """


    sit = Situation(type = GENERIC, pattern = None)

    return sit

