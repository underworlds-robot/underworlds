import uuid
import time
import logging;logger = logging.getLogger("underworlds.server")

from underworlds.types import *
from underworlds.helpers.profile import profile, profileonce
from grpc.framework.interfaces.face.face import ExpirationError,NetworkError,AbortionError
import underworlds.underworlds_pb2 as gRPC 
from grpc.beta import interfaces as beta_interfaces
from grpc.beta import implementations

_TIMEOUT_SECONDS = 1

class Client:

    def __init__(self, name, host, port):
        self.id = str(uuid.uuid4())
        self.name = name

        # stores the links (cf clients' types) with the various worlds.
        self.links = {}

        self.channel = None
        self.invalidation_server = self._connect_invalidation_server(name, host, port)
        self.isactive = (self.invalidation_server is not None)

        self.active_invalidations = []

        self.grpc_client = gRPC.Client(id=self.id)

        if self.isactive:
            logger.debug("Client %s (id: %s) successfully created." % (self.name, self.id))
        else:
            logger.warn("Client %s (id: %s) created but inactive." % (self.name, self.id))


    def _connect_invalidation_server(self, name, host, port):
        try:
            self.channel = implementations.insecure_channel(host, port)
            invalidation_server = gRPC.beta_create_UnderworldsInvalidation_stub(self.channel)
            logger.info("Connected to invalidation server of client <%s>" % name)
            return invalidation_server

        except (NetworkError, AbortionError) as e:
            logger.warn("Underworld server unable to establish a connection with Underworlds'\n"
                         " client <%> on %s:%d. Client died? Unreachable over network?\n"
                         "Removing the client.\nOriginal error: %s" % (name, host, port, str(e)))
            return None

    def emit_invalidation(self, invalidation):

        if not self.isactive:
            logger.debug("Attempting to send invalidations to inactive client <%s>. Skipping" % self.name)
            return

        future = self.invalidation_server.emitNodesInvalidation.future(invalidation, _TIMEOUT_SECONDS)

        # remove the future form the current list of active invalidations upon completion
        future.add_done_callback(self.active_invalidations.remove)

        self.active_invalidations.append(future)

    def close(self):
        self.isactive = False



