#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import os
import sys
import math
import underworlds

from underworlds.helpers import transformations
from underworlds.types import *
from underworlds.tools.loader import ModelLoader
from underworlds.tools.primitives_3d import Box

import logging; logger = logging.getLogger("underworlds.tools.edit")
logging.basicConfig(level=logging.INFO)

def _get_node(world, name):
    """ Returns a node from a name or an ID (or None if the name is None).
        Exits with error message if the node does not exist.
    """

    if name is None:
        return None

    try:
        return world.scene.nodes[name]
    except KeyError as e:
        candidate_nodes = world.scene.nodebyname(name)
        if not candidate_nodes:
            logger.error("Node %s could not be found. Check for typos!" % name)
            sys.exit(1)
        elif len(candidate_nodes) > 1:
            logger.error("More than one node matches %s: %s. Please provide "
                         "the exact ID instead of the name." % (name, str([repr(n) for n in candidate_nodes])))
            sys.exit(1)
        return candidate_nodes[0]

def _get_id(world, name):
    node = _get_node(world, name)
    return None if node is None else node.id

def create_mesh_node(world, node, mesh_ids, parent=None):
    """ Creates a node of type Mesh. 
    """

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        new_node = Mesh()

        new_node.properties["mesh_ids"] = mesh_ids

        new_node.name = node
        new_node.parent = _get_id(target_world, parent) # if parent is None, will be automatically parented to root by the server

        logger.info("Created Mesh Node %s with meshes %s in world %s"%(repr(new_node),str(new_node.properties["mesh_ids"]), world))

        target_world.scene.nodes.append(new_node)

def create_camera_node(world, node, aspect=0, horizontalfov=0, parent=None):
    """ Creates a node of type Camera.
    """

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        new_node = Camera()
        new_node.properties["aspect"] = aspect
        new_node.properties["horizontalfov"] = horizontalfov

        new_node.name = node
        new_node.parent = _get_id(target_world, parent) # if parent is None, will be automatically parented to root by the server

        logger.info("Created Camera node %s in world %s"%(repr(new_node),world))
        target_world.scene.nodes.append(new_node)

def create_entity_node(world, node, parent=None):
    """ Creates a node of type Entity.
    """

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        new_node = Entity()

        new_node.name = node
        new_node.parent = _get_id(target_world, parent) # if parent is None, will be automatically parented to root by the server

        logger.info("Created Entity node %s in world %s"%(repr(new_node),world))
        target_world.scene.nodes.append(new_node)

def remove_node(world, node):
    """ Removes a node.
    """

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]

        rem_node = _get_node(target_world, node)

        logger.info("Removing <%s : %s> NODE" % (str(rem_node),str(rem_node.id)))
        target_world.scene.nodes.remove(rem_node)

def create_box_mesh(world, scaleX=1, scaleY=1, scaleZ=1, diffuse=(1,1,1,1)):
    """ Creates a box mesh adds it to underworlds and returns the 
        ids of the mesh.
    """

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]

        logger.info("Created a new box mesh of x=%s y=%s z=%s m" % (str(scaleX), str(scaleY), str(scaleZ)))
        box = Box.create(scaleX,scaleY,scaleZ, diffuse)
        ctx.push_mesh(box)

        mesh_ids = [box.id]

        return mesh_ids

def add_mesh_to_node(world, node, mesh_ids):
    """ Attaches a previously created mesh to a Mesh node
    """

    logger.info("Starting add_mesh_to_node")
    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]

        mesh_node = _get_node(target_world, node)

        try:
            cur_mesh_ids = mesh_node.properties["mesh_ids"]
        except AttributeError as e:
            logger.error("Node is not of type Mesh.")
            sys.exit(1)

        cur_mesh_ids += mesh_ids
        mesh_node.properties["mesh_ids"] = cur_mesh_ids

        logger.info("Adding MESH for <%s : %s> with meshes %s" % (str(mesh_node),str(mesh_node.id), str(mesh_ids)))

        target_world.scene.nodes.update(mesh_node)

def add_sphere_mesh(world, node, radius=1, diffuse=(1,1,1,1)):
    """ Not Implemented.
    """
    raise NotImplementedError # Issue #9

def load_mesh(world, model):
    """ Loads meshes from a file and adds it to underworlds. Note
        that the meshes loaded are stand alone and not attached to
        a node.
    """

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]

        mesh_ids = []

        meshes = ModelLoader().load_meshes(model, ctx=ctx)
        for m in meshes.values():
            mesh_ids = mesh_ids + m

        logger.info("Loaded mesh %s with ids: %s" % (str(model), str(mesh_ids)))

        return mesh_ids

def remove_mesh(world, node, mesh_id):
    """ Removes a mesh from a Mesh node. If the last mesh is removed
        then the Mesh node will be removed as well.
    """

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]

        rem_mesh_node = _get_node(target_world, node)

        try:
            cur_mesh_ids = rem_mesh_node.properties["mesh_ids"]
        except AttributeError as e:
            logger.error("Node is not of type Mesh.")
            sys.exit(1)

        cur_mesh_ids.remove(mesh_id)

        if len(cur_mesh_ids) == 0:
            logger.info("Last mesh removed, removing node %s" % str(rem_mesh_node.id))
            remove_node(world, node)
        else:
            logger.info("Removing Mesh %s from node %s" % (str(mesh_id),str(rem_mesh_node.id)))
            rem_mesh_node.properties["mesh_ids"] = cur_mesh_ids
            target_world.scene.nodes.update(rem_mesh_node)



def set_parent(world, node, parent=None):
    """ Sets the parent node of a node.

    :parent: the node ID of the parent, or None or 'root' if the node is
             to be parented to the scene's root node.
    """

    if parent == "root":
        parent = None

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]

        updt_node = _get_node(target_world, node)

        if parent is not None:
            parent_node = _get_node(target_world, parent)
            updt_node.parent = parent_node.id
            logger.info("Setting parent of node %s to %s" % (repr(updt_node),repr(parent_node)))
        else:
            updt_node.parent = None
            logger.info("Setting parent of node %s to root" % (repr(updt_node)))


        target_world.scene.nodes.update(updt_node)
        
def format_name(world, node):
    """ Changes the node name to be a more human readable name, removing
    '_' and '-'.
    """

    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        fmt_node = _get_node(target_world, node)
        
        #Remove blender unique naming ids
        name_split = fmt_node.name.split(".")
        #Remove numbering assuming that '-' has been used to number.
        name_split = name_split[0].split("-")
        #Remove '_' spacing
        name_split = name_split[0].split("_")
        
        #Put back together using actual spaces
        fmt_node.name = ' '.join(name_split)
        
        target_world.scene.nodes.update(fmt_node)

def get_mesh(id):
    with underworlds.Context("edit-tool") as ctx:

        return ctx.mesh(id)

if __name__ == "__main__":

    print("Use uwds-edit to directly use these tools.")
