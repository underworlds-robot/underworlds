import uuid
import time
import threading
import logging;logger = logging.getLogger("underworlds.server")

from underworlds.types import READER
from underworlds.helpers.profile import profile, profileonce
from grpc.framework.interfaces.face.face import ExpirationError,NetworkError,AbortionError
import underworlds.underworlds_pb2 as gRPC 
from grpc.beta import interfaces as beta_interfaces
from grpc.beta import implementations

_TIMEOUT_SECONDS = 1

class Client:

    def __init__(self, name, host, port):
        self.id = str(uuid.uuid4())
        self.name = name

        # stores the links (cf clients' types) with the various worlds.
        self.links = {}

        self.channel = None
        self.invalidation_server = self._connect_invalidation_server(name, host, port)
        self.isactive = (self.invalidation_server is not None)

        self.active_invalidations = []

        self.grpc_client = gRPC.Client(id=self.id)

        if self.isactive:
            logger.debug("Client %s (id: %s) successfully created." % (self.name, self.id))
        else:
            logger.warn("Client %s (id: %s) created but inactive." % (self.name, self.id))


    def _connect_invalidation_server(self, name, host, port):
        try:
            self.channel = implementations.insecure_channel(host, port)
            invalidation_server = gRPC.beta_create_UnderworldsInvalidation_stub(self.channel)
            logger.info("Connected to invalidation server of client <%s>" % name)
            return invalidation_server

        except (NetworkError, AbortionError) as e:
            logger.warning("Underworld server unable to establish a connection with Underworlds'\n"
                         " client <%> on %s:%d. Client died? Unreachable over network?\n"
                         "Removing the client.\nOriginal error: %s" % (name, host, port, str(e)))
            return None

    def emit_invalidation(self, invalidation):

        if not self.isactive:
            logger.debug("Attempting to send invalidations to inactive client <%s>. Skipping" % self.name)
            return

        future = self.invalidation_server.emitInvalidation.future(invalidation, _TIMEOUT_SECONDS)

        self.active_invalidations.append(future)

        # remove the future form the current list of active invalidations upon completion
        future.add_done_callback(self._cleanup_completed_invalidations)


    def _cleanup_completed_invalidations(self, invalidation):
        e = invalidation.exception()
        if e is not None:
            logger.warn("An exception occured while sending invalidations to %s: %s" % (self.name, str(e)))
            self.isactive = False
        else:
            self.active_invalidations.remove(invalidation)

    def reset_links(self):
        self.links = {}

    def close(self):
        self.isactive = False
        logger.debug("Waiting for all pending invalidation to client <%s> to complete..." % self.name)
        for i in self.active_invalidations:
            i.result()
        logger.debug("No more pending invalidations. The client <%s> is now properly disconnected." % self.name)
        self.active_invalidations = []




