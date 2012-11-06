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
        self._worlds = {}
        self._clients = {} # for each client, stored the links (cf clients' types) with the various worlds.

    def new_client(self, name):
        if name not in self._clients:
            self._clients[name] = {}
            logger.info("New client %s has connected." % name)
        else:
            logger.info("Client %s has just reconnected." % name)

    def update_current_links(self, client, world, type):
        if world in self._clients[client]:
            current_type = self._clients[client][world][0]
            # update only if the current link is 'READER' (we do not 
            # want a 'READER' to overwrite a 'PROVIDER' for instance)
            type = type if current_type == READER else current_type
        self._clients[client][world] = (type, time.time())

    def new_world(self, name):
        self._worlds[name] = World(name)
        logger.info("New world %s has been created." % name)

    def get_current_topology(self):
        return {"clients": self._clients, "worlds": self._worlds.keys()}

    def delete_node(self, scene, id):
        scene.nodes.remove(scene.node(id))

    def update_node(self, scene, node):

        node.last_update = time.time()

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

    def uptime(self):
        return time.time() - self.starttime

    def run(self):

        logger.info("Starting the server.")

        self.starttime = time.time()

        context = zmq.Context()
        rpc = context.socket(zmq.REP)
        rpc.bind("tcp://*:5555")

        invalidation = context.socket(zmq.PUB)
        invalidation.bind ("tcp://*:5556")

        poller = zmq.Poller()
        poller.register(rpc, zmq.POLLIN)



        while self._running:
            socks = dict(poller.poll(200))
            
            if socks.get(rpc) == zmq.POLLIN:

                req = json.loads(rpc.recv())
                client = req["client"]
                world = None
                scene = None

                if "world" in req:

                    world = req["world"]

                    if world not in self._worlds:
                        self.new_world(world)

                    scene = self._worlds[world].scene

                req = req["req"].split(" ",1)
                cmd = req[0]
                arg = ""
                if len(req) == 2:
                    arg = req[1]

                logger.debug("Received request: <%s(%s)> from %s on world %s" % (cmd, arg, client, world))

                if cmd == "helo":
                    self.new_client(client)
                    rpc.send(str("helo " + client))

                elif cmd == "uptime":
                    rpc.send(str(self.uptime()))

                elif cmd == "get_nodes_len":
                    rpc.send(str(len(scene.nodes)))

                elif cmd == "get_nodes_ids":
                    rpc.send(json.dumps([n.id for n in scene.nodes]))

                elif cmd == "get_node":
                    self.update_current_links(client, world, READER)
                    rpc.send(scene.node(arg).serialize())

                elif cmd == "update_node":
                    self.update_current_links(client, world, PROVIDER)
                    node = Node.deserialize(arg)
                    rpc.send("ack")
                    action = self.update_node(scene, node)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [" + action + "]")
                    invalidation.send(str("%s### %s" % (world, action)))

                elif cmd == "delete_node":
                    self.update_current_links(client, world, PROVIDER)
                    rpc.send("ack")
                    action = self.delete_node(scene, arg)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [delete]")
                    invalidation.send(str("%s### delete %s" % (world, arg)))

                elif cmd == "get_topology":
                    rpc.send(json.dumps(self.get_current_topology()))


                else:
                    logger.warning("Unknown request <%s>" % cmd)
                    rpc.send(str("unknown request"))
            else:
                invalidation.send(str("nop"))

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

    logger.info("The server process terminates now.")
