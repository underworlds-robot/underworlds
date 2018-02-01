
import os # for the UWDS_SERVER environment variable
import sys

import time
import copy
import threading
import random

from collections import deque

import logging
logger = logging.getLogger("underworlds.client")

from grpc.beta import implementations
from grpc.framework.interfaces.face.face import ExpirationError,NetworkError,AbortionError
import underworlds.underworlds_pb2 as gRPC

from underworlds.types import World, Node, Situation, MeshData

from underworlds.helpers.profile import profile, profileonce

_TIMEOUT_SECONDS = 1
_TIMEOUT_SECONDS_MESH_LOADING = 20

#TODO: inherit for a collections.MutableSequence? what is the benefit?
class NodesProxy:

    def __init__(self, context, world):

        self._ctx = context # current underworlds context (useful to know the client name)
        self._world = world

        # This contains the tuple (id, world) and is used for identification
        # when communicating with the server
        self._server_ctx = gRPC.Context(client=self._ctx.id, world=self._world.name)

        self._len = self._ctx.rpc.getNodesLen(self._server_ctx, _TIMEOUT_SECONDS).size

        self._nodes = {} # node store

        # list of all node IDs that were once obtained.
        # They may be valid or invalid (if present in _updated_ids)
        self._ids = []

        # list of invalid ids (ie, nodes that have remotely changed).
        # This list is updated asynchronously from a server publisher
        self._updated_ids = deque(self._ctx.rpc.getNodesIds(self._server_ctx, _TIMEOUT_SECONDS).ids)

        self._deleted_ids = deque()

        # holds futures for non-blocking RPC calls when updating/removing nodes
        self.update_future = None
        self.remove_future = None

        # Get the root node
        self.rootnode = self._ctx.rpc.getRootNode(self._server_ctx, _TIMEOUT_SECONDS).id
        self._update_node_from_remote(self.rootnode)
 
        self.waitforchanges_cv = threading.Condition()
        self.lastchange = None

    @profile
    def _on_remotely_updated_nodes(self, ids):

        for id in ids:
            if id not in self._updated_ids:
                self._updated_ids.append(id)

        with self.waitforchanges_cv:
            self.lastchange = (ids, gRPC.Invalidation.UPDATE)
            self.waitforchanges_cv.notify_all()


    @profile
    def _on_remotely_added_nodes(self, ids):

        self._len += len(ids)

        for id in ids:
            if id not in self._updated_ids:
                self._updated_ids.append(id)

        with self.waitforchanges_cv:
            self.lastchange = (ids, gRPC.Invalidation.NEW)
            self.waitforchanges_cv.notify_all()


    @profile
    def _on_remotely_deleted_nodes(self, ids):

        self._len -= len(ids)
        self._deleted_ids.extend(ids)

        with self.waitforchanges_cv:
            self.lastchange = (ids, gRPC.Invalidation.DELETE)
            self.waitforchanges_cv.notify_all()


    def _get_more_node(self):
        
        if not self._updated_ids:
            logger.warning("Slow propagation? Waiting for new/updated nodes notifications...")
            time.sleep(0.05) #leave some time for propagation

            # still empty? we have a problem!
            if not self._updated_ids:
                logger.error("Inconsistency detected! The server has not"\
                             " notified all the nodes updates. Or the "\
                             "IPC transport is really slow.")
                raise Exception()

        # here, _updated_ids is not empty. It should not raise an exception
        id = self._updated_ids.pop()

        self._get_node_from_remote(id)

    def _get_node_from_remote(self, id):

        nodeInCtxt = gRPC.NodeInContext(context=self._server_ctx,
                                        node=gRPC.Node(id=id))
        try:
            gRPCNode = self._ctx.rpc.getNode(nodeInCtxt, _TIMEOUT_SECONDS)
        except AbortionError as e:
            raise IndexError(e.details)

        # is it a new node, or rather an update to an existing one?
        if id not in self._ids:
            self._ids.append(id)

        self._nodes[id] = Node.deserialize(gRPCNode)


    def _update_node_from_remote(self, id):

        self._get_node_from_remote(id)

        self._updated_ids.remove(id)

    def __getitem__(self, key):

        # First, a bit of house keeping
        # do we have pending nodes to delete?
        if self._deleted_ids:
            tmp = copy.copy(self._deleted_ids)
            for id in tmp:
                try:
                    self._ids.remove(id)
                    del(self._nodes[id])
                    self._deleted_ids.remove(id)
                except ValueError:
                    logger.warning("The node %s is already removed. Feels like a synchro issue..." % id)

        # Then, let see what the user want:
        if type(key) is int:

            # First, are we over the length of our node list?
            if key >= self._len:
                raise IndexError

            # not downloaded enough nodes yet?
            while key >= len(self._ids):
                self._get_more_node()

            id = self._ids[key]

            # did the node changed since the last time we obtained it?
            if id in self._updated_ids:
                self._update_node_from_remote(id)

            return self._nodes[id]

        else: #assume it's a node ID

            if key in self._ids:
                # did the node changed since the last time we obtained it?
                if key in self._updated_ids:
                        self._update_node_from_remote(key)
                return self._nodes[key]
            elif key in self._updated_ids:
                self._update_node_from_remote(key)
                return self._nodes[key]
            else: # we do not have this node locally. Let's try to fetch it
                try:
                    self._get_node_from_remote(key)
                except ValueError:
                    #The node does not exist!!
                    raise KeyError("The node ID %s does not exist" % key)
                return self._nodes[key]

    def __len__(self):
        return self._len

    def append(self, nodes):
        """ Adds one or several new nodes to the node set.

        It is actually an alias for NodesProxy.update: all the restrictions
        regarding ordering or propagation time apply as well.

        :param nodes: a single node instance, or a sequence of node instances.
        """
        return self.update(nodes)

    @profile
    def update(self, nodes):
        """ Update the value of one or several nodes in the node set.
        If the node(s) do(es) not exist yet, add them.

        This method sends the new/updated nodes to the
        remote. IT DOES NOT DIRECTLY modify the local
        copy of nodes: the roundtrip is slower, but data
        consistency is easier to ensure.

        This means that if you create or update a node, the
        node won't be created/updated immediately. It will 
        take some time (a couple of milliseconds) to propagate
        the change.

        Also, you have no guarantee regarding the ordering:

        for instance,

        >>> nodes.update(n1)
        >>> nodes.update(n2)

        does not mean that nodes[0] = n1 and nodes[1] = n2.
        This is due to the lazy access process.

        However, once accessed once, nodes keep their index (until a
        node with a smaller index is removed).

        :param nodes: a single node instance, or a sequence of node instances.
        """

        # if for some reason, the previous non-blocking call to update the node is
        # not yet complete, finish it now
        if self.update_future is not None:
            self.update_future.result()

        if not isinstance(nodes, list):
            nodes = [nodes]

        gRPCNodes = [node.serialize(gRPC.Node) for node in nodes]

        self.update_future = self._ctx.rpc.updateNodes.future(
                                 gRPC.NodesInContext(context=self._server_ctx,
                                                     nodes=gRPCNodes),
                                 _TIMEOUT_SECONDS)

    @profile
    def remove(self, nodes):
        """ Deletes one or several nodes from the node set.

        THIS METHOD DOES NOT DIRECTLY delete the local
        copy of the nodes: it tells instead the server to
        delete these nodes for all clients.
        The roundtrip is slower, but data consistency is easier to ensure.

        This means that if you delete a node, the
        node won't be actually deleted immediately. It will 
        take some time (a couple of milliseconds) to propagate
        the change.

        If the deleted node(s) have children, the children are reparented to
        the root node.

        :param nodes: a single node instance, or a sequence of node instances.
        """
        # if for some reason, the previous non-blocking call to delete the node is
        # not yet complete, finish it now
        if self.remove_future is not None:
            self.remove_future.result()

        if not isinstance(nodes, list):
            nodes = [nodes]

        gRPCNodes = [node.serialize(gRPC.Node) for node in nodes]

        self.remove_future = self._ctx.rpc.deleteNodes.future(
                                 gRPC.NodesInContext(context=self._server_ctx,
                                                    nodes=gRPCNodes),
                                 _TIMEOUT_SECONDS)


