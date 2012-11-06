#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys
import uuid
from pyassimp import core as pyassimp
from pyassimp.postprocess import *

import logging; logger = logging.getLogger("underworlds.mesh_loader")
logging.basicConfig(level=logging.INFO)

import underworlds
from underworlds.types import *

DEST_WORLD = "base"

meshes = {}
node_map = {}

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
            id = str(uuid.uuid4())
            logger.info("\tAdding mesh %s" % id)
            meshes[id] = m
            underworlds_node.cad.append(id)
            underworlds_node.hires.append(id)

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

    with underworlds.Context("mesh loader") as ctx:
        model = pyassimp.load(filename, aiProcessPreset_TargetRealtime_MaxQuality)
        world = ctx.worlds[DEST_WORLD]
        nodes = world.scene.nodes
        logger.info("Nodes found:")
        recur_node(model.rootnode)
        for n, pair in node_map.items():
            fill_node_details(*pair)

        for pair in node_map.values():
            nodes.update(pair[1])

        for id, mesh in meshes.items():
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
