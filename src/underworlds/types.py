import uuid
import copy
import json
import time

from underworlds.errors import *

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
        self.entity = None #if the node belongs to a group  (like a complex object), the node that represent this entity.
        self.transformation = None # 4x4 transformation matrix, relative to parent. Stored as a list of lists.
        self.properties = {}
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

    def __init__(self):

        self.activesituations = []

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
        raise NotImplementedError

    def end(self, situation):
        """ Asserts the end of a situation.

        Note that in the special case of events, this method a no effect.
        """
        raise NotImplementedError

    def event(self, event):
        """ Asserts a new event occured in this timeline
        at time 'time.time()'.
        """
        self.start(event)

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


class Situation(object):
    """ A situation represents a generic temporal object.
    
    It has two subclasses:
     - events, which are instantaneous situations (null duration)
     - static situations, that have a duration.
     """

    # Some situation types
    GENERIC = "generic"

    # Default owner
    DEFAULT_OWNER = "SYSTEM"

    def __init__(self, type = GENERIC, owner = DEFAULT_OWNER, pattern = None):

        self.id = str(uuid.uuid4())
        self.type = type
        self.owner = owner
        self.pattern = pattern

        self.starttime = time.time()
        self.endtime = -1 # convention for situations that are not terminated

class Event(Situation):
    """ An event is a (immediate) change of the world. It has no
    duration, contrary to a StaticSituation that has a non-null duration.
    """

    # Some standard event types
    MODELLOAD = "modelload"

    def __init__(self, type = Situation.GENERIC, owner = Situation.DEFAULT_OWNER, pattern = None):
        super(Event, self).__init__(type, owner, pattern)
        self.endtime = self.starttime