class SceneProxy(object):

    def __init__(self, ctx, world):

        self._ctx = ctx # context

        self.nodes = NodesProxy(self._ctx, world)

    @property
    def rootnode(self):
        return self.nodes[self.nodes.rootnode]

    def waitforchanges(self, timeout = None):
        """ This method blocks until either the scene has
        been updated (a node has been either updated, 
        added or removed) or the timeout is over.

        :param timeout: timeout in seconds (float value)
        :returns: the change that occured as a pair [[node ids], operation]
        (operation is one of gRPC.Invalidation.UPDATE,
        gRPC.Invalidation.NEW, gRPC.Invalidation.DELETE) or None if the
        timeout has been reached.
        """
        lastchange = None
        with self.nodes.waitforchanges_cv:
            self.nodes.waitforchanges_cv.wait(timeout)
            lastchange = self.nodes.lastchange
            self.nodes.lastchange = None

        profileonce("client.scene.waitforchanges notified")

        return lastchange


    def nodebyname(self, name):
        """ Returns a list of node that have the given name (or [] if no node has this name)
        """
        nodes = []
        for n in self.nodes:
            if n.name == name:
                nodes.append(n)
        return nodes

    def append_and_propagate(self, nodes):
        """An alias for NodesProxy.append
        """
        self.nodes.append(nodes)

    def update_and_propagate(self, nodes):
        """An alias for NodesProxy.update
        """
        self.nodes.update(nodes)

    def remove_and_propagate(self, nodes):
        """An alias for NodesProxy.remove
        """
        self.nodes.remove(nodes)


