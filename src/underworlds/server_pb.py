import uuid
import time
import logging;logger = logging.getLogger("underworlds.server")

from underworlds.types import *
import underworlds_pb2 as gRPC 


class Server(gRPC.BetaUnderworldsServicer):

    def __init__(self):
        self._running = True
        self._worlds = {}
        self._clients = {} # for each client, stored the links (cf clients' types) with the various worlds.
        self._clientnames = {}
        
        # meshes are stored as a dictionary:
        # - the key is a unique ID
        # - the value is a ditionary with these keys:
        #   - vertices: [(x,y,z), ...]
        #   - faces: [(i1, i2, i3), ...] with i an index in the vertices list
        #   - normals
        self.meshes = {}

    def _new_client(self, id, name):
        self._clients[id] = {}
        self._clientnames[id] = name
        logger.info("New client <%s> has connected." % name)

    def _clientname(self, id):
        return self._clientnames.get(id, id)

    def _new_world(self, name):
        self._worlds[name] = World(name)


    def _get_scene_timeline(self, ctxt):

        world = ctxt.world

        if world not in self._worlds:
            self._new_world(world)
            logger.info("<%s> created a new world %s" % (self._clientname(ctxt.client), 
                                                         world))

        scene = self._worlds[world].scene
        timeline = self._worlds[world].timeline

        return scene, timeline

    def _update_current_links(self, client, world, type):
        if world in self._clients[client]:
            current_type = self._clients[client][world][0]
            # update only if the current link is 'READER' (we do not 
            # want a 'READER' to overwrite a 'PROVIDER' for instance)
            type = type if current_type == READER else current_type
        self._clients[client][world] = (type, time.time())

    def _serialize(self, n):
        """Outputs a protobuf encoding of the node
        """

        node = gRPC.Node()
        node.id = n.id
        node.name = n.name
        node.type = n.type
        node.parent = n.parent if n.parent is not None else ""

        for c in n.children:
            node.children.append(c)

        for v in n.transformation.flatten().tolist():
            node.transformation.append(v)

        node.last_update = n.last_update

        node.physics = n.properties["physics"]

        return node

    #############################################
    ############ Underworlds API ################

    def Helo(self, client, context):
        client_id = str(uuid.uuid4())
        self._new_client(client_id, client.name)
        return gRPC.Client(id=client_id)


    def GetNodesLen(self, ctxt, context):
        scene,_ = self._get_scene_timeline(ctxt)
        return gRPC.Size(size=len(scene.nodes))

    def GetNodesIds(self, ctxt, context):
        scene,_ = self._get_scene_timeline(ctxt)

        nodes = gRPC.Nodes()
        for n in scene.nodes:
            nodes.ids.append(n.id)

        return nodes

    def GetRootNode(self, ctxt, context):
        scene,_ = self._get_scene_timeline(ctxt)
        return gRPC.Node(id=scene.rootnode.id)

    def GetNode(self, nodeInCtxt, context):

        clientid, world = nodeInCtxt.context.client, nodeInCtxt.context.world

        scene,_ = self._get_scene_timeline(nodeInCtxt.context)

        self._update_current_links(clientid, world, READER)

        node = scene.node(nodeInCtxt.id)

        if not node:
            logger.warning("%s has required an non-existant"
                           "node %s" % (self._clientname(clientid), nodeInCtxt.id))
        else:
            return self._serialize(node)
