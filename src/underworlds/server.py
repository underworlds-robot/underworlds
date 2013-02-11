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
        self._clientnames = {}
        
        # meshes are stored as a dictionary:
        # - the key is a unique ID
        # - the value is a ditionary with these keys:
        #   - vertices: [(x,y,z), ...]
        #   - faces: [(i1, i2, i3), ...] with i an index in the vertices list
        #   - normals
        self.meshes = {}

    def new_client(self, id, name):
        self._clients[id] = {}
        self._clientnames[id] = name
        logger.info("New client <%s> has connected." % name)

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
        return {"clientnames": self._clientnames, "clients": self._clients, "worlds": self._worlds.keys()}

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

    def event(self, timeline, sit):

        if timeline.situation(sit.id): # the situation already exist. Error!
            raise StandardError("Attempting to add twice the same situation!")

        else: # new situation
            timeline.event(sit)
            action = "event"

        return str(action + " " + sit.serialize())

    def new_situation(self, timeline, sit):

        if timeline.situation(sit.id): # the situation already exist. Error!
            raise StandardError("Attempting to add twice the same situation!")

        else: # new situation
            timeline.start(sit)
            action = "start"
        
        return str(action + " " + sit.serialize())

    def end_situation(self, timeline, id):

        sit = timeline.situation(id)

        if not sit:
            raise StandardError("Attempting to end a non-existant situation!")

        timeline.end(sit)
        action = "end"
        
        return str(action + " " + id)


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
                timeline = None

                if "world" in req:

                    world = req["world"]

                    if world not in self._worlds:
                        self.new_world(world)

                    scene = self._worlds[world].scene
                    timeline = self._worlds[world].timeline

                req = req["req"].split(" ",1)
                cmd = req[0]
                arg = ""
                if len(req) == 2:
                    arg = req[1]

                logger.debug("Received request: <%s(%s)> from <%s> on world <%s>" % (cmd, arg, self._clientnames.get(client, client), world))

                if cmd == "helo":
                    self.new_client(client, arg)
                    rpc.send(str("helo " + client))


                ###########################################################################
                # SCENES
                ###########################################################################
                elif cmd == "deepcopy":
                    self.update_current_links(client, world, PROVIDER)
                    logger.info("Running a deep copy of world <%s> into world <%s>" % (arg, world))
                    self._worlds[world].deepcopy(self._worlds[arg])
                    rpc.send("ack")

                elif cmd == "get_nodes_len":
                    rpc.send(str(len(scene.nodes)))

                elif cmd == "get_nodes_ids":
                    rpc.send(json.dumps([n.id for n in scene.nodes]))

                elif cmd == "get_root_node":
                    rpc.send(scene.rootnode.id)

                elif cmd == "get_node":
                    self.update_current_links(client, world, READER)
                    node = scene.node(arg)
                    if not node:
                        logger.warning("Client %s has required a inexistant node %s" % (client, arg))
                        rpc.send("")
                    else:
                        rpc.send(scene.node(arg).serialize())

                elif cmd == "update_node":
                    self.update_current_links(client, world, PROVIDER)
                    node = Node.deserialize(arg)
                    rpc.send("ack")
                    action = self.update_node(scene, node)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [" + action + "]")
                    invalidation.send(str("%s?nodes### %s" % (world, action)))

                elif cmd == "delete_node":
                    self.update_current_links(client, world, PROVIDER)
                    rpc.send("ack")
                    action = self.delete_node(scene, arg)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [delete]")
                    invalidation.send(str("%s?nodes### delete %s" % (world, arg)))

                ###########################################################################
                # TIMELINES
                ###########################################################################
                elif cmd == "timeline_origin":
                    self.update_current_links(client, world, READER)
                    rpc.send(json.dumps(timeline.origin))

                elif cmd == "get_situations":
                    #self.update_current_links(client, world, READER)
                    #rpc.send(json.dumps(timeline.origin))
                    #action = self.new_situation(timeline, situation)
                    ## tells everyone about the change
                    #logger.debug("Sent invalidation action [" + action + "]")
                    #invalidation.send(str("%s?timeline### %s" % (world, action)))
                    pass #TODO

                elif cmd == "event":
                    self.update_current_links(client, world, PROVIDER)
                    situation = Situation.deserialize(arg)
                    rpc.send("ack")
                    action = self.event(timeline, situation)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [" + action + "]")
                    invalidation.send(str("%s?timeline### %s" % (world, action)))
                elif cmd == "new_situation":
                    self.update_current_links(client, world, PROVIDER)
                    situation = Situation.deserialize(arg)
                    rpc.send("ack")
                    action = self.new_situation(timeline, situation)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [" + action + "]")
                    invalidation.send(str("%s?timeline### %s" % (world, action)))

                elif cmd == "end_situation":
                    self.update_current_links(client, world, PROVIDER)
                    rpc.send("ack")
                    action = self.end_situation(timeline, arg)
                    # tells everyone about the change
                    logger.debug("Sent invalidation action [" + action + "]")
                    invalidation.send(str("%s?timeline### %s" % (world, action)))



                ###########################################################################
                # MESHES
                ###########################################################################
                elif cmd == "push_mesh":
                    mesh_id, data = arg.split(" ",1)
                    self.meshes[mesh_id] = json.loads(data)
                    rpc.send("ack")

                elif cmd == "get_mesh":
                    rpc.send(json.dumps(self.meshes[arg]))

                elif cmd == "has_mesh":
                    rpc.send(json.dumps(arg in self.meshes))

                ###########################################################################
                # MISC
                ###########################################################################

                elif cmd == "uptime":
                    rpc.send(str(self.uptime()))

                elif cmd == "get_topology":
                    rpc.send(json.dumps(self.get_current_topology()))

                ###########################################################################

                else:
                    logger.warning("Unknown request <%s>" % cmd)
                    rpc.send(str("unknown request"))
            else:
                invalidation.send(str("nop"))

        logger.info("Closing the server.")

if __name__ == "__main__":

    #logging.basicConfig(level=logging.INFO)
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