class Server(gRPC.BetaUnderworldsServicer):

    def __init__(self):

        self._worlds = {}

        # for each world (key), stores the list of clients that are to be notified when a change
        # occurs in that world
        self._observers = {}
        self._invalidation_futures = []
        self._timeline_invalidations = {}

        self._clients = {} 
        
        # meshes are stored as a dictionary:
        # - the key is a unique ID
        # - the value is a ditionary with these keys:
        #   - vertices: [(x,y,z), ...]
        #   - faces: [(i1, i2, i3), ...] with i an index in the vertices list
        #   - normals
        self.meshes = {}

        self.starttime = time.time()

    def _clientname(self, id):
        return self._clients[id].name

    def _new_world(self, name):
        self._worlds[name] = World(name)
        self._observers[name] = set()
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

        # register client for notifications to future changes to world 'world'
        self._observers.setdefault(world, set()).add(client)

        if world in self._clients[client].links:
            current_type = self._clients[client].links[world][0]
            # update only if the current link is 'READER' (we do not 
            # want a 'READER' to overwrite a 'PROVIDER' for instance)
            type = type if current_type == READER else current_type
        self._clients[client].links[world] = (type, time.time())

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
            
            action = gRPC.NodesInvalidation.UPDATE

        else: # new node
            scene.nodes.append(node)
            if node.parent:
                parent_has_changed = True
            action = gRPC.NodesInvalidation.NEW

        return action, parent_has_changed

    def _delete_node(self, scene, id):
        scene.nodes.remove(scene.node(id))

    @profile
    def _emit_nodes_invalidation(self, world, node_id, invalidation_type):

        invalidation = gRPC.NodesInvalidation(type=invalidation_type, world=world, id=node_id)


        for client_id in self._observers[world]:
            logger.debug("Informing client <%s> that nodes have been invalidated in world <%s>" % (self._clientname(client_id), world))
            self._clients[client_id].emit_invalidation(invalidation)


    @profile
    def _add_timeline_invalidation(self, world, sit_id, invalidation_type):

        for client_id in self._timeline_invalidations[world].keys():
            self._timeline_invalidations[world][client_id].append(gRPC.TimelineInvalidation(type=invalidation_type, id=sit_id))

    #############################################
    ############ Underworlds API ################

    ############ GENERAL
    @profile
    def helo(self, client, context):
        logger.debug("Got <helo> from %s" % client.name)
        c = Client(client.name, client.host, client.invalidation_server_port)
        self._clients[c.id] = c

        logger.debug("<helo> completed")
        return c.grpc_client

    @profile
    def byebye(self, client, context):
        logger.debug("Got <byebye> from %s" % (self._clientname(client.id)))
        self._clients[client.id].close()
        logger.debug("<byebye> completed")
        return gRPC.Empty()


    @profile
    def uptime(self, client, context):
        logger.debug("Got <uptime> from %s" % client.id)
        res = gRPC.Time(time=time.time() - self.starttime)
        logger.debug("<uptime> completed")
        return res

    @profile
    def topology(self, client, context):
        logger.debug("Got <topology> from %s" % client.id)
    
        topo = gRPC.Topology()

        for w in self._worlds.keys():
            topo.worlds.append(w)

        for client_id in self._clients.keys():
            links = self._clients[client_id].links
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

    @profile
    def reset(self, client, context):
        logger.debug("Got <reset> from %s" % client.id)
        logger.warning("Resetting Underworlds upon client <%s> request" % client.id)
        logger.warning("This might break other clients!")

        self._worlds = {}

        self._observers = {}
        self._timeline_invalidations = {}


        logger.debug("<reset> completed")

        return gRPC.Empty()


    ############ NODES
    @profile
    def getNodesLen(self, ctxt, context):
        logger.debug("Got <getNodesLen> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene,_ = self._get_scene_timeline(ctxt)

        res = gRPC.Size(size=len(scene.nodes))
        logger.debug("<getNodesLen> completed")
        return res

    @profile
    def getNodesIds(self, ctxt, context):
        logger.debug("Got <getNodesIds> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene,_ = self._get_scene_timeline(ctxt)

        nodes = gRPC.Nodes()
        for n in scene.nodes:
            nodes.ids.append(n.id)

        logger.debug("<getNodesIds> completed")
        return nodes

    @profile
    def getRootNode(self, ctxt, context):
        logger.debug("Got <getRootNode> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene,_ = self._get_scene_timeline(ctxt)

        res = gRPC.Node(id=scene.rootnode.id)
        logger.debug("<getRootNode> completed")
        return res

    @profile
    def getNode(self, nodeInCtxt, context):
        logger.debug("Got <getNode> from %s" % nodeInCtxt.context.client)
        self._update_current_links(nodeInCtxt.context.client, nodeInCtxt.context.world, READER)

        client_id, world = nodeInCtxt.context.client, nodeInCtxt.context.world

        scene,_ = self._get_scene_timeline(nodeInCtxt.context)

        self._update_current_links(client_id, world, READER)

        node = scene.node(nodeInCtxt.node.id)

        if not node:
            logger.warning("%s has required an non-existant "
                           "node <%s> in world %s" % (self._clientname(client_id), nodeInCtxt.node.id, world))

            context.details("Node <%s> does not exist in world %s" % (nodeInCtxt.node.id, world))
            context.code(beta_interfaces.StatusCode.UNKNOWN)


        else:
            res = node.serialize(gRPC.Node)
            logger.debug("<getNode> completed")
            return res


    @profile
    def updateNode(self, nodeInCtxt, context):
        logger.debug("Got <updateNode> from %s" % nodeInCtxt.context.client)
        self._update_current_links(nodeInCtxt.context.client, nodeInCtxt.context.world, PROVIDER)

        client_id, world = nodeInCtxt.context.client, nodeInCtxt.context.world
        scene,_ = self._get_scene_timeline(nodeInCtxt.context)

        node = Node.deserialize(nodeInCtxt.node)

        invalidation_type, parent_has_changed = self._update_node(scene, node)

        logger.info("<%s> %s node <%s> in world <%s>" % \
                            (self._clientname(client_id), 
                             "updated" if invalidation_type==gRPC.NodesInvalidation.UPDATE else ("created" if invalidation_type==gRPC.NodesInvalidation.NEW else "deleted"),
                             repr(node), 
                             world))


        logger.debug("Adding invalidation action [" + str(invalidation_type) + "]")
        self._emit_nodes_invalidation(world, node.id, invalidation_type)

        ## If necessary, update the node hierarchy
        if parent_has_changed:
            parent = scene.node(node.parent)
            if parent is None:
                logger.warning("Node %s references a non-exisiting parent" % node)
            elif node.id not in parent.children:
                parent.children.append(node.id)
                # tells everyone about the change to the parent
                logger.debug("Adding invalidation action [update " + parent.id + "] due to hierarchy update")
                self._emit_nodes_invalidation(world, parent.id, gRPC.NodesInvalidation.UPDATE)

                # As a node has only one parent, if the parent has changed we must
                # remove our node for its previous parent
                for othernode in scene.nodes:
                    if othernode.id != parent.id and node.id in othernode.children:
                        othernode.children.remove(node.id)
                        # tells everyone about the change to the former parent
                        logger.debug("Adding invalidation action [update " + othernode.id + "] due to hierarchy update")
                        self._emit_nodes_invalidation(world, othernode.id, gRPC.NodesInvalidation.UPDATE)
                        break

        logger.debug("<updateNode> completed")
        return gRPC.Empty()

    @profile
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
        self._emit_nodes_invalidation(world, nodeInCtxt.node.id, gRPC.NodesInvalidation.DELETE)

        # Also remove the node for its parent's children
        parent = scene.node(node.parent)
        if parent:
            parent.children.remove(node.id)
            # tells everyone about the change to the parent
            logger.debug("Sent invalidation action [update " + parent.id + "] due to hierarchy update")
            self._emit_nodes_invalidation(world, parent.id, gRPC.NodesInvalidation.UPDATE)

        logger.debug("<updateNode> completed")
        return gRPC.Empty()


    ############ TIMELINES
    @profile
    def timelineOrigin(self, ctxt, context):
        logger.debug("Got <timelineOrigin> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        _,timeline = self._get_scene_timeline(ctxt)

        res = gRPC.Time(time=timeline.origin)
        logger.debug("<timelineOrigin> completed")
        return res

    @profile
    def event(self, sitInCtxt, context):

        client, world = sitInCtxt.context.client, sitInCtxt.context.world

        logger.debug("Got <event> from %s" % client)

        self._update_current_links(client, world, PROVIDER)

        _, timeline = self._get_scene_timeline(sitInCtxt.context)
        sit = Situation.deserialize(sitInCtxt.situation)

        if timeline.situation(sit.id): # the situation already exist. Error!
            raise Exception("Attempting to add twice the same situation!")

        timeline.event(sit)
        self._add_timeline_invalidation(world, sit.id, gRPC.TimelineInvalidation.EVENT)

        logger.debug("<event> completed")
        return gRPC.Empty()

    @profile
    def startSituation(self, sitInCtxt, context):

        client, world = sitInCtxt.context.client, sitInCtxt.context.world

        logger.debug("Got <startSituation> from %s" % client)

        self._update_current_links(client, world, PROVIDER)

        _, timeline = self._get_scene_timeline(sitInCtxt.context)
        sit = Situation.deserialize(sitInCtxt.situation)

        if timeline.situation(sit.id): # the situation already exist. Error!
            raise Exception("Attempting to add twice the same situation!")

        timeline.start(sit)
        self._add_timeline_invalidation(world, sit.id, gRPC.TimelineInvalidation.START)

        logger.debug("<startSituation> completed")
        return gRPC.Empty()

    @profile
    def endSituation(self, sitInCtxt, context):

        client, world = sitInCtxt.context.client, sitInCtxt.context.world

        logger.debug("Got <endSituation> from %s" % client)

        self._update_current_links(client, world, PROVIDER)

        _, timeline = self._get_scene_timeline(sitInCtxt.context)

        sit = timeline.situation(sitInCtxt.situation.id)
        if not sit:
            raise Exception("Attempting to end a non-existant situation!")

        timeline.end(sit)
        self._add_timeline_invalidation(world, sit.id, gRPC.TimelineInvalidation.END)

        logger.debug("<endSituation> completed")
        return gRPC.Empty()

    #### Timeline invalidation streams
    def getTimelineInvalidations(self, ctxt, context):
        """ For each pair (world, client), check if situations need to be
        invalidated, and yield accordingly the invalidation messages.
        """

        world, client = ctxt.world, ctxt.client

        # (if this client is not yet monitoring this world, add it as a side effect of the test)
        if self._timeline_invalidations[world].setdefault(client,[]):
            for invalidation in self._timeline_invalidations[world][client]:
                yield invalidation
            self._timeline_invalidations[world][client] = []



    ############ MESHES
    @profile
    def hasMesh(self, meshInCtxt, context):
        logger.debug("Got <hasMesh> from %s" % meshInCtxt.client.id)
        res = gRPC.Bool(value=(meshInCtxt.mesh.id in self.meshes))
        logger.debug("<hasMesh> completed")
        return res

    @profile
    def getMesh(self, meshInCtxt, context):
        logger.debug("Got <getMesh> from %s" % meshInCtxt.client.id)
        logger.debug("<getMesh> completed")
        return self.meshes[meshInCtxt.mesh.id]

    @profile
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

def start():

    PORT="50051"

    server = gRPC.beta_create_Underworlds_server(Server())
    port = server.add_insecure_port('[::]:%s' % PORT)

    if port == 0:
        raise RuntimeError("The port %s is already in use! Underworlds server already running? "
                     "I can not start the server." % PORT)

    logger.info("Starting the server...")
    server.start()
    time.sleep(0.2) # leave some time to the server to start
    logger.info("Server started.")

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
