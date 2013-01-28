#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys
import uuid
from pyassimp import core as pyassimp
from pyassimp.postprocess import *

import logging; logger = logging.getLogger("underworlds.model_loader")

import underworlds
from underworlds.types import *

DEFAULT_WORLD = "base"

class ModelLoader:

    meshes = {}
    node_map = {}

    def __init__(self, world = DEFAULT_WORLD):
        self.world = world

    def mesh_hash(self, mesh):
        m = (mesh.vertices, \
            mesh.faces, \
            mesh.normals, \
            mesh.material.properties)
        return hash(str(m))

    def node_boundingbox(self, node):
        """ Returns the AABB bounding box of an ASSIMP node.
        Be careful: this is the *untransformed* bounding box,
        ie, the bounding box of the mesh in the node frame.
        """
        bb_min = [1e10, 1e10, 1e10] # x,y,z
        bb_max = [-1e10, -1e10, -1e10] # x,y,z
        for mesh in node.meshes:
            for v in mesh.vertices:
                bb_min[0] = round(min(bb_min[0], v[0]), 5)
                bb_min[1] = round(min(bb_min[1], v[1]), 5)
                bb_min[2] = round(min(bb_min[2], v[2]), 5)
                bb_max[0] = round(max(bb_max[0], v[0]), 5)
                bb_max[1] = round(max(bb_max[1], v[1]), 5)
                bb_max[2] = round(max(bb_max[2], v[2]), 5)
        return (bb_min, bb_max)

    def fill_node_details(self, assimp_node, underworlds_node, assimp_model):

        logger.debug("Parsing node " + str(assimp_node))
        underworlds_node.name = assimp_node.name
        #underworlds_node.parent = self.node_map[assimp_node.parent.name][1].id
        for c in assimp_node.children:
            underworlds_node.children.append(self.node_map[c.name][1].id)

        underworlds_node.transformation = assimp_node.transformation.tolist() # convert numpy array to plain python lists

        if assimp_node.meshes:
            underworlds_node.type = MESH
            underworlds_node.cad = []
            underworlds_node.hires = []

            for m in assimp_node.meshes:
                id = self.mesh_hash(m)
                logger.debug("\tLoading mesh %s" % id)
                self.meshes[id] = m
                underworlds_node.cad.append(id)
                underworlds_node.hires.append(id)

            underworlds_node.aabb = self.node_boundingbox(assimp_node)

        elif assimp_node.name in [c.name for c in assimp_model.cameras]:
            logger.debug("\tAdding camera <%s>" % assimp_node.name)

            [cam] = [c for c in assimp_model.cameras if c.name == assimp_node.name]
            underworlds_node.type = CAMERA
            underworlds_node.clipplanenear = cam.clipplanenear
            underworlds_node.clipplanefar = cam.clipplanefar
            underworlds_node.aspect = cam.aspect
            underworlds_node.horizontalfov = cam.horizontalfov
            underworlds_node.lookat = [round(a, 5) for a in cam.lookat]
        else:
            underworlds_node.type = UNDEFINED

    def recur_node(self, assimp_node,level = 0):
        logger.info("  " + "\t" * level + "- " + str(assimp_node))
        self.node_map[assimp_node.name] = (assimp_node, Node()) # cannot use assimp_node as key: it is unhashable
        for child in assimp_node.children:
            self.recur_node(child, level + 1)


    def load(self, filename):
        """Loads a Collada (or any Assimp compatible model) file in the world.

        The kinematic chains are added to the world's geometric state.
        The meshes are added to the meshes repository.

        A new 'load' event is also added the the world timeline.

        :param string path: the path (relative or absolute) to the Collada resource
        :todo: everything :-)

        """

        with underworlds.Context("model loader") as ctx:
            logger.info("Loading model <%s> with ASSIMP..." % filename)
            model = pyassimp.load(filename, aiProcessPreset_TargetRealtime_MaxQuality)
            logger.info("...done")

            world = ctx.worlds[self.world]
            nodes = world.scene.nodes
            logger.info("Nodes found:")
            self.recur_node(model.rootnode)
            logger.info("%d nodes in the model" % len(self.node_map))
            logger.info("Loading the nodes...")
            for n, pair in self.node_map.items():
                self.fill_node_details(*pair, assimp_model = model)
            logger.info("...done")

            for name, pair in self.node_map.items():
                if pair[0] == model.rootnode:
                    logger.info("Merging the root nodes")
                    pair[1].id = world.scene.rootnode.id

                nodes.update(pair[1])

            logger.info("Sending meshes to the server...")
            count_sent = 0
            count_notsent = 0
            for id, mesh in self.meshes.items():
                if ctx.has_mesh(id):
                    logger.debug("Not resending mesh <%s>: already available on the server" % id)
                    count_notsent += 1
                else:
                    logger.debug("Sending mesh <%s>" % id)
                    ctx.push_mesh(id, 
                                mesh.vertices.tolist(), 
                                mesh.faces.tolist(), 
                                mesh.normals.tolist(),
                                mesh.material.properties)
                    count_sent += 1

            logger.info("Sent %d meshes (%d were already available on the server)" % (count_sent, count_notsent))
            pyassimp.release(model)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) == 1:
        print("usage: %s path/to/model" % sys.argv[0])
        sys.exit(2)

    # Loads the model in the 'DEFAULT_WORLD' (ie, 'base')
    ModelLoader().load(sys.argv[1])