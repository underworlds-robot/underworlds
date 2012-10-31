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

    def delete_node(self, scene, id):
        scene.nodes.remove(scene.node(id))

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
                req = rpc.recv().split(" ",1)
                cmd = req[0]
                arg = ""
                if len(req) == 2:
                    arg = req[1]

                logger.info("Received request: " + cmd + " " + arg)

                if cmd == "get_nodes_len":
                    rpc.send(str(len(scene.nodes)))

                elif cmd == "get_nodes_ids":
                    rpc.send(json.dumps([n.id for n in scene.nodes]))

                elif cmd == "get_node":
                    rpc.send(scene.node(arg).serialize())

                elif cmd == "update_node":
                    node = Node.deserialize(arg)
                    rpc.send("ack")
                    action = self.update_node(scene, node)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [" + action + "]")
                    invalidation.send(action)

                elif cmd == "delete_node":
                    rpc.send("ack")
                    action = self.delete_node(scene, arg)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [delete]")
                    invalidation.send(str("delete " + arg))



                else:
                    logger.warning("Unknown request")
                    socket.send(json.dumps("unknown request"))
            else:
                invalidation.send("nop 0")

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
