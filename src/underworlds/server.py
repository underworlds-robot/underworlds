from underworlds.types import *

import zmq
import time
import json
from threading import Thread

import logging;logger = logging.getLogger("underworlds.server")

class Server(Thread):

    def __init__(self):
        Thread.__init__(self)
        self._running = True

    def update_node(self, scene, node):

        if scene.node(node.id): # the node already exist
            # replace the node
            scene.nodes = [node if old == node else old for old in scene.nodes]
            action = "update"

        else: # new node
            scene.nodes.append(node)
            action = "new"
        
        return str(action + " " + node.id)

    def stop(self):
        self._running = False

    def run(self):

        logger.info("Starting the server.")

        context = zmq.Context()
        rpc = context.socket(zmq.REP)
        rpc.bind("tcp://*:5555")

        invalidation = context.socket(zmq.PUB)
        invalidation.bind ("tcp://*:5556")

        poller = zmq.Poller()
        poller.register(rpc, zmq.POLLIN)

        scene = Scene()


        while self._running:
            socks = dict(poller.poll(200))
            
            if socks.get(rpc) == zmq.POLLIN:
                req = rpc.recv().split()

                logger.info("Received request: " + str(req))

                name = req[0]

                if name == "get_nodes_len":
                    rpc.send(str(len(scene.nodes)))

                elif name == "get_nodes_ids":
                    rpc.send(json.dumps([n.id for n in scene.nodes]))

                elif name == "get_node":
                    id = req[1]
                    rpc.send(scene.node(id).serialize())

                elif name == "update_node":
                    id = req[1]
                    rpc.send("get_node " + id)
                    data = rpc.recv()
                    rpc.send("ack")
                    node = Node.deserialize(data)
                    action = self.update_node(scene, node)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [" + action + "]")
                    invalidation.send(action)


                else:
                    logger.warning("Unknown request")
                    socket.send(json.dumps("unknown request"))
            else:
                time.sleep(0.01)


        logger.info("Closing the server.")

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    server = Server()

    server.start()

    try:
        while True:
            server.join(.2)
    except KeyboardInterrupt:
        server.stop()
        server.join()
