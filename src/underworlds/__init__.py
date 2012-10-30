
import zmq
import time
import json

from threading import *

import logging
netlogger = logging.getLogger("underworlds.network")
logger = logging.getLogger("underworlds.client")

from underworlds.types import World, Node


#TODO: inherit for a collections.MutableSequence? what is the benefit?
class NodesProxy(Thread):

    def __init__(self):
        Thread.__init__(self)

        self.context = zmq.Context()
        netlogger.debug("Connecting to underworlds server...")
        self.rpc = self.context.socket(zmq.REQ)
        self.rpc.connect ("tcp://localhost:5555")

        self.rpc.send("get_nodes_len")
        self._len = int(self.rpc.recv())

        self._nodes = {} # node store

        # list of all node IDs that were once obtained.
        # They may be valid or invalid (if present in _invalid_ids)
        self._ids = []

        # When I commit a node update, I get a notification from the
        # remote as any client. To prevent the reloading of the node I have
        # created myself, I store their ids in this list.
        self._ids_being_propagated = []

        # list of invalid ids (ie, nodes that have remotely changed).
        # This list is updated asynchronously from a server publisher
        self.rpc.send("get_nodes_ids")
        self._invalid_ids = json.loads(self.rpc.recv())

        self.invalidate_lock = Lock()

        self._running = True
        import pdb;pdb.set_trace()
        self.start()


    def __del__(self):
        self._running = False
        
    def _on_remotely_updated_node(self, id):
        # implement here listening for changed node

        self.invalidate_lock.acquire()

        if id not in self._invalid_ids:
            self._invalid_ids.append(id)

        self.invalidate_lock.release()

    def _get_more_node(self):
        
        if not self._invalid_ids:
            # release the lock
            logger.debug("Waiting for new/updated nodes notifications...")
            time.sleep(0.01) #leave some time for propagation

            # still empty? we have a problem!
            if not self._invalid_ids:
                logger.error("Inconsistency detected! The server has not"\
                             " notified all the nodes updates. Or the "\
                             "IPC transport is really slow.")
                raise Exception()

        self.invalidate_lock.acquire()
        # here, _invalid_ids is not empty. It should not raise an exception
        id = self._invalid_ids.pop()
        self.invalidate_lock.release()

        self.rpc.send("get_node " + str(id))
        
        self._ids.append(id)
        data = self.rpc.recv()
        self._nodes[id] = Node.deserialize(data)


    def _update_node_from_remote(self, id):

        self.rpc.send("get_node " + id)

        data = self.rpc.recv()
        updated_node = Node.deserialize(data)
        self._nodes[id] = updated_node

        self.invalidate_lock.acquire()
        try:
            self._invalid_ids.remove(id)
        except ValueError as ve:
            raise ve
        finally:
            self.invalidate_lock.release()

    def __getitem__(self, key):

        if type(key) is int:

            # not downloaded enough nodes yet?
            while key >= len(self._ids):
                self._get_more_node()

            id = self._ids[key]

            # did the node changed since the last time we obtained it?
            if id in self._invalid_ids:
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
        """
        id = node.id
        self.rpc.send("update_node " + id)
        self.rpc.recv() # server send a "get_node"
        self.rpc.send(node.serialize())
        self.rpc.recv() # server send a "ack"


    def run(self):
        #implement here the listener for model updates
        invalidation_pub = self.context.socket(zmq.SUB)
        invalidation_pub.connect ("tcp://localhost:5556")
        invalidation_pub.setsockopt(zmq.SUBSCRIBE, "") # no filter

        poller = zmq.Poller()
        poller.register(invalidation_pub, zmq.POLLIN)

        while self._running:
            socks = dict(poller.poll(200))
            
            if socks.get(invalidation_pub) == zmq.POLLIN:
                action, id = invalidation_pub.recv().split()
                if action == "update":
                    netlogger.debug("Updated node: " + id)
                    self._on_remotely_updated_node(id)
                elif action == "new":
                    netlogger.debug("New node: " + id)
                    self._len += 1 # not atomic, but still fine since I'm the only one to write it
                    self._on_remotely_updated_node(id)



class WorldsProxy:

    def __getitem__(self, key):
        world = World(key)
        world.scene.nodes = NodesProxy()
        return world

    def __setitem__(self, key, world):
        pass

class Context(object):

    def __init__(self, name):

        self.name = name

        self.worlds = WorldsProxy()

    def __repr__(self):
        return "Underworlds context for " + self.name