class TimelineProxy:

    def __init__(self, ctx, world):

        self._ctx = ctx # context
        self._world = world

        # This contains the tuple (id, world) and is used for identification
        # when communicating with the server
        self._server_ctx = gRPC.Context(client=self._ctx.id, world=self._world.name)

        self._len = self._ctx.rpc.getSituationsLen(self._server_ctx, _TIMEOUT_SECONDS).size

        self._situations = {}

        # list of all node IDs that were once obtained.
        # They may be valid or invalid (if present in _updated_ids)
        self._ids = []

        # list of invalid ids (ie, nodes that have remotely changed).
        # This list is updated asynchronously from a server publisher
        self._updated_ids = deque(self._ctx.rpc.getSituationsIds(self._server_ctx, _TIMEOUT_SECONDS).ids)

        self._deleted_ids = deque()

        # holds futures for non-blocking RPC calls when updating/removing nodes
        self.update_future = None
        self.remove_future = None


        self.origin = self._ctx.rpc.timelineOrigin(self._server_ctx, _TIMEOUT_SECONDS).time
        logger.info("Accessing world <%s> (initially created on  %s)"%(self._world.name, time.asctime(time.localtime(self.origin))))

        self.waitforchanges_cv = threading.Condition()
        self.lastchange = None

    @profile
    def _on_remotely_updated_situations(self, ids):

        for id in ids:
            if id not in self._updated_ids:
                self._updated_ids.append(id)

        with self.waitforchanges_cv:
            self.lastchange = (ids, gRPC.Invalidation.UPDATE)
            self.waitforchanges_cv.notify_all()

    @profile
    def _on_remotely_added_situations(self, ids):


        self._len += len(ids)

        for id in ids:
            if id not in self._updated_ids:
                self._updated_ids.append(id)

        with self.waitforchanges_cv:
            self.lastchange = (ids, gRPC.Invalidation.NEW)
            self.waitforchanges_cv.notify_all()


    @profile
    def _on_remotely_deleted_situations(self, ids):

        self._len -= len(ids)
        self._deleted_ids.extend(ids)

        with self.waitforchanges_cv:
            self.lastchange = (ids, gRPC.Invalidation.DELETE)
            self.waitforchanges_cv.notify_all()

    def _get_more_situations(self):
        
        if not self._updated_ids:
            logger.warning("Slow propagation? Waiting for new/updated situations notifications...")
            time.sleep(0.05) #leave some time for propagation

            # still empty? we have a problem!
            if not self._updated_ids:
                logger.error("Inconsistency detected! The server has not"\
                             " notified all the situations updates. Or the "\
                             "IPC transport is really slow.")
                raise Exception()

        # here, _updated_ids is not empty. It should not raise an exception
        id = self._updated_ids.pop()

        self._get_situation_from_remote(id)

    def _get_situation_from_remote(self, id):

        sitInCtxt = gRPC.SituationInContext(context=self._server_ctx,
                                        situation=gRPC.Situation(id=id))
        try:
            gRPCSituation = self._ctx.rpc.getSituation(sitInCtxt, _TIMEOUT_SECONDS)
        except AbortionError as e:
            raise IndexError(e.details)

        # is it a new situation, or rather an update to an existing one?
        if id not in self._ids:
            self._ids.append(id)

        self._situations[id] = Situation.deserialize(gRPCSituation)

    def _update_situation_from_remote(self, id):

        self._get_situation_from_remote(id)

        self._updated_ids.remove(id)

    def __contains__(self, situation):
        try:
            self[situation.id]
            return True
        except KeyError:
            return False
        

    def __getitem__(self, key):

        # First, a bit of house keeping
        # do we have pending situations to delete?
        if self._deleted_ids:
            tmp = copy.copy(self._deleted_ids)
            for id in tmp:
                try:
                    self._ids.remove(id)
                    del(self._situations[id])
                    self._deleted_ids.remove(id)
                except ValueError:
                    logger.warning("The situation %s is already removed. Feels like a synchro issue..." % id)

        # Then, let see what the user want:
        if type(key) is int:

            # First, are we over the length of our situation list?
            if key >= self._len:
                raise IndexError

            # not downloaded enough nodes yet?
            while key >= len(self._ids):
                self._get_more_situations()

            id = self._ids[key]

            # did the situation changed since the last time we obtained it?
            if id in self._updated_ids:
                self._update_situation_from_remote(id)

            return self._situations[id]

        else: #assume it's a situation ID

            if key in self._ids:
                # did the situation changed since the last time we obtained it?
                if key in self._updated_ids:
                        self._update_situation_from_remote(key)
                return self._situations[key]
            elif key in self._updated_ids:
                self._update_situation_from_remote(key)
                return self._situations[key]
            else: # we do not have this situation locally. Let's try to fetch it
                try:
                    self._get_situation_from_remote(key)
                except ValueError:
                    #The situation does not exist!!
                    raise KeyError("The situation ID %s does not exist" % key)
                return self._situations[key]

    def __len__(self):
        return self._len

    def __repr__(self):
        return "TimelineProxy %s" % [str(s) for s in self._situations]

    def start(self):
        """ Starts (and return) a new situation

        This method sends the new situation to the
        remote. IT DOES NOT DIRECTLY modify the local
        copy of situations: the roundtrip is slower, but data
        consistency is easier to ensure.

        Note that the situation starting time is set by the client, at the time
        at which this method is called.
        """
        situation = Situation()
        situation.starttime = time.time()
        self.update(situation)
        return situation

    def end(self, situation):
        """ Ends an existing situation

        This method sends the situation update to the
        remote. IT DOES NOT DIRECTLY modify the local
        copy of situations: the roundtrip is slower, but data
        consistency is easier to ensure.

        Note that the situation ending time is set by the client, at the time
        at which this method is called.
        """
        if situation.isevent():
            return situation
        situation.endtime = time.time()
        self.update(situation)
        return situation

    def event(self):
        """ Creates (and return) a new event (situation with 0 duration)

        This method sends the new event to the
        remote. IT DOES NOT DIRECTLY modify the local
        copy of situations: the roundtrip is slower, but data
        consistency is easier to ensure.

        Note that the event time is set by the client, at the time
        at which this method is called.
        """
        situation = Situation()
        situation.starttime = time.time()
        situation.endtime = situation.starttime
        self.update(situation)
        return situation

    def append(self, situations):
        """ Adds one or several new situations to the timeline.

        It is actually an alias for TimelineProxy.update: all the restrictions
        regarding ordering or propagation time apply as well.

        :param situations: a single situation instance, or a sequence of situation instances.
        """
        return self.update(situations)


    @profile
    def update(self, situations):
        """ Update the value of a situation.
        If the situation does not exist yet, add it.

        This method sends the new/updated situations to the
        remote. IT DOES NOT DIRECTLY modify the local
        copy of situations: the roundtrip is slower, but data
        consistency is easier to ensure.

        This means that if you create or update a situation, the
        situation won't be created/updated immediately. It will 
        take some time (a couple of milliseconds) to propagate
        the change.

        Also, you have no guarantee regarding the ordering:

        for instance,

        >>> timeline.update(sit1)
        >>> timeline.update(sit2)

        does not mean that timeline[0] = sit1 and timeline[1] = sit2.
        This is due to the lazy access process.

        However, once accessed once, situations keep their index (until a
        situation with a smaller index is removed).

        :param situations: a single situation instance, or a sequence of situation instances.
        """

        # if for some reason, the previous non-blocking call to update the situation is
        # not yet complete, finish it now
        if self.update_future is not None:
            self.update_future.result()

        if not isinstance(situations, list):
            situations = [situations]

        gRPCSituations = [situation.serialize(gRPC.Situation) for situation in situations]

        self.update_future = self._ctx.rpc.updateSituations.future(
                                 gRPC.SituationsInContext(context=self._server_ctx,
                                                    situations=gRPCSituations),
                                 _TIMEOUT_SECONDS)

    @profile
    def remove(self, situations):
        """ Deletes one or several situations.

        THIS METHOD DOES NOT DIRECTLY delete the local
        copy of the situations: it tells instead the server to
        delete this situation for all clients.
        the roundtrip is slower, but data consistency is easier to ensure.

        This means that if you delete a situation, the
        situation won't be actually deleted immediately. It will 
        take some time (a couple of milliseconds) to propagate
        the change.

        :param situations: a single situation instance, or a sequence of situation instances.
        """
        # if for some reason, the previous non-blocking call to delete the situation is
        # not yet complete, finish it now
        if self.remove_future is not None:
            self.remove_future.result()

        if not isinstance(situations, list):
            situations = [situations]

        gRPCSituations = [situation.serialize(gRPC.Situation) for situation in situations]

        self.remove_future = self._ctx.rpc.deleteSituations.future(
                                 gRPC.SituationsInContext(context=self._server_ctx,
                                                          situations=gRPCSituations),
                                 _TIMEOUT_SECONDS)


    def waitforchanges(self, timeout = None):
        """ This method blocks until either the timeline has
        been updated (a situation has been either started or
        ended) or the timeout is over.

        :param timeout: timeout in seconds (float value)

        :returns: the change that occured as a pair [[node ids], operation]
        (operation is one of gRPC.Invalidation.UPDATE,
        gRPC.Invalidation.NEW, gRPC.Invalidation.DELETE) or None if the
        timeout has been reached.
        """
        lastchange = None
        with self.waitforchanges_cv:
            self.waitforchanges_cv.wait(timeout)
            lastchange = self.lastchange
            self.lastchange = None

        profileonce("client.timeline.waitforchanges notified")

        return lastchange



