from mytypes import *

import zmq
import time
import json
import copy
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")


nodes = [Node() for i in range(1000)]
print(nodes[0])

def get_node(id):
    for n in nodes:
        if n.id == id:
            return n

def tojson(n):
    d = copy.copy(n.__dict__)
    d["value"] = d["value"].tolist()
    return json.dumps(d)

while True:
    # Wait for next request from client
    req = socket.recv().split()

    print "Received request: ", req

    name = req[0]

    if name == "get_nodes_len":
        socket.send(str(len(nodes)))
    elif name == "get_nodes_ids":
        socket.send(json.dumps([n.id for n in nodes]))
    elif name == "get_node":
        id = req[1]
        socket.send(tojson(get_node(id)))
    else:
        print("Unknown request")
        socket.send(json.dumps("unknown request"))


