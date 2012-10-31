
import zmq
import time
import json
import copy

import threading
from collections import deque

import logging
netlogger = logging.getLogger("underworlds.network")
logger = logging.getLogger("underworlds.client")

from underworlds.types import World, Node


#TODO: inherit for a collections.MutableSequence? what is the benefit?
class NodesProxy(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.context = zmq.Context()
        netlogger.debug("Connecting to underworlds server...")
        self.rpc = self.context.socket(zmq.REQ)
        self.rpc.connect ("tcp://localhost:5555")

        self.rpc.send("get_nodes_len")
        self._len = int(self.rpc.recv())

        self._nodes = {} # node store

        # list of all node IDs that were once obtained.
        # They may be valid or invalid (if present in _updated_ids)
        self._ids = []

        # When I commit a node update, I get a notification from the
        # remote as any client. To prevent the reloading of the node I have
        # created myself, I store their ids in this list.
        self._ids_being_propagated = []

        # list of invalid ids (ie, nodes that have remotely changed).
        # This list is updated asynchronously from a server publisher
        self.rpc.send("get_nodes_ids")
        self._updated_ids = deque(json.loads(self.rpc.recv()))

        self._deleted_ids = deque()


        self._running = True
        self.cv = threading.Condition()

        self.start()

        # wait for the 'invalidation' thread to notify it is ready
        self.cv.acquire()
        self.cv.wait()
        self.cv.release()


    def __del__(self):
        self._running = False

    def _on_remotely_updated_node(self, id):

        if id not in self._updated_ids:
            self._updated_ids.append(id)


    def _on_remotely_deleted_node(self, id):

        self._len -= 1 # not atomic, but still fine since I'm the only one to write it
        self._deleted_ids.append(id)

    def _get_more_node(self):
        
        if not self._updated_ids:
            # release the lock
            logger.warning("Slow propagation? Waiting for new/updated nodes notifications...")
            time.sleep(0.01) #leave some time for propagation

            # still empty? we have a problem!
            if not self._updated_ids:
                logger.error("Inconsistency detected! The server has not"\
                             " notified all the nodes updates. Or the "\
                             "IPC transport is really slow.")
                raise Exception()

        # here, _updated_ids is not empty. It should not raise an exception
        id = self._updated_ids.pop()

        self.rpc.send("get_node " + str(id))
        
        self._ids.append(id)
        data = self.rpc.recv()
        self._nodes[id] = Node.deserialize(data)


    def _update_node_from_remote(self, id):

        self.rpc.send("get_node " + id)

        data = self.rpc.recv()
        updated_node = Node.deserialize(data)
        self._nodes[id] = updated_node

        try:
            self._updated_ids.remove(id)
        except ValueError as ve:
            raise ve

    def __getitem__(self, key):

        if type(key) is int:

            # First, are we over the lenght of our node list?
            if key >= self._len:
                raise IndexError

            # Then, do we have pending nodes to delete?
            if self._deleted_ids:
                tmp = copy.copy(self._deleted_ids)
                for id in tmp:
                    try:
                        self._ids.remove(id)
                        del(self._nodes[id])
                    except ValueError:
                        logger.warning("The node %s is already removed. Feels like a synchro issue..." % id)

            # not downloaded enough nodes yet?
            while key >= len(self._ids):
                self._get_more_node()

            id = self._ids[key]

            # did the node changed since the last time we obtained it?
            if id in self._updated_ids:
                self._update_node_from_remote(id)

            return self._nodes[id]

        else:
            raise TypeError()

    def __len__(self):
        return self._len

    def update(self, node):
        """ Update the value of a node in the node set.
        If the node does not exist yet, add it.

        This method sends the new/updated node to the
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
        node which a smaller index is removed).

        """
        self.rpc.send("update_node " + node.serialize())
        self.rpc.recv() # server send a "ack"

    def remove(self, node):
        """ Deletes a node from the node set.

        THIS METHOD DOES NOT DIRECTLY delete the local
        copy of the node: it tells instead the server to
        delete this node for all clients.
        the roundtrip is slower, but data consistency is easier to ensure.

        This means that if you delete a node, the
        node won't be actually deleted immediately. It will 
        take some time (a couple of milliseconds) to propagate
        the change.
        """
        self.rpc.send("delete_node " + node.id)
        self.rpc.recv() # server send a "ack"



    def run(self):
        #implement here the listener for model updates
        invalidation_pub = self.context.socket(zmq.SUB)
        invalidation_pub.connect ("tcp://localhost:5556")
        invalidation_pub.setsockopt(zmq.SUBSCRIBE, "") # no filter

        # wait until we receive something on the 'invalidation'
        # channel. This makes sure we wont miss any following
        # message
        self.cv.acquire()
        invalidation_pub.recv()
        self.cv.notify_all()
        self.cv.release()

        poller = zmq.Poller()
        poller.register(invalidation_pub, zmq.POLLIN)

        while self._running:
            socks = dict(poller.poll(200))
            
            if socks.get(invalidation_pub) == zmq.POLLIN:
                action, id = invalidation_pub.recv().split()
                if action == "update":
                    netlogger.debug("Request to update node: " + id)
                    self._on_remotely_updated_node(id)
                elif action == "new":
                    netlogger.debug("Request to add node: " + id)
                    self._len += 1 # not atomic, but still fine since I'm the only one to write it
                    self._on_remotely_updated_node(id)
                elif action == "delete":
                    netlogger.debug("Request to delete node: " + id)
                    self._on_remotely_deleted_node(id)
                elif action == "nop":
                    pass



class WorldsProxy:

    def __init__(self):
        self._worlds = []

    def __getitem__(self, key):
        world = World(key)
        self._worlds.append(world)
        world.scene.nodes = NodesProxy()
        return world

    def __setitem__(self, key, world):
        pass

    def finalize(self):
        for w in self._worlds:
            logger.info("Closing world " + w.name)
            w.scene.nodes._running = False
            w.scene.nodes.join()

class Context(object):

    def __init__(self, name):

        self.name = name

        self.worlds = WorldsProxy()

    def __del__(self):
        self.worlds.finalize()

    def __enter__(self):
        return self

    def __exit__(self):
        pass

    def __repr__(self):
        return "Underworlds context for " + self.name