class WorldProxy:

    def __init__(self, ctx, name):
    
        if not (isinstance(name, str) or isinstance(name, unicode)):
            raise TypeError("A world proxy must be initialized "
                            "with a string as name. Got %s instead." % type(name))

        self._ctx = ctx # context

        self._world = World(name)

        self.name = name
        self.scene = SceneProxy(self._ctx, self._world)
        self.timeline = TimelineProxy(self._ctx, self._world)

    def copy_from(self, world):
        """ Creates and/or replaces the content of the world with an exact copy
        of the given `world`.
        """
        req = {"client":self._ctx.id,
               "world": self._world.name,
               "req": "deepcopy %s" % (world.name)}

        self._ctx.rpc.send_json(req)
        self._ctx.rpc.recv() #ack

    def __str__(self):
        return self.name

class WorldsProxy:

    def __init__(self, ctx):

        self._ctx = ctx # context

        self._worlds = []

    def __getitem__(self, key):
        for world in self._worlds:
            if world.name == key:
                return world

        world = WorldProxy(self._ctx, key)
        self._worlds.append(world)
        return world

    def __setitem__(self, key, world):
        logger.error("Can not set a world")
        pass

    def __iter__(self):
        """To iterate over the existing worlds, first ask the server
        an up-to-date list of worlds, and yield worlds as much as needed.
        Doing so, worlds are lazily created.
        """
        topo = self._ctx.rpc.topology(gRPC.Client(id=self._ctx.id), _TIMEOUT_SECONDS)
        for world in topo.worlds:
            yield self.__getitem__(world)

