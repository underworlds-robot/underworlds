import uuid
import copy
import json
import time

from underworlds.errors import *
from underworlds.situations import *

# Clients types
READER = "READER"
PROVIDER = "PROVIDER"
MONITOR = "MONITOR"
FILTER = "FILTER"


# Node types
UNDEFINED = 0
MESH = 1
# Entities are group of nodes. They are either rigid bodies (ie, no
# joints, and hence only one node) or complex bodies (ie, with a
# kinematic chain and hence several nodes, one per joint).
ENTITY = 2
CAMERA = 3

class Node():
    def __init__(self, name = "", type = UNDEFINED):

        ################################################################
        ##                     START OF THE API                       ##
        ################################################################
        self.id = str(uuid.uuid4())
        self.name = name
        self.type = type #one of the node constant defined in types.py
        self.parent = None
        self.children = []
        self.transformation = None # 4x4 transformation matrix, relative to parent. Stored as a list of lists.
        self.properties = {
                "physics": False # no physics applied by default
            }
        self.last_update = time.time()
        ################################################################
        ##                     END OF THE API                         ##
        ################################################################

    def __repr__(self):
        return self.id + (" (" + self.name + ")" if self.name else "")
    
    
    def __str__(self):
        type = ["undefined", "mesh", "entity", "camera"][self.type]
        return self.name if self.name else self.id + " (" + type + ")"

    def __cmp__(self, node):
        # TODO: check here other values equality, and raise exception if any differ? may be costly, though...
         return cmp(self.id, node.id)

    def __hash__(self):
        return hash(self.id)

    def serialize(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def deserialize(serialized):
        n = Node()
        data = json.loads(serialized)

        for key, value in data.items():
            setattr(n, str(key), value)
        #n.__dict__ = data
        return n



class Scene():
    """An Underworlds scene
    """

    def __init__(self):

        self.rootnode = Node("root", ENTITY)

        self.nodes = []

        self.nodes.append(self.rootnode)

    def list_entities(self):
        """ Returns the list of entities contained in the scene.
        """
        raise NotImplementedError

    def node(self, id):
        for n in self.nodes:
            if n.id == id:
                return n

class Timeline:
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


class EventMonitor:

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

class World:

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

    :sees: situations.py for a set of standard situation types
     """

    # Default owner
    DEFAULT_OWNER = "SYSTEM"

    def __init__(self, desc="", type = GENERIC, owner = DEFAULT_OWNER):

        self.id = str(uuid.uuid4())
        self.type = type
        self.owner = owner
        self.desc = desc

        # Start|Endtime are in seconds (float)
        self.starttime = None # convention for situations that are not yet started
        self.endtime = None # convention for situations that are not terminated

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

    def serialize(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def deserialize(serialized):
        sit = Situation()
        data = json.loads(serialized)

        for key, value in data.items():
            setattr(sit, str(key), value)

        return sit


def createevent():
    """ An event is a (immediate) change of the world. It has no
    duration, contrary to a StaticSituation that has a non-null duration.

    This function creates and returns such a instantaneous situation.

    :sees: situations.py for a set of standard events types
    """


    sit = Situation(type = GENERIC, owner = Situation.DEFAULT_OWNER, pattern = None)

    return sit

