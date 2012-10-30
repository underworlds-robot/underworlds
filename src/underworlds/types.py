import uuid
import copy, json


# Node types
UNDEFINED = 0
MESH = 1
ENTITY = 2
CAMERA = 3

class Node():
    def __init__(self, name = "", type = UNDEFINED):

        ################################################################
        ##                     START OF THE API                       ##
        ################################################################
        self.id = str(uuid.uuid4())
        self.name = name
        self.type = type #one of the constant defined in Node.py
        self.parent = None
        self.children = []
        self.entity = None #if the node belongs to a group  (like a complex object), the node that represent this entity.
        self.transformation = None # 4x4 transformation matrix, relative to parent. Stored as a list, row major.
        self.properties = {}
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

        #for key, value in data.items():
        #    if hasattr(n, key):
        #        setattr(n, key, value)
        n.__dict__ = data
        return n



class Scene():

    def __init__(self):

        self.rootnode = Node("root", ENTITY)

        self.nodes = []

        self.nodes.append(self.rootnode)

    def list_entities(self):
        """ Returns the list of entities contained in the scene.

        Entities are group of nodes. They are either rigid bodies (ie, no
        joints, and hence only one node) or complex bodies (ie, with a
        kinematic chain and hence several nodes, one per joint).
        """
        return []

    def node(self, id):
        for n in self.nodes:
            if n.id == id:
                return n

class Timeline:
    pass

class World:

    def __init__(self, name):

        self.name = name
        self.scene = Scene()
        self.timeline = Timeline()

    def __repr__(self):
        return "world " + self.name