class InvalidationServer(gRPC.BetaUnderworldsInvalidationServicer):

    def __init__(self, ctx):
        self.ctx=ctx

    @profile
    def emitInvalidation(self, invalidation, context):
        logger.info("Got <emitInvalidation> for world <%s>" % invalidation.world)
       
        target, action, world, ids = invalidation.target, invalidation.type, invalidation.world, invalidation.ids

        if target == gRPC.Invalidation.SCENE:
            if action == gRPC.Invalidation.UPDATE:
                logger.debug("Server notification: nodes updated: " + str(ids))
                self.ctx.worlds[world].scene.nodes._on_remotely_updated_nodes(ids)
            elif action == gRPC.Invalidation.NEW:
                logger.debug("Server notification: nodes added: " + str(ids))
                self.ctx.worlds[world].scene.nodes._on_remotely_added_nodes(ids)
            elif action == gRPC.Invalidation.DELETE:
                logger.debug("Server notification: nodes deleted: " + str(ids))
                self.ctx.worlds[world].scene.nodes._on_remotely_deleted_nodes(ids)
            else:
                raise RuntimeError("Unexpected invalidation action")

        elif target == gRPC.Invalidation.TIMELINE:
            if action == gRPC.Invalidation.UPDATE:
                logger.debug("Server notification: situations updated: " + str(ids))
                self.ctx.worlds[world].timeline._on_remotely_updated_situations(ids)
            elif action == gRPC.Invalidation.NEW:
                logger.debug("Server notification: situations added: " + str(ids))
                self.ctx.worlds[world].timeline._on_remotely_added_situations(ids)
            elif action == gRPC.Invalidation.DELETE:
                logger.debug("Server notification: situations deleted: " + str(ids))
                self.ctx.worlds[world].timeline._on_remotely_deleted_situations(ids)
            else:
                raise RuntimeError("Unexpected invalidation action")
        else:
            raise RuntimeError("Unexpected invalidation target")

        return gRPC.Empty()


