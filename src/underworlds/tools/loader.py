#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys
import uuid

import logging; logger = logging.getLogger("underworlds.model_loader")

try:
    from pyassimp import core as pyassimp
    from pyassimp.postprocess import *
except BaseException as ae:
    logger.error("pyassimp could not be loaded: %s" % ae)
    pass

import math
import underworlds
from underworlds.types import *
from underworlds.helpers import transformations

DEFAULT_WORLD = "base"
ROTATION_180_X = numpy.array([[1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,1]], dtype=numpy.float32)

class ModelLoader:

    def __init__(self):

        self.meshes = {}

        # mapping {assimp name: (assimp node, underworld node)}
        self.node_map = {}

    def node_boundingbox(self, node):
        """ Returns the AABB bounding box of an ASSIMP node.
        Be careful: this is the *untransformed* bounding box,
        ie, the bounding box of the mesh in the node frame.
        """
        x_min, y_min, z_min = 1e10, 1e10, 1e10
        x_max, y_max, z_max = -1e10, -1e10, -1e10
        for mesh in node.meshes:
            for v in mesh.vertices:
                x_min = round(min(x_min, v[0]), 5)
                y_min = round(min(y_min, v[1]), 5)
                z_min = round(min(z_min, v[2]), 5)
                x_max = round(max(x_max, v[0]), 5)
                y_max = round(max(y_max, v[1]), 5)
                z_max = round(max(z_max, v[2]), 5)
        return float(x_min), float(y_min), float(z_min), float(x_max), float(y_max), float(z_max)


    def fill_node_details(self, 
                          assimp_node, 
                          underworlds_node, 
                          assimp_model,
                          custom_root=None):

        logger.debug("Parsing node " + str(assimp_node))
        underworlds_node.name = assimp_node.name

        if assimp_node is not assimp_model.rootnode:
            parent = assimp_node.parent
            if parent == assimp_model.rootnode and custom_root:
                underworlds_node.parent = custom_root.id
            else:
                underworlds_node.parent = self.node_map[assimp_node.parent.name][1].id

        # No need to specify the node's children: this is automatically done
        # by underworlds

        underworlds_node.transformation = assimp_node.transformation.astype(numpy.float32)

        if assimp_node.meshes:

            for m in assimp_node.meshes:
                
                mesh = MeshData(m.vertices.tolist(), 
                                m.faces.tolist(), 
                                m.normals.tolist(),
                                m.material.properties["diffuse"])

                id = mesh.id
                logger.debug("\tLoading mesh %s" % id)
                self.meshes[id] = mesh
                if underworlds_node.properties["mesh_ids"] is None:
                    underworlds_node.properties["mesh_ids"] = [id]
                else:
                    underworlds_node.properties["mesh_ids"].append(id)

            underworlds_node.properties["aabb"] = self.node_boundingbox(assimp_node)

        elif assimp_node.name in [c.name for c in assimp_model.cameras]:
            logger.debug("\tAdding camera <%s>" % assimp_node.name)

            [cam] = [c for c in assimp_model.cameras if c.name == assimp_node.name]
            underworlds_node.properties["clipplanenear"] = cam.clipplanenear
            underworlds_node.properties["clipplanefar"] = cam.clipplanefar

            if numpy.allclose(cam.lookat, [0,0,-1]) and numpy.allclose(cam.up, [0,1,0]): # Cameras in .blend files

                # Rotate by 180deg around X to have Z pointing forward
                underworlds_node.transformation = numpy.dot(underworlds_node.transformation, ROTATION_180_X)
            else:
                raise RuntimeError("I do not know how to normalize this camera orientation: lookat=%s, up=%s" % (cam.lookat, cam.up))

            if cam.aspect == 0.0:
                logger.warning("Camera aspect not set. Setting to default 4:3")
                underworlds_node.properties["aspect"] = 1.333
            else:
                underworlds_node.properties["aspect"] = cam.aspect

            underworlds_node.properties["horizontalfov"] = cam.horizontalfov

            #underworlds_node.lookat = [round(a, 5) for a in cam.lookat]
        else:
            # Entity
            pass

    def recur_node(self, assimp_node, model, level = 0):
        logger.info("  " + "\t" * level + "- " + str(assimp_node))

        if assimp_node != model.rootnode: # the rootnode is already there
            if assimp_node.meshes:
                node = Mesh()
            elif assimp_node.name in [c.name for c in model.cameras]:
                node = Camera()
            else:
                node = Entity()

            self.node_map[assimp_node.name] = (assimp_node, node) # cannot use assimp_node as key: it is unhashable

        for child in assimp_node.children:
            self.recur_node(child, model, level + 1)


    def load(self, filename, ctx=None, world=DEFAULT_WORLD, root=None, only_meshes=False):
        """Loads a Collada (or any Assimp compatible model) file in the world.

        The kinematic chains are added to the world's geometric state.
        The meshes are added to the meshes repository.

        A new 'load' event is also added in the world timeline.

        :param string path: the path (relative or absolute) to the Collada resource
        :param Context ctx: an existing underworlds context. If not provided, a
                            new one is created (named 'model loader')
        :param string world: the target world for the creation of nodes
        :param Node root: if given, the loaded nodes will be parented to this
                          node instead of the scene's root.
        :param bool only_meshes: if true, no node is created. Only the
        meshes are pushed to the server.
        :returns: the list of loaded underworlds nodes.
        """

        self.meshes = {}
        self.node_map = {}

        if not only_meshes and world is None:
            raise RuntimeError("Can not create nodes if the world is None")

        close_ctx_at_end = False

        # Create a context if needed:
        if ctx is None:
            close_ctx_at_end = True
            ctx = underworlds.Context("model loader")

        logger.info("Loading model <%s> with ASSIMP..." % filename)
        model = pyassimp.load(filename, aiProcessPreset_TargetRealtime_MaxQuality)
        logger.info("...done")

        if not only_meshes:
            if not root:
                logger.info("Merging the root nodes")
                self.node_map[model.rootnode.name] = (model.rootnode, ctx.worlds[world].scene.rootnode)
        else:
            self.node_map[model.rootnode.name] = (model.rootnode, Entity())

        logger.info("Nodes found:")
        self.recur_node(model.rootnode, model)

        logger.info("%d nodes in the model" % len(self.node_map))
        logger.info("Loading the nodes...")
        for n, pair in list(self.node_map.items()):
            self.fill_node_details(*pair,
                                    assimp_model = model,
                                    custom_root=root)
        logger.info("...done")


        # Send first the meshes to make sure they are available on the server
        # when needed by clients.  (but only if they do not already exist on
        # the server)
        logger.info("Sending meshes to the server...")
        count_sent = 0
        count_notsent = 0
        for id, mesh in list(self.meshes.items()):
            if ctx.has_mesh(id):
                logger.debug("Not resending mesh <%s>: already available on the server" % id)
                count_notsent += 1
            else:
                logger.debug("Sending mesh <%s>" % id)
                ctx.push_mesh(mesh)
                count_sent += 1

        logger.info("Sent %d meshes (%d were already available on the server)" % (count_sent, count_notsent))

        if not only_meshes:
            nodes = ctx.worlds[world].scene.nodes

            # Send the nodes to the server (only the nodes)
            logger.info("Sending the nodes to the server...")
            for name, pair in list(self.node_map.items()):
                nodes.update(pair[1])


        pyassimp.release(model)



        if close_ctx_at_end:
            ctx.close()

        return [nodes[1] for _,nodes in self.node_map.items()]

    def load_meshes(self, filename, ctx=None):
        """Pushes meshes from any Assimp-compatible 3D model to the server's
        mesh repository.

        A new 'load' event is also added in the world timeline.

        :param string path: the path (relative or absolute) to the 3D model
        :param Context ctx: an existing underworlds context. If not provided, a
                            new one is created (named 'model loader')
        :returns: a dictionary {mesh name: mesh ID} 

        :see: `load` loads the meshes and creates corresponding nodes.
        """

        return {n.name:n.cad for n in self.load(filename, ctx, None, None, True) if n.type == MESH}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) == 1:
        print(("usage: %s path/to/model" % sys.argv[0]))
        sys.exit(2)

    # Loads the model in the 'DEFAULT_WORLD' (ie, 'base')
    ModelLoader().load(sys.argv[1])