class Server(gRPC.BetaUnderworldsServicer):

    def __init__(self):

        # maps the worlds to a mapping {object id, gRPC object} of the objects they contain
        self._worlds = {}

        self._clients = {} 
        self._client_lock = threading.RLock()

        # meshes are stored as a dictionary:
        # - the key is a unique ID
        # - the value is a ditionary with these keys:
        #   - vertices: [(x,y,z), ...]
        #   - faces: [(i1, i2, i3), ...] with i an index in the vertices list
        #   - normals
        self.meshes = {}

        self.starttime = time.time()

    def _clientname(self, id):
        with self._client_lock:
            return self._clients[id].name

    def _new_world(self, name):
        self._worlds[name] = {}

    def _get_object(self, ctxt, id):

        return self._worlds[ctxt.world].get(id, None)

    def _update_current_links(self, client, world, type):

        with self._client_lock:
            if world in self._clients[client].links:
                current_type = self._clients[client].links[world][0]
                # update only if the current link is 'READER' (we do not 
                # want a 'READER' to overwrite a 'PROVIDER' for instance)
                type = type if current_type == READER else current_type
            self._clients[client].links[world] = (type, time.time())

    def _update_object(self, world, object):

        parent_has_changed = False

        object.last_update = time.time()

        oldobject = self._get_object(object.id)

        if oldobject: # the object already exist
            parent = object.properties.get("parent", None)
            oldparent = oldobject.properties.get("parent", None)
            parent_has_changed = oldparent != object.parent

            # update the list of children
            children = [id for id, obj in self._worlds[world].items() if obj.properties.get("parent", None) == object.id]
            if children:
                object.properties["children"] = json.dumps(children)

            # replace the object
            scene.objects = [object if old == object else old for old in scene.objects]
            
            action = gRPC.Invalidation.UPDATE

        else: # new object
            scene.objects.append(object)
            parent_has_changed = True
            if object.parent is None:
                object.parent = scene.rootobject.id
            action = gRPC.Invalidation.NEW

        return action, parent_has_changed

    def _delete_object(self, scene, id):
        scene.objects.remove(scene.object(id))

    def _update_situation(self, timeline, situation):

        situation.last_update = time.time()

        if situation.id in timeline.situations:
            action = gRPC.Invalidation.UPDATE
        else:
            action = gRPC.Invalidation.NEW

        timeline.update(situation)

        return action

    @profile
    def _emit_invalidation(self, target, world, object_ids, invalidation_type):

        invalidation = gRPC.Invalidation(target=target,
                                         type=invalidation_type, 
                                         world=world)
        invalidation.ids[:] = object_ids


        with self._client_lock:
            for client_id in self._clients:
                if world in self._clients[client_id].links:
                    logger.debug("Informing client <%s> that objects have been invalidated in world <%s>" % (self._clientname(client_id), world))
                    self._clients[client_id].emit_invalidation(invalidation)


    #############################################
    ############ Underworlds API ################

    ############ GENERAL
    @profile
    def helo(self, client, context):
        logger.debug("Got <helo> from %s" % client.name)
        c = Client(client.name, client.host, client.invalidation_server_port)
        with self._client_lock:
            self._clients[c.id] = c

        logger.debug("<helo> completed")
        return c.grpc_client

    @profile
    def byebye(self, client, context):
        logger.debug("Got <byebye> from %s" % (self._clientname(client.id)))

        with self._client_lock:
            self._clients[client.id].close()
            del self._clients[client.id]

        logger.debug("<byebye> completed")
        return gRPC.Empty()


    @profile
    def uptime(self, client, context):
        logger.debug("Got <uptime> from %s" % client.id)
        res = gRPC.Time(time=time.time() - self.starttime)
        logger.debug("<uptime> completed")
        return res

    @profile
    def topology(self, client, context):
        logger.debug("Got <topology> from %s" % client.id)
    
        topo = gRPC.Topology()

        for w in self._worlds.keys():
            topo.worlds.append(w)

        with self._client_lock:
            for client_id in self._clients:
                links = self._clients[client_id].links
                client = topo.clients.add()
                client.id  = client_id
                client.name = self._clientname(client_id)

                for w, details in links.items():

                    type, timestamp = details

                    interaction = client.links.add()
                    interaction.world = w
                    interaction.type = type
                    interaction.last_activity.time = timestamp



        logger.debug("<topology> completed")
        return topo

    @profile
    def reset(self, client, context):
        logger.debug("Got <reset> from %s" % client.id)
        logger.warning("Resetting Underworlds upon client <%s> request" % client.id)
        logger.warning("This might break other clients!")

        self._worlds = {}

        with self._client_lock:
            for cid, c in self._clients.items():
                c.reset_links()

        logger.debug("<reset> completed")

        return gRPC.Empty()


    ############ objectS
    @profile
    def getObjectsLen(self, ctxt, context):
        logger.debug("Got <getObjectsLen> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene, timeline = self._get_scene_timeline(ctxt)

        res = gRPC.Size(size=len(scene.objects) + len(scene.situations))
        logger.debug("<getObjectsLen> completed")
        return res

    @profile
    def getObjectsIds(self, ctxt, context):
        logger.debug("Got <getObjectsIds> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene, timeline = self._get_scene_timeline(ctxt)

        objects = gRPC.IdsInContext()
        objects.context = context

        for n in scene.objects:
            objects.ids.append(n.id)

        for s in timeline.situations:
            objects.ids.append(s.id)

        logger.debug("<getObjectsIds> completed")
        return objects

    @profile
    def getRootObject(self, ctxt, context):
        logger.debug("Got <getRootObject> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        scene,_ = self._get_scene_timeline(ctxt)

        res = gRPC.Object(id=scene.rootobject.id)
        logger.debug("<getRootObject> completed")
        return res

    @profile
    def getObject(self, objectInCtxt, context):
        logger.debug("Got <getObject> from %s" % self._clientname(objectInCtxt.context.client))

        client_id, world = objectInCtxt.context.client, objectInCtxt.context.world


        self._update_current_links(client_id, world, READER)

        if not objectInCtxt.id:
            logger.warning("%s has required an object without specifying its id!" % (self._clientname(client_id)))

            context.details("No object id provided")
            context.code(beta_interfaces.StatusCode.NOT_FOUND)
            return gRPC.Object()

        object = self._get_object(objectInCtxt.context, objectInCtxt.id)

        if object is not None:
            res = object.serialize(gRPC.Object)
            logger.debug("<getObject> completed")
            return res


        logger.warning("%s has required an non-existant "
                        "object <%s> in world %s" % (self._clientname(client_id), objectInCtxt.object.id, world))

        context.details("Object <%s> does not exist in world %s" % (objectInCtxt.object.id, world))
        context.code(beta_interfaces.StatusCode.NOT_FOUND)
        return gRPC.Object()

    @profile
    def updateObjects(self, objectsInCtxt, context):
        logger.debug("Got <updateObjects> from %s" % objectsInCtxt.context.client)

        client_id, world = objectsInCtxt.context.client, objectsInCtxt.context.world
        self._update_current_links(client_id, world, PROVIDER)

        scene,_ = self._get_scene_timeline(objectsInCtxt.context)
        object = self._get_object(objectInCtxt.context, objectInCtxt.id)

        objects_to_invalidate_new = []
        objects_to_invalidate_update = []
        for gRPCObject in objectsInCtxt.objects:
            object = Object.deserialize(gRPCObject)

            invalidation_type, parent_has_changed = self._update_object(scene, object)

            logger.info("<%s> %s object <%s> in world <%s>" % \
                                (self._clientname(client_id), 
                                "updated" if invalidation_type==gRPC.Invalidation.UPDATE else "created",
                                repr(object), 
                                world))

            if invalidation_type ==  gRPC.Invalidation.UPDATE:
                objects_to_invalidate_update.append(gRPCObject.id)
            elif invalidation_type ==  gRPC.Invalidation.NEW:
                objects_to_invalidate_new.append(gRPCObject.id)
            else:
                raise RuntimeError("Unexpected invalidation type")


            ## If necessary, update the object hierarchy
            if parent_has_changed:
                parent = scene.object(object.parent)
                if parent is None:
                    logger.warning("Object %s references a non-exisiting parent" % object)
                elif object.id not in parent.children:
                    parent._children.append(object.id)
                    # tells everyone about the change to the parent
                    logger.debug("Adding invalidation action [update " + parent.id + "] due to hierarchy update")
                    objects_to_invalidate_update.append(parent.id)

                    # As a object has only one parent, if the parent has changed we must
                    # remove our object from its previous parent
                    for otherobject in scene.objects:
                        if otherobject.id != parent.id and object.id in otherobject.children:
                            otherobject._children.remove(object.id)
                            # tells everyone about the change to the former parent
                            logger.debug("Adding invalidation action [update " + otherobject.id + "] due to hierarchy update")
                            objects_to_invalidate_update.append(otherobject.id)
                            break

        if objects_to_invalidate_update:
            self._emit_invalidation(gRPC.Invalidation.SCENE, world, objects_to_invalidate_update, gRPC.Invalidation.UPDATE)
        if objects_to_invalidate_new:
            self._emit_invalidation(gRPC.Invalidation.SCENE, world, objects_to_invalidate_new, gRPC.Invalidation.NEW)


        logger.debug("<updateObjects> completed")
        return gRPC.Empty()

    @profile
    def deleteObjects(self, objectsInCtxt, context):
        logger.debug("Got <deleteObjects> from %s" % objectsInCtxt.context.client)
        self._update_current_links(objectsInCtxt.context.client, objectsInCtxt.context.world, PROVIDER)

        client_id, world = objectsInCtxt.context.client, objectsInCtxt.context.world
        scene,_ = self._get_scene_timeline(objectsInCtxt.context)

        objects_to_invalidate_delete = []
        objects_to_invalidate_update = []
        for gRPCObject in objectsInCtxt.objects:
            object = scene.object(gRPCObject.id)
            logger.info("<%s> deleted object <%s> in world <%s>" % \
                                (self._clientname(client_id), 
                                repr(object), 
                                world))

            action = self._delete_object(scene, gRPCObject.id)

            # tells everyone about the change
            logger.debug("Sent invalidation action [delete]")
            objects_to_invalidate_delete.append(gRPCObject.id)

            # reparent children to the scene's root object
            children_to_update = []
            for child_id in object.children:
                child = scene.object(child_id)
                child.parent = scene.rootobject.id
                logger.debug("Reparenting child " + child_id + " to root object")
                objects_to_invalidate_update.append(child_id)

            # Also remove the object from its parent's children
            parent = scene.object(object.parent)
            if parent:
                parent._children.remove(object.id)
                # tells everyone about the change to the parent
                logger.debug("Sent invalidation action [update " + parent.id + "] due to hierarchy update")
                objects_to_invalidate_update.append(parent.id)

        if objects_to_invalidate_update:
            self._emit_invalidation(gRPC.Invalidation.SCENE, world, objects_to_invalidate_update, gRPC.Invalidation.UPDATE)
        if objects_to_invalidate_delete:
            self._emit_invalidation(gRPC.Invalidation.SCENE, world, objects_to_invalidate_delete, gRPC.Invalidation.DELETE)


        logger.debug("<deleteObjects> completed")
        return gRPC.Empty()


    ############ TIMELINES
    @profile
    def getSituationsLen(self, ctxt, context):
        logger.debug("Got <getSituationsLen> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        _,timeline = self._get_scene_timeline(ctxt)

        res = gRPC.Size(size=len(timeline.situations))
        logger.debug("<getSituationsLen> completed")
        return res

    @profile
    def getSituationsIds(self, ctxt, context):
        logger.debug("Got <getSituationsIds> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        _,timeline = self._get_scene_timeline(ctxt)

        situations = gRPC.Situations()
        for s in timeline.situations:
            situations.ids.append(s.id)

        logger.debug("<getSituationsIds> completed")
        return situations


    @profile
    def getSituation(self, sitInCtxt, context):
        logger.debug("Got <getSituation> from %s" % sitInCtxt.context.client)

        client_id, world = sitInCtxt.context.client, sitInCtxt.context.world

        _,timeline = self._get_scene_timeline(sitInCtxt.context)

        self._update_current_links(client_id, world, READER)

        if not sitInCtxt.situation.id:
            logger.warning("%s has required a situation without specifying its id!" % (self._clientname(client_id)))

            context.details("No situation id provided")
            context.code(beta_interfaces.StatusCode.NOT_FOUND)
            return gRPC.Object()


        situation = timeline.situation(sitInCtxt.situation.id)

        if not situation:
            logger.warning("%s has required an non-existant "
                           "situation <%s> in world %s" % (self._clientname(client_id), sitInCtxt.object.id, world))

            context.details("Situation <%s> does not exist in world %s" % (sitInCtxt.object.id, world))
            context.code(beta_interfaces.StatusCode.NOT_FOUND)
            return gRPC.Situation()


        else:
            res = situation.serialize(gRPC.Situation)
            logger.debug("<getSituation> completed")
            return res

    @profile
    def timelineOrigin(self, ctxt, context):
        logger.debug("Got <timelineOrigin> from %s" % ctxt.client)
        self._update_current_links(ctxt.client, ctxt.world, READER)

        _,timeline = self._get_scene_timeline(ctxt)

        res = gRPC.Time(time=timeline.origin)
        logger.debug("<timelineOrigin> completed")
        return res

    @profile
    def updateSituations(self, sitInCtxt, context):
        logger.debug("Got <updateSituations> from %s" % sitInCtxt.context.client)
        self._update_current_links(sitInCtxt.context.client, sitInCtxt.context.world, PROVIDER)

        client_id, world = sitInCtxt.context.client, sitInCtxt.context.world
        _, timeline = self._get_scene_timeline(sitInCtxt.context)

        situations_to_invalidate_update = []
        situations_to_invalidate_new = []
        for gRPCSit in sitInCtxt.situations:


            situation = Situation.deserialize(gRPCSit)

            invalidation_type = self._update_situation(timeline, situation)

            logger.info("<%s> updated situation <%s> in world <%s>" % \
                                (self._clientname(client_id), 
                                repr(situation), 
                                world))


            logger.debug("Adding invalidation action [" + str(invalidation_type) + "]")

            if invalidation_type ==  gRPC.Invalidation.UPDATE:
                situations_to_invalidate_update.append(situation.id)
            elif invalidation_type ==  gRPC.Invalidation.NEW:
                situations_to_invalidate_new.append(situation.id)
            else:
                raise RuntimeError("Unexpected invalidation type")

        if situations_to_invalidate_update:
            self._emit_invalidation(gRPC.Invalidation.TIMELINE, world, situations_to_invalidate_update, gRPC.Invalidation.UPDATE)
        if situations_to_invalidate_new:
            self._emit_invalidation(gRPC.Invalidation.TIMELINE, world, situations_to_invalidate_new, gRPC.Invalidation.NEW)


        logger.debug("<updateSituations> completed")
        return gRPC.Empty()

    @profile
    def deleteSituations(self, sitInCtxt, context):
        logger.debug("Got <deleteSituations> from %s" % sitInCtxt.context.client)
        self._update_current_links(sitInCtxt.context.client, sitInCtxt.context.world, PROVIDER)

        client_id, world = sitInCtxt.context.client, sitInCtxt.context.world
        _, timeline = self._get_scene_timeline(sitInCtxt.context)

        situations_to_invalidate_delete = []
        for gRPCSit in sitInCtxt.situations:

            situation = Situation.deserialize(gRPCSit)

            timeline.remove(situation)

            logger.info("<%s> deleted situation <%s> in world <%s>" % \
                                (self._clientname(client_id), 
                                repr(situation), 
                                world))

            # tells everyone about the change
            logger.debug("Sent invalidation action [delete]")
            situations_to_invalidate_delete.append(situation.id)

        if situations_to_invalidate_delete:
            self._emit_invalidation(gRPC.Invalidation.TIMELINE, world, situations_to_invalidate_delete, gRPC.Invalidation.DELETE)

        logger.debug("<deleteSituations> completed")
        return gRPC.Empty()

    ############ MESHES
    @profile
    def hasMesh(self, meshInCtxt, context):
        logger.debug("Got <hasMesh> from %s" % meshInCtxt.client.id)
        res = gRPC.Bool(value=(meshInCtxt.mesh.id in self.meshes))
        logger.debug("<hasMesh> completed")
        return res

    @profile
    def getMesh(self, meshInCtxt, context):
        logger.debug("Got <getMesh> from %s" % meshInCtxt.client.id)
        logger.debug("<getMesh> completed")
        return self.meshes[meshInCtxt.mesh.id]

    @profile
    def pushMesh(self, meshInCtxt, context):
        logger.debug("Got <pushMesh> from %s" % meshInCtxt.client.id)

        mesh_id = meshInCtxt.mesh.id
        self.meshes[mesh_id] = meshInCtxt.mesh

        logger.info("<%s> added a new mesh ID %s (%d faces)" % \
                                (self._clientname(meshInCtxt.client.id),
                                mesh_id, 
                                len(self.meshes[mesh_id].faces)))

        logger.debug("<pushMesh> completed")
        return gRPC.Empty()


#
#                ###########################################################################
#                # SCENES
#                ###########################################################################
#                if cmd == "deepcopy":
#                    self.update_current_links(client, world, PROVIDER)
#                    logger.info("<%s> made a deep copy of world %s "
#                                "into world %s" % (clientname, arg, world))
#                    self._worlds[world].deepcopy(self._worlds[arg])
#                    rpc.send(b"ack")
#
#
#

#                ###########################################################################
#                # TIMELINES
#                ###########################################################################
#
#                elif cmd == "get_situations":
#                    #self.update_current_links(client, world, READER)
#                    #rpc.send_json(timeline.origin)
#                    #action = self.new_situation(timeline, situation)
#                    ## tells everyone about the change
#                    #logger.debug("Sent invalidation action [" + action + "]")
#                    #invalidation.send(("%s?timeline### %s" % (world, action)).encode())
#                    pass #TODO
#

def start(port=50051, signaling_queue=None):
    """Starts the underworlds server in a thread on the given port and returns
    the resulting gRPC server.

    If signaling_queue is provided, the behaviour is blocking:
    it creates and start an underworlds server, then blocks until something is pushed onto the queue.
    It then properly closes the server and returns None.
    """

    desired_port=str(port)

    server = gRPC.beta_create_Underworlds_server(Server())
    port = server.add_insecure_port('[::]:%s' % desired_port)

    if port == 0:
        raise RuntimeError("The port %s is already in use! Underworlds server already running? "
                     "I can not start the server." % desired_port)

    logger.info("Starting the server...")
    server.start()
    time.sleep(0.2) # leave some time to the server to start
    logger.info("Server started.")

    if signaling_queue is None:
        return server
    else:
        # block on the queue
        signaling_queue.get()
        logger.info("uwds server exiting. Closing connections...")
        server.stop(1).wait()
        logger.info("uwds server closed.")

def start_process(port=50051):
    import multiprocessing

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=start, args=(port, q,))
    p.start()

    return p, q

if __name__ == "__main__":

    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)

    server = start()

    try:
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        logger.info("Closing the server.")
        server.stop(0)

    logger.info("Bye bye.")