class Context(object):

    def __init__(self, name, host="localhost",port=50051):

        self.name = name
        self.worlds = WorldsProxy(self)

        self.invalidation_port = 0

        while self.invalidation_port == 0:
            invalidation_port = random.randint(port + 1,60000)
            logger.info("Creating my own invalidation server on port %s..." % (invalidation_port))

            self.invalidation_server = gRPC.beta_create_UnderworldsInvalidation_server(InvalidationServer(self))
            self.invalidation_port = self.invalidation_server.add_insecure_port('[::]:%d' % invalidation_port)

            if self.invalidation_port == 0:
                logger.error("The port for my invalidation server is already in use! Trying another one...")


        self.invalidation_server.start()

        logger.info("Invalidation server created")


        if "UWDS_SERVER" in os.environ and os.environ["UWDS_SERVER"] != "":
            if ":" in os.environ["UWDS_SERVER"]:
                host, port = os.environ["UWDS_SERVER"].split(":")
                port = int(port)
            else:
                host = os.environ["UWDS_SERVER"]

        logger.info("Connecting to the underworlds server on %s:%s..." % (host, port))


        try:
            channel = implementations.insecure_channel(host, port)
            self.rpc = gRPC.beta_create_Underworlds_stub(channel)

            self.id = self.rpc.helo(gRPC.Welcome(name=name,
                                                 host="localhost", 
                                                 invalidation_server_port=self.invalidation_port), _TIMEOUT_SECONDS).id
        except NetworkError as e:
            logger.fatal("Underworld server unreachable on %s:%d! Is it started?\n"
                         "Set UWDS_SERVER=host:port if underworlded is running on a different machine.\n"
                         "Original error: %s" % (host, port, str(e)))
            sys.exit(1)
        except AbortionError as e:
            logger.fatal("Underworld server refused connection on %s:%d.\n"
                         "Original error: %s" % (host, port, str(e)))
            sys.exit(1)

        logger.info("<%s> connected to the underworlds server." % self.name)


    def reset(self):
        """ Hard reset of Underworlds: all the worlds are deleted.
        The existing mesh database is kept, however.
        This does not impact the list of known clients (ie, clients do not have to
        call 'helo' again).
        """
        self.rpc.reset(gRPC.Client(id=self.id), _TIMEOUT_SECONDS)


    def topology(self):
        """Returns the current topology to the underworlds environment.

        It returns an object with two members:
        - 'worlds': the list of all worlds' names known to the system
        - 'clients': the list of known clients. Each client is an object with
          the following members:
          - client.id
          - client.name
          - client.links: a list of the 'links' between this client and the
            worlds. Each link has the following members:
            - link.world
            - link.type: `READER`, `PROVIDER`, `FILTER`, `MONITOR`, see `types.py`
            - link.last_activity: the timestamp of the last time this link has been used
        """
        return self.rpc.topology(gRPC.Client(id=self.id), _TIMEOUT_SECONDS)

    def uptime(self):
        """Returns the server uptime in seconds.
        """
        return self.rpc.uptime(gRPC.Client(id=self.id),_TIMEOUT_SECONDS).time

    def has_mesh(self, id):
        ok = self.rpc.hasMesh(gRPC.MeshInContext(client=gRPC.Client(id=self.id),
                                                   mesh=gRPC.Mesh(id=id)),
                              _TIMEOUT_SECONDS)
        return ok.value

    def mesh(self, id):
        mesh = self.rpc.getMesh(gRPC.MeshInContext(client=gRPC.Client(id=self.id),
                                                   mesh=gRPC.Mesh(id=id)),
                              _TIMEOUT_SECONDS_MESH_LOADING)
        return MeshData.deserialize(mesh)

    def push_mesh(self, mesh):

        starttime = time.time()
        try:
            self.rpc.pushMesh(gRPC.MeshInContext(client=gRPC.Client(id=self.id),
                                             mesh=mesh.serialize(gRPC.Mesh)),
                              _TIMEOUT_SECONDS_MESH_LOADING)
        except ExpirationError:
            logger.error("Timeout while trying to push a mesh to the server!")

        logger.info("Pushed mesh <%s> in %.2fsec" % (mesh.id, time.time() - starttime))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        logger.info("Closing context [%s]..." % self.name)
        self.rpc.byebye(gRPC.Client(id=self.id), _TIMEOUT_SECONDS)
        self.invalidation_server.stop(1).wait()
        logger.info("The context [%s] is now closed." % self.name)

    def __repr__(self):
        return "Underworlds context for " + self.name
