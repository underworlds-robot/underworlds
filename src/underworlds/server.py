import uuid
import time
import threading
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

        future = self.invalidation_server.emitInvalidation.future(invalidation, _TIMEOUT_SECONDS)

        self.active_invalidations.append(future)

        # remove the future form the current list of active invalidations upon completion
        future.add_done_callback(self._cleanup_completed_invalidations)


    def _cleanup_completed_invalidations(self, invalidation):
        e = invalidation.exception()
        if e is not None:
            logger.warn("An exception occured while sending invalidations to %s: %s" % (self.name, str(e)))
            self.isactive = False
        else:
            self.active_invalidations.remove(invalidation)

    def reset_links(self):
        self.links = {}

    def close(self):
        self.isactive = False
        logger.debug("Waiting for all pending invalidation to client <%s> to complete..." % self.name)
        for i in self.active_invalidations:
            i.result()
        logger.debug("No more pending invalidations. The client <%s> is now properly disconnected." % self.name)
        self.active_invalidations = []




class Server(gRPC.BetaUnderworldsServicer):

    def __init__(self):

        self._worlds = {}

        self._clients = {} 
        self._client_lock = threading.RLock()

        # meshes are stored as a dictionary:
        # - the key is a unique ID
        # - the value is a ditionary with these keys:
        #   - vertices: [(x,y,z), ...]
        #   - faces: [(i1, i2, i3), ...] with i an index in the vertices list
        #   - normals
        self.meshes = {}

        self.starttime = time.time()

    def _clientname(self, id):
        with self._client_lock:
            return self._clients[id].name

    def _new_world(self, name):
        self._worlds[name] = World(name)


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

        with self._client_lock:
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
            node._children = [n.id for n in scene.nodes if n.parent == node.id]

            # replace the node
            scene.nodes = [node if old == node else old for old in scene.nodes]
            
            action = UPDATE

        else: # new node
            scene.nodes.append(node)
            parent_has_changed = True
            if node.parent is None:
                node.parent = scene.rootnode.id
            action = NEW

        return action, parent_has_changed

    def _delete_node(self, scene, id):
        scene.nodes.remove(scene.node(id))

    def _update_situation(self, timeline, situation):

        situation.last_update = time.time()

        if situation.id in timeline.situations:
            action = UPDATE
        else:
            action = NEW

        timeline.update(situation)

        return action

    @profile
    def _emit_invalidation(self, target, world, node_ids, invalidation_type):

        invalidation = gRPC.Invalidation(target=target,
                                         type=invalidation_type, 
                                         world=world)
        invalidation.ids[:] = node_ids


        with self._client_lock:
            for client_id in self._clients:
                if world in self._clients[client_id].links:
                    logger.debug("Informing client <%s> that nodes have been invalidated in world <%s>" % (self._clientname(client_id), world))
                    self._clients[client_id].emit_invalidation(invalidation)


    #############################################
    ############ Underworlds API ################

    ############ GENERAL
    @profile
    def helo(self, client, context):
        logger.debug("Got <helo> from %s" % client.name)
        c = Client(client.name, client.host, client.invalidation_server_port)
        with self._client_lock:
            self._clients[c.id] = c

        logger.debug("<helo> completed")
        return c.grpc_client

    @profile
    def byebye(self, client, context):
        logger.debug("Got <byebye> from %s" % (self._clientname(client.id)))

        with self._client_lock:
            self._clients[client.id].close()
            del self._clients[client.id]

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

        with self._client_lock:
            for client_id in self._clients:
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

        with self._client_lock:
            for cid, c in self._clients.items():
                c.reset_links()

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
        logger.debug("Got <getNode> from %s" % self._clientname(nodeInCtxt.context.client))

        client_id, world = nodeInCtxt.context.client, nodeInCtxt.context.world

        scene,_ = self._get_scene_timeline(nodeInCtxt.context)

        self._update_current_links(client_id, world, READER)

        if not nodeInCtxt.node.id:
            logger.warning("%s has required a node without specifying its id!" % (self._clientname(client_id)))

            context.details("No node id provided")
            context.code(beta_interfaces.StatusCode.NOT_FOUND)
            return gRPC.Node()

        node = scene.node(nodeInCtxt.node.id)

        if not node:
            logger.warning("%s has required an non-existant "
                           "node <%s> in world %s" % (self._clientname(client_id), nodeInCtxt.node.id, world))

            context.details("Node <%s> does not exist in world %s" % (nodeInCtxt.node.id, world))
            context.code(beta_interfaces.StatusCode.NOT_FOUND)
            return gRPC.Node()


        else:
            res = node.serialize(gRPC.Node)
            logger.debug("<getNode> completed")
            return res


    @profile
    def updateNodes(self, nodesInCtxt, context):
        logger.debug("Got <updateNodes> from %s" % nodesInCtxt.context.client)
        self._update_current_links(nodesInCtxt.context.client, nodesInCtxt.context.world, PROVIDER)

        client_id, world = nodesInCtxt.context.client, nodesInCtxt.context.world
        scene,_ = self._get_scene_timeline(nodesInCtxt.context)

        nodes_to_invalidate_new = []
        nodes_to_invalidate_update = []
        for gRPCNode in nodesInCtxt.nodes:
            node = Node.deserialize(gRPCNode)

            invalidation_type, parent_has_changed = self._update_node(scene, node)

            logger.info("<%s> %s node <%s> in world <%s>" % \
                                (self._clientname(client_id), 
                                "updated" if invalidation_type==UPDATE else "created",
                                repr(node), 
                                world))

            if invalidation_type ==  UPDATE:
                nodes_to_invalidate_update.append(gRPCNode.id)
            elif invalidation_type ==  NEW:
                nodes_to_invalidate_new.append(gRPCNode.id)
            else:
                raise RuntimeError("Unexpected invalidation type")


            ## If necessary, update the node hierarchy
            if parent_has_changed:
                parent = scene.node(node.parent)
                if parent is None:
                    logger.warning("Node %s references a non-exisiting parent" % node)
                elif node.id not in parent.children:
                    parent._children.append(node.id)
                    # tells everyone about the change to the parent
                    logger.debug("Adding invalidation action [update " + parent.id + "] due to hierarchy update")
                    nodes_to_invalidate_update.append(parent.id)

                    # As a node has only one parent, if the parent has changed we must
                    # remove our node from its previous parent
                    for othernode in scene.nodes:
                        if othernode.id != parent.id and node.id in othernode.children:
                            othernode._children.remove(node.id)
                            # tells everyone about the change to the former parent
                            logger.debug("Adding invalidation action [update " + othernode.id + "] due to hierarchy update")
                            nodes_to_invalidate_update.append(othernode.id)
                            break

        if nodes_to_invalidate_update:
            self._emit_invalidation(gRPC.Invalidation.SCENE, world, nodes_to_invalidate_update, UPDATE)
        if nodes_to_invalidate_new:
            self._emit_invalidation(gRPC.Invalidation.SCENE, world, nodes_to_invalidate_new, NEW)


        logger.debug("<updateNodes> completed")
        return gRPC.Empty()

    @profile
    def deleteNodes(self, nodesInCtxt, context):
        logger.debug("Got <deleteNodes> from %s" % nodesInCtxt.context.client)
        self._update_current_links(nodesInCtxt.context.client, nodesInCtxt.context.world, PROVIDER)

        client_id, world = nodesInCtxt.context.client, nodesInCtxt.context.world
        scene,_ = self._get_scene_timeline(nodesInCtxt.context)

        nodes_to_invalidate_delete = []
        nodes_to_invalidate_update = []
        for gRPCNode in nodesInCtxt.nodes:
            node = scene.node(gRPCNode.id)
            logger.info("<%s> deleted node <%s> in world <%s>" % \
                                (self._clientname(client_id), 
                                repr(node), 
                                world))

            action = self._delete_node(scene, gRPCNode.id)

            # tells everyone about the change
            logger.debug("Sent invalidation action [delete]")
            nodes_to_invalidate_delete.append(gRPCNode.id)

            # reparent children to the scene's root node
            children_to_update = []
            for child_id in node.children:
                child = scene.node(child_id)
                child.parent = scene.rootnode.id
                logger.debug("Reparenting child " + child_id + " to root node")
                nodes_to_invalidate_update.append(child_id)

            # Also remove the node from its parent's children
            parent = scene.node(node.parent)
            if parent:
                parent._children.remove(node.id)
                # tells everyone about the change to the parent
                logger.debug("Sent invalidation action [update " + parent.id + "] due to hierarchy update")
                nodes_to_invalidate_update.append(parent.id)

        if nodes_to_invalidate_update:
            self._emit_invalidation(gRPC.Invalidation.SCENE, world, nodes_to_invalidate_update, UPDATE)
        if nodes_to_invalidate_delete:
            self._emit_invalidation(gRPC.Invalidation.SCENE, world, nodes_to_invalidate_delete, DELETE)


        logger.debug("<deleteNodes> completed")
        return gRPC.Empty()


    ############ TIMELINES
    @profile
    def getSituationsLen(self, ctxt, context):
        logger.debug("Got <getSituationsLen> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        _,timeline = self._get_scene_timeline(ctxt)

        res = gRPC.Size(size=len(timeline.situations))
        logger.debug("<getSituationsLen> completed")
        return res

    @profile
    def getSituationsIds(self, ctxt, context):
        logger.debug("Got <getSituationsIds> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        _,timeline = self._get_scene_timeline(ctxt)

        situations = gRPC.Situations()
        for s in timeline.situations:
            situations.ids.append(s.id)

        logger.debug("<getSituationsIds> completed")
        return situations


    @profile
    def getSituation(self, sitInCtxt, context):
        logger.debug("Got <getSituation> from %s" % sitInCtxt.context.client)

        client_id, world = sitInCtxt.context.client, sitInCtxt.context.world

        _,timeline = self._get_scene_timeline(sitInCtxt.context)

        self._update_current_links(client_id, world, READER)

        if not sitInCtxt.situation.id:
            logger.warning("%s has required a situation without specifying its id!" % (self._clientname(client_id)))

            context.details("No situation id provided")
            context.code(beta_interfaces.StatusCode.NOT_FOUND)
            return gRPC.Node()


        situation = timeline.situation(sitInCtxt.situation.id)

        if not situation:
            logger.warning("%s has required an non-existant "
                           "situation <%s> in world %s" % (self._clientname(client_id), sitInCtxt.node.id, world))

            context.details("Situation <%s> does not exist in world %s" % (sitInCtxt.node.id, world))
            context.code(beta_interfaces.StatusCode.NOT_FOUND)
            return gRPC.Situation()


        else:
            res = situation.serialize(gRPC.Situation)
            logger.debug("<getSituation> completed")
            return res

    @profile
    def timelineOrigin(self, ctxt, context):
        logger.debug("Got <timelineOrigin> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        _,timeline = self._get_scene_timeline(ctxt)

        res = gRPC.Time(time=timeline.origin)
        logger.debug("<timelineOrigin> completed")
        return res

    @profile
    def updateSituations(self, sitInCtxt, context):
        logger.debug("Got <updateSituations> from %s" % sitInCtxt.context.client)
        self._update_current_links(sitInCtxt.context.client, sitInCtxt.context.world, PROVIDER)

        client_id, world = sitInCtxt.context.client, sitInCtxt.context.world
        _, timeline = self._get_scene_timeline(sitInCtxt.context)

        situations_to_invalidate_update = []
        situations_to_invalidate_new = []
        for gRPCSit in sitInCtxt.situations:


            situation = Situation.deserialize(gRPCSit)

            invalidation_type = self._update_situation(timeline, situation)

            logger.info("<%s> updated situation <%s> in world <%s>" % \
                                (self._clientname(client_id), 
                                repr(situation), 
                                world))


            logger.debug("Adding invalidation action [" + str(invalidation_type) + "]")

            if invalidation_type == UPDATE:
                situations_to_invalidate_update.append(situation.id)
            elif invalidation_type == NEW:
                situations_to_invalidate_new.append(situation.id)
            else:
                raise RuntimeError("Unexpected invalidation type")

        if situations_to_invalidate_update:
            self._emit_invalidation(gRPC.Invalidation.TIMELINE, world, situations_to_invalidate_update, UPDATE)
        if situations_to_invalidate_new:
            self._emit_invalidation(gRPC.Invalidation.TIMELINE, world, situations_to_invalidate_new, NEW)


        logger.debug("<updateSituations> completed")
        return gRPC.Empty()

    @profile
    def deleteSituations(self, sitInCtxt, context):
        logger.debug("Got <deleteSituations> from %s" % sitInCtxt.context.client)
        self._update_current_links(sitInCtxt.context.client, sitInCtxt.context.world, PROVIDER)

        client_id, world = sitInCtxt.context.client, sitInCtxt.context.world
        _, timeline = self._get_scene_timeline(sitInCtxt.context)

        situations_to_invalidate_delete = []
        for gRPCSit in sitInCtxt.situations:

            situation = Situation.deserialize(gRPCSit)

            timeline.remove(situation)

            logger.info("<%s> deleted situation <%s> in world <%s>" % \
                                (self._clientname(client_id), 
                                repr(situation), 
                                world))

            # tells everyone about the change
            logger.debug("Sent invalidation action [delete]")
            situations_to_invalidate_delete.append(situation.id)

        if situations_to_invalidate_delete:
            self._emit_invalidation(gRPC.Invalidation.TIMELINE, world, situations_to_invalidate_delete, DELETE)

        logger.debug("<deleteSituations> completed")
        return gRPC.Empty()

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

def start(port=50051, signaling_queue=None):
    """Starts the underworlds server in a thread on the given port and returns
    the resulting gRPC server.

    If signaling_queue is provided, the behaviour is blocking:
    it creates and start an underworlds server, then blocks until something is pushed onto the queue.
    It then properly closes the server and returns None.
    """

    desired_port=str(port)

    server = gRPC.beta_create_Underworlds_server(Server())
    port = server.add_insecure_port('[::]:%s' % desired_port)

    if port == 0:
        raise RuntimeError("The port %s is already in use! Underworlds server already running? "
                     "I can not start the server." % desired_port)

    logger.info("Starting the server...")
    server.start()
    time.sleep(0.2) # leave some time to the server to start
    logger.info("Server started.")

    if signaling_queue is None:
        return server
    else:
        # block on the queue
        signaling_queue.get()
        logger.info("uwds server exiting. Closing connections...")
        server.stop(1).wait()
        logger.info("uwds server closed.")

def start_process(port=50051):
    import multiprocessing

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=start, args=(port, q,))
    p.start()

    return p, q

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
