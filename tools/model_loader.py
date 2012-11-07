#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys
import uuid
from pyassimp import core as pyassimp
from pyassimp.postprocess import *

import logging; logger = logging.getLogger("underworlds.model_loader")
logging.basicConfig(level=logging.INFO)

import underworlds
from underworlds.types import *

DEST_WORLD = "base"

meshes = {}
node_map = {}

def mesh_hash(mesh):
    m = (mesh.vertices, \
         mesh.faces, \
         mesh.normals)
    return hash(str(m))

def node_boundingbox(node):
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

def fill_node_details(assimp_node, underworlds_node):

    logger.info("Parsing node " + str(assimp_node))
    underworlds_node.name = assimp_node.name
    #underworlds_node.parent = node_map[assimp_node.parent.name][1].id
    for c in assimp_node.children:
        underworlds_node.children.append(node_map[c.name][1].id)

    underworlds_node.transformation = assimp_node.transformation.tolist() # convert numpy array to plain python lists

    if assimp_node.meshes:
        underworlds_node.type = MESH
        underworlds_node.cad = []
        underworlds_node.hires = []

        for m in assimp_node.meshes:
            id = mesh_hash(m)
            logger.info("\tAdding mesh %s" % id)
            meshes[id] = m
            underworlds_node.cad.append(id)
            underworlds_node.hires.append(id)

        underworlds_node.aabb = node_boundingbox(assimp_node)

    else:
        underworlds_node.type = UNDEFINED

def recur_node(assimp_node,level = 0):
    logger.info("  " + "\t" * level + "- " + str(assimp_node))
    node_map[assimp_node.name] = (assimp_node, Node()) # cannot use assimp_node as key: it is unhashable
    for child in assimp_node.children:
        recur_node(child, level + 1)


def load(filename):
    """Loads a Collada (or any Assimp compatible mesh) file in the world.

    The kinematic chains are added to the world's geometric state.
    The meshes are added to the meshes repository.

    A new 'load' event is also added the the world timeline.

    :param string path: the path (relative or absolute) to the Collada resource
    :todo: everything :-)

    """

    with underworlds.Context("model loader") as ctx:
        model = pyassimp.load(filename, aiProcessPreset_TargetRealtime_MaxQuality)
        world = ctx.worlds[DEST_WORLD]
        nodes = world.scene.nodes
        logger.info("Nodes found:")
        recur_node(model.rootnode)
        for n, pair in node_map.items():
            fill_node_details(*pair)

        for name, pair in node_map.items():
            if pair[0] == model.rootnode:
                logger.info("Merging the root nodes")
                pair[1].id = world.scene.rootnode.id

            nodes.update(pair[1])

        for id, mesh in meshes.items():
            if ctx.has_mesh(id):
                logger.info("Not resending mesh %s: already available on the server" % id)
            else:
                ctx.push_mesh(id, 
                            mesh.vertices.tolist(), 
                            mesh.faces.tolist(), 
                            mesh.normals.tolist())

        pyassimp.release(model)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("usage: %s path/to/model" % sys.argv[0])
        sys.exit(2)

    load(sys.argv[1])