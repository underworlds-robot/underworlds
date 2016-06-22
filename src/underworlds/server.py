import uuid
import time
import logging;logger = logging.getLogger("underworlds.server")

from underworlds.types import *
import underworlds_pb2 as gRPC 
from grpc.beta import interfaces as beta_interfaces


class Server(gRPC.BetaUnderworldsServicer):

    def __init__(self):

        self._worlds = {}

        # for each world (key), stores a mapping {client: list of node IDs that
        # are to be invalidated}
        self._node_invalidations = {}
        self._timeline_invalidations = {}

        self._clients = {} # for each client, stored the links (cf clients' types) with the various worlds.
        self._clientnames = {}
        
        # meshes are stored as a dictionary:
        # - the key is a unique ID
        # - the value is a ditionary with these keys:
        #   - vertices: [(x,y,z), ...]
        #   - faces: [(i1, i2, i3), ...] with i an index in the vertices list
        #   - normals
        self.meshes = {}

        self.starttime = time.time()

    def _new_client(self, id, name):
        self._clients[id] = {}
        self._clientnames[id] = name
        logger.info("New client <%s> has connected." % name)

    def _clientname(self, id):
        return self._clientnames.get(id, id)

    def _new_world(self, name):
        self._worlds[name] = World(name)
        self._node_invalidations[name] = {}
        self._timeline_invalidations[name] = {}


    def _get_scene_timeline(self, ctxt):

        world = ctxt.world

        if world not in self._worlds:
            self._new_world(world)
            logger.info("<%s> created a new world <%s>" % (self._clientname(ctxt.client), 
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

    def _update_node(self, scene, node):

        parent_has_changed = False

        node.last_update = time.time()

        oldnode = scene.node(node.id)

        if oldnode: # the node already exist
            parent_has_changed = oldnode.parent != node.parent

            # update the list of children
            node.children = [n.id for n in scene.nodes if n.parent == node.id]

            # replace the node
            scene.nodes = [node if old == node else old for old in scene.nodes]
            
            action = gRPC.NodeInvalidation.UPDATE

        else: # new node
            scene.nodes.append(node)
            if node.parent:
                parent_has_changed = True
            action = gRPC.NodeInvalidation.NEW

        return action, parent_has_changed

    def _delete_node(self, scene, id):
        scene.nodes.remove(scene.node(id))
 
    def _add_node_invalidation(self, world, node_id, invalidation_type):

        for client_id in self._node_invalidations[world].keys():
            self._node_invalidations[world][client_id].append(gRPC.NodeInvalidation(type=invalidation_type, id=node_id))

    #############################################
    ############ Underworlds API ################

    ############ GENERAL
    def helo(self, client, context):
        client_id = str(uuid.uuid4())
        logger.debug("Got <helo> from %s" % client_id)
        self._new_client(client_id, client.name)

        res = gRPC.Client(id=client_id)
        logger.debug("<helo> completed")
        return res

    def uptime(self, client, context):
        logger.debug("Got <uptime> from %s" % client.id)
        res = gRPC.Time(time=time.time() - self.starttime)
        logger.debug("<uptime> completed")
        return res

    def topology(self, client, context):
        logger.debug("Got <topology> from %s" % client.id)
    
        topo = gRPC.Topology()

        for w in self._worlds.keys():
            topo.worlds.append(w)

        for client_id, links in self._clients.items():
            client = topo.clients.add()
            client.id  = client_id
            client.name = self._clientname(client_id)

            for w, details in links.items():

                type, timestamp = details

                interaction = client.links.add()
                interaction.world = w
                interaction.type = type
                interaction.last_activity.time = timestamp



        logger.debug("<topology> completed")
        return topo



    ############ NODES
    def getNodesLen(self, ctxt, context):
        logger.debug("Got <getNodesLen> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene,_ = self._get_scene_timeline(ctxt)

        res = gRPC.Size(size=len(scene.nodes))
        logger.debug("<getNodesLen> completed")
        return res

    def getNodesIds(self, ctxt, context):
        logger.debug("Got <getNodesIds> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene,_ = self._get_scene_timeline(ctxt)

        nodes = gRPC.Nodes()
        for n in scene.nodes:
            nodes.ids.append(n.id)

        logger.debug("<getNodesIds> completed")
        return nodes

    def getRootNode(self, ctxt, context):
        logger.debug("Got <getRootNode> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene,_ = self._get_scene_timeline(ctxt)

        res = gRPC.Node(id=scene.rootnode.id)
        logger.debug("<getRootNode> completed")
        return res

    def getNode(self, nodeInCtxt, context):
        logger.debug("Got <getNode> from %s" % nodeInCtxt.context.client)
        self._update_current_links(nodeInCtxt.context.client, nodeInCtxt.context.world, READER)

        client_id, world = nodeInCtxt.context.client, nodeInCtxt.context.world

        scene,_ = self._get_scene_timeline(nodeInCtxt.context)

        self._update_current_links(client_id, world, READER)

        node = scene.node(nodeInCtxt.node.id)

        if not node:
            logger.warning("%s has required an non-existant"
                           "node %s" % (self._clientname(client_id), nodeInCtxt.node.id))
        else:
            res = node.serialize(gRPC.Node)
            logger.debug("<getNode> completed")
            return res


    def updateNode(self, nodeInCtxt, context):
        logger.debug("Got <updateNode> from %s" % nodeInCtxt.context.client)
        self._update_current_links(nodeInCtxt.context.client, nodeInCtxt.context.world, PROVIDER)

        client_id, world = nodeInCtxt.context.client, nodeInCtxt.context.world
        scene,_ = self._get_scene_timeline(nodeInCtxt.context)

        node = Node.deserialize(nodeInCtxt.node)

        invalidation_type, parent_has_changed = self._update_node(scene, node)

        logger.info("<%s> %s node <%s> in world <%s>" % \
                            (self._clientname(client_id), 
                             "updated" if invalidation_type==gRPC.NodeInvalidation.UPDATE else ("created" if invalidation_type==gRPC.NodeInvalidation.NEW else "deleted"),
                             repr(node), 
                             world))


        logger.debug("Adding invalidation action [" + str(invalidation_type) + "]")
        self._add_node_invalidation(world, node.id, invalidation_type)

        ## If necessary, update the node hierarchy
        if parent_has_changed:
            parent = scene.node(node.parent)
            if parent is None:
                logger.warning("Node %s references a non-exisiting parent" % node)
            elif node.id not in parent.children:
                parent.children.append(node.id)
                # tells everyone about the change to the parent
                logger.debug("Adding invalidation action [update " + parent.id + "] due to hierarchy update")
                self._add_node_invalidation(world, parent.id, gRPC.NodeInvalidation.UPDATE)

                # As a node has only one parent, if the parent has changed we must
                # remove our node for its previous parent
                for othernode in scene.nodes:
                    if othernode.id != parent.id and node.id in othernode.children:
                        othernode.children.remove(node.id)
                        # tells everyone about the change to the former parent
                        logger.debug("Adding invalidation action [update " + othernode.id + "] due to hierarchy update")
                        self._add_node_invalidation(world, othernode.id, gRPC.NodeInvalidation.UPDATE)
                        break

        logger.debug("<updateNode> completed")
        return gRPC.Empty()

    def deleteNode(self, nodeInCtxt, context):
        logger.debug("Got <deleteNode> from %s" % nodeInCtxt.context.client)
        self._update_current_links(nodeInCtxt.context.client, nodeInCtxt.context.world, PROVIDER)

        client_id, world = nodeInCtxt.context.client, nodeInCtxt.context.world
        scene,_ = self._get_scene_timeline(nodeInCtxt.context)


        node = scene.node(nodeInCtxt.node.id)
        logger.info("<%s> deleted node <%s> in world <%s>" % \
                            (self._clientname(client_id), 
                             repr(node), 
                             world))

        action = self._delete_node(scene, nodeInCtxt.node.id)

        # tells everyone about the change
        logger.debug("Sent invalidation action [delete]")
        self._add_node_invalidation(world, nodeInCtxt.node.id, gRPC.DELETE)

        # Also remove the node for its parent's children
        parent = scene.node(node.parent)
        if parent:
            parent.children.remove(node.id)
            # tells everyone about the change to the parent
            logger.debug("Sent invalidation action [update " + parent.id + "] due to hierarchy update")
            self._add_node_invalidation(world, parent.id, gRPC.NodeInvalidation.UPDATE)

        logger.debug("<updateNode> completed")
        return gRPC.Empty()

    #### Nodes invalidation streams
    def getNodeInvalidations(self, ctxt, context):
        """ For each pair (world, client), check if nodes need to be
        invalidated, and yield accordingly the invalidation messages.
        """

        world, client = ctxt.world, ctxt.client

        # (if this client is not yet monitoring this world, add it as a side effect of the test)
        if self._node_invalidations[world].setdefault(client,[]):
            for invalidation in self._node_invalidations[world][client]:
                yield invalidation
            self._node_invalidations[world][client] = []

        #try:
        #except Exception as e:
        #    context.details("Exception in getInvalidations: %s" %repr(e))
        #    context.code(beta_interfaces.StatusCode.UNKNOWN)


    ############ TIMELINES
    def timelineOrigin(self, ctxt, context):
        logger.debug("Got <timelineOrigin> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        _,timeline = self._get_scene_timeline(ctxt)

        res = gRPC.Time(time=timeline.origin)
        logger.debug("<timelineOrigin> completed")
        return res


    #### Timeline invalidation streams
    def getTimelineInvalidations(self, ctxt, context):
        """ For each pair (world, client), check if situations need to be
        invalidated, and yield accordingly the invalidation messages.
        """

        world, client = ctxt.world, ctxt.client


        if client in self._timeline_invalidations[world] and self._timeline_invalidations[world][client]:
            for invalidation in self._timeline_invalidations[world][client]:
                yield invalidation
            self._timeline_invalidations[world][client] = []



    ############ MESHES
    def hasMesh(self, meshInCtxt, context):
        logger.debug("Got <hasMesh> from %s" % meshInCtxt.client.id)
        res = gRPC.Bool(value=(meshInCtxt.mesh.id in self.meshes))
        logger.debug("<hasMesh> completed")
        return res

    def getMesh(self, meshInCtxt, context):
        logger.debug("Got <getMesh> from %s" % meshInCtxt.client.id)
        logger.debug("<getMesh> completed")
        return self.meshes[meshInCtxt.mesh.id]

    def pushMesh(self, meshInCtxt, context):
        logger.debug("Got <pushMesh> from %s" % meshInCtxt.client.id)

        mesh_id = meshInCtxt.mesh.id
        self.meshes[mesh_id] = meshInCtxt.mesh

        logger.info("<%s> added a new mesh ID %s (%d faces)" % \
                                (self._clientname(meshInCtxt.client.id),
                                mesh_id, 
                                len(self.meshes[mesh_id].faces)))

        logger.debug("<pushMesh> completed")
        return gRPC.Empty()


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
#
#
#    def run(self):
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

#                ###########################################################################
#                # TIMELINES
#                ###########################################################################
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

#                else:
#                    logger.warning("Unknown request <%s>" % cmd)
#                    rpc.send(b"unknown request")
#            else:
#                invalidation.send(b"nop")
#
#        logger.info("Closing the server.")

def start():

    server = gRPC.beta_create_Underworlds_server(Server())
    port = server.add_insecure_port('[::]:50051')

    if port == 0:
        logger.error("The port is already in use! Underworlds server already running?"
                     "I can not start the server.")
        return server

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
