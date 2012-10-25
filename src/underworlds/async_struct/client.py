from mytypes import *

import zmq
import time
import json

from threading import Lock

context = zmq.Context()
print "Connecting to underworlds server..."
socket = context.socket(zmq.REQ)
socket.connect ("tcp://localhost:5555")



class NodesProxy(object):

    def __init__(self):

        socket.send("get_nodes_len")
        self._len = int(socket.recv())

        self._nodes = {} # node store

        # list of all node IDs that were once obtained.
        #They may be valid or invalid (if present in _invalid_ids)
        self._ids = []

        # list of invalid ids (ie, nodes that have remotely changed).
        # This list is updated asynchronously from a server publisher
        socket.send("get_nodes_ids")
        self._invalid_ids = json.loads(socket.recv())

        self.invalidate_lock = Lock()

        self._invalid_len = True



    def _on_new_node(self):
        # implement here listening for new or removed nodes
        # should update _len and _invalid_ids with the new one
        self.invalidate_lock.acquire()

        if id not in self._invalid_ids:
            self._invalid_ids.append(id)

        self.invalidate_lock.release()

        self._len += 1 # not atomic, but still fine since I'm the only one to write it
       
    def _on_changed_node(self, id):
        # implement here listening for changed node

        self.invalidate_lock.acquire()

        if id not in self._invalid_ids:
            self._invalid_ids.append(id)

        self.invalidate_lock.release()

    def _get_more_node(self):
        
        self.invalidate_lock.acquire()
        node = self._invalid_ids.pop()
        self.invalidate_lock.release()

        socket.send("get_node " + str(node))
        
        self._ids.append(node)
        data = json.loads(socket.recv())
        self._nodes[node] = Node(**data)


    def _update__node(self, id):

        socket.send("get_node " + str(id))

        data = json.loads(socket.recv())
        updated_node = Node(**data)
        self._nodes[id] = updated_node

        self.invalidate_lock.acquire()
        self._invalid_nodes.remove(id)
        self.invalidate_lock.release()

    def __getitem__(self, key):

        if type(key) is int:

            # not downloaded enough nodes yet?
            while key >= len(self._ids):
                self._get_more_node()

            id = self._ids[key]

            # did the node changed since the last time we obtained it?
            if id in self._invalid_ids:
                self._update_node(id)

            return self._nodes[id]

        else:
            raise TypeError()

    def __len__(self):
        return self._len

     
    def run(self):
        #implement here the listener for model updates

class Scene(object):

    def __init__(self):
        self.nodes = NodesProxy()


scene = Scene()

print(scene.nodes[0])
print(len(scene.nodes))

for n in scene.nodes:
    if n.name.startswith("abc"):
        print n
        break
