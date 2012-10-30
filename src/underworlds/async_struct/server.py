from mytypes import *

import zmq
import time
import json

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

invalidation = context.socket(zmq.PUB)
invalidation.bind ("tcp://*:5556")


nodes = [Node() for i in range(1000)]
print(nodes[0])

def get_node(id):
    for n in nodes:
        if n.id == id:
            return n

def change_node(node):

    # replace the node
    nodes = [node if old.id == node.id else old for old in nodes]
   
    # tells everyone about the change
    invalidation.send("invalidate " + node.id)

while True:
    # Wait for next request from client
    req = socket.recv().split()

    print "Received request: ", req

    name = req[0]

    if name == "get_nodes_len":
        socket.send(str(len(nodes)))
    elif name == "get_nodes_ids":
        socket.send(json.dumps([n.id for n in nodes]))
    elif name == "update_node":
        node = Node.deserialize(req[1])
        socket.send(get_node(id).serialize())
    elif name == "get_node":
        id = req[1]
        socket.send(get_node(id).serialize())
    else:
        print("Unknown request")
        socket.send(json.dumps("unknown request"))