#
#    def get_current_topology(self):
#        return {"clientnames": self._clientnames, "clients": self._clients, "worlds": list(self._worlds.keys())}
#
#    def delete_node(self, scene, id):
#        scene.nodes.remove(scene.node(id))
#
#    def update_node(self, scene, node):
#
#        parent_has_changed = False
#
#        node.last_update = time.time()
#
#        oldnode = scene.node(node.id)
#
#        if oldnode: # the node already exist
#            parent_has_changed = oldnode.parent != node.parent
#
#            # update the list of children
#            node.children = [n.id for n in scene.nodes if n.parent == node.id]
#
#            # replace the node
#            scene.nodes = [node if old == node else old for old in scene.nodes]
#            
#            action = "update"
#
#        else: # new node
#            scene.nodes.append(node)
#            if node.parent:
#                parent_has_changed = True
#            action = "new"
#        
#        return str(action + " " + node.id), parent_has_changed
#
#    def event(self, timeline, sit):
#
#        if timeline.situation(sit.id): # the situation already exist. Error!
#            raise Exception("Attempting to add twice the same situation!")
#
#        else: # new situation
#            timeline.event(sit)
#            action = "event"
#
#        return str(action + " " + sit.serialize())
#
#    def new_situation(self, timeline, sit):
#
#        if timeline.situation(sit.id): # the situation already exist. Error!
#            raise Exception("Attempting to add twice the same situation!")
#
#        else: # new situation
#            timeline.start(sit)
#            action = "start"
#        
#        return action + " " + json.dumps(sit.serialize())
#
#    def end_situation(self, timeline, id):
#
#        sit = timeline.situation(id)
#
#        if not sit:
#            raise Exception("Attempting to end a non-existant situation!")
#
#        timeline.end(sit)
#        action = "end"
#        
#        return str(action + " " + id)
#
#
#    def stop(self):
#        self._running = False
#
#    def uptime(self):
#        return time.time() - self.starttime
#
#    def run(self):
#
#        logger.info("Starting the server.")
#
#        self.starttime = time.time()
#
#        context = zmq.Context()
#        rpc = context.socket(zmq.REP)
#        rpc.bind("tcp://*:5555")
#
#        invalidation = context.socket(zmq.PUB)
#        invalidation.bind ("tcp://*:5556")
#
#        poller = zmq.Poller()
#        poller.register(rpc, zmq.POLLIN)
#
#
#
#        while self._running:
#            socks = dict(poller.poll(200))
#            
#            if socks.get(rpc) == zmq.POLLIN:
#
#                req = rpc.recv_json()
#                client = req["client"]
#                clientname = self._clientname(client)
#                world = None
#                scene = None
#                timeline = None
#
#
#                req = req["req"].split(" ",1)
#                cmd = req[0]
#                arg = ""
#                if len(req) == 2:
#                    arg = req[1]
#
#                logger.debug("Received request: <%s(%s)> from <%s> on world <%s>" % \
#                                (cmd, 
#                                 arg,
#                                 clientname,
#                                 world))
#
#
#                ###########################################################################
#                # SCENES
#                ###########################################################################
#                if cmd == "deepcopy":
#                    self.update_current_links(client, world, PROVIDER)
#                    logger.info("<%s> made a deep copy of world %s "
#                                "into world %s" % (clientname, arg, world))
#                    self._worlds[world].deepcopy(self._worlds[arg])
#                    rpc.send(b"ack")
#
#
#
#                elif cmd == "update_node":
#                    self.update_current_links(client, world, PROVIDER)
#                    node = Node.deserialize(json.loads(arg))
#                    rpc.send(b"ack")
#
#                    logger.info("<%s> updated node %s in world %s" % \
#                                        (clientname, 
#                                         repr(node), 
#                                         world))
#
#                    action, parent_has_changed = self.update_node(scene, node)
#                    # tells everyone about the change
#                    logger.debug("Sent invalidation action [" + action + "]")
#                    invalidation.send(("%s?nodes### %s" % (world, action)).encode())
#
#                    ## If necessary, update the node hierarchy
#                    if parent_has_changed:
#                        parent = scene.node(node.parent)
#                        if parent is None:
#                            logger.warning("Node %s references a non-exisiting parent" % node)
#                        elif node.id not in parent.children:
#                            parent.children.append(node.id)
#                            # tells everyone about the change to the parent
#                            logger.debug("Sent invalidation action [update " + parent.id + "] due to hierarchy update")
#                            invalidation.send(("%s?nodes### update %s" % (world, parent.id)).encode())
#
#                            # As a node has only one parent, if the parent has changed we must
#                            # remove our node for its previous parent
#                            for othernode in scene.nodes:
#                                if othernode.id != parent.id and node.id in othernode.children:
#                                    othernode.children.remove(node.id)
#                                    # tells everyone about the change to the former parent
#                                    logger.debug("Sent invalidation action [update " + othernode.id + "] due to hierarchy update")
#                                    invalidation.send(("%s?nodes### update %s" % (world, othernode.id)).encode())
#                                    break
#
#                elif cmd == "delete_node":
#                    self.update_current_links(client, world, PROVIDER)
#                    rpc.send(b"ack")
#
#                    node = scene.node(arg)
#                    logger.info("<%s> deleted node %s in world %s" % \
#                                    (clientname, repr(node), world))
#
#                    action = self.delete_node(scene, arg)
#                    # tells everyone about the change
#                    logger.debug("Sent invalidation action [delete]")
#                    invalidation.send(("%s?nodes### delete %s" % (world, arg)).encode())
#
#                    # Also remove the node for its parent's children
#                    parent = scene.node(node.parent)
#                    if parent:
#                        parent.children.remove(node.id)
#                        # tells everyone about the change to the parent
#                        logger.debug("Sent invalidation action [update " + parent.id + "] due to hierarchy update")
#                        invalidation.send(("%s?nodes### update %s" % (world, parent.id)).encode())
#
#                ###########################################################################
#                # TIMELINES
#                ###########################################################################
#                elif cmd == "timeline_origin":
#                    self.update_current_links(client, world, READER)
#                    rpc.send_json(timeline.origin)
#
#                elif cmd == "get_situations":
#                    #self.update_current_links(client, world, READER)
#                    #rpc.send_json(timeline.origin)
#                    #action = self.new_situation(timeline, situation)
#                    ## tells everyone about the change
#                    #logger.debug("Sent invalidation action [" + action + "]")
#                    #invalidation.send(("%s?timeline### %s" % (world, action)).encode())
#                    pass #TODO
#
#                elif cmd == "event":
#                    self.update_current_links(client, world, PROVIDER)
#                    situation = Situation.deserialize(arg)
#                    rpc.send(b"ack")
#                    action = self.event(timeline, situation)
#                    # tells everyone about the change
#                    logger.debug("Sent invalidation action [" + action + "]")
#                    invalidation.send("%s?timeline### %s" % (world, action).encode())
#                elif cmd == "new_situation":
#                    self.update_current_links(client, world, PROVIDER)
#                    situation = Situation.deserialize(json.loads(arg))
#                    rpc.send(b"ack")
#                    action = self.new_situation(timeline, situation)
#                    # tells everyone about the change
#                    logger.debug("Sent invalidation action [" + action + "]")
#                    invalidation.send(("%s?timeline### %s" % (world, action)).encode())
#
#                elif cmd == "end_situation":
#                    self.update_current_links(client, world, PROVIDER)
#                    rpc.send(b"ack")
#                    action = self.end_situation(timeline, arg)
#                    # tells everyone about the change
#                    logger.debug("Sent invalidation action [" + action + "]")
#                    invalidation.send(("%s?timeline### %s" % (world, action)).encode())
#
#
#
#                ###########################################################################
#                # MESHES
#                ###########################################################################
#                elif cmd == "push_mesh":
#                    mesh_id, data = arg.split(" ",1)
#                    self.meshes[mesh_id] = json.loads(data)
#                    logger.info("<%s> added a new mesh ID %s (%d faces)" % \
#                                           (clientname,
#                                            mesh_id, 
#                                            len(self.meshes[mesh_id]['faces'])))
#                    rpc.send(b"ack")
#
#                elif cmd == "get_mesh":
#                    rpc.send_json(self.meshes[arg])
#
#                elif cmd == "has_mesh":
#                    rpc.send_json(arg in self.meshes)
#
#                ###########################################################################
#                # MISC
#                ###########################################################################
#
#                elif cmd == "uptime":
#                    rpc.send_json(self.uptime())
#
#                elif cmd == "get_topology":
#                    rpc.send_json(self.get_current_topology())
#
#                ###########################################################################
#
#                else:
#                    logger.warning("Unknown request <%s>" % cmd)
#                    rpc.send(b"unknown request")
#            else:
#                invalidation.send(b"nop")
#
#        logger.info("Closing the server.")

def start():

    server = gRPC.beta_create_Underworlds_server(Server())
    server.add_insecure_port('[::]:50051')

    logger.info("Starting the server.")
    server.start()

    return server


if __name__ == "__main__":

    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)

    server = start()

    try:
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        logger.info("Closing the server.")
        server.stop(0)

    logger.info("Bye bye.")
