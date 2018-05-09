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

def create_mesh_node(world, node, mesh_ids, parent="root"):
    
    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        logger.info("Attempting to create Mesh node")
        new_node = Mesh()
        
        new_node.properties["mesh_ids"] = mesh_ids

        new_node.name = node
        
        #Just add the node with root and parent so we can use the set_parent code to update to the correct parent.
        new_node.parent = target_world.scene.rootnode.id

        logger.info("Creating Mesh Node <%s : %s> with meshes %s"%(str(new_node),str(new_node.id),str(new_node.properties["mesh_ids"])))
        target_world.scene.nodes.append(new_node)
        if parent != "root":
            set_parent(world, new_node.id, parent)
        
def create_camera_node(world, node, aspect=0, horizontalfov=0, parent="root"):
    
    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        logger.info("Attempting to create Mesh node")
        new_node = Camera()
        new_node.properties["aspect"] = aspect
        new_node.properties["horizontalfov"] = horizontalfov
        
        new_node.name = node
        
        #Just add the node with root and parent so we can use the set_parent code to update to the correct parent.
        new_node.parent = target_world.scene.rootnode.id

        logger.info("Creating Camera Node <%s : %s>"%(str(new_node),str(new_node.id)))
        target_world.scene.nodes.append(new_node)
        if parent != "root":
            set_parent(world, new_node.id, parent)
        
def create_entity_node(world, node, parent="root"):
    
    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        logger.info("Attempting to create Mesh node")
        new_node = Entity()

        new_node.name = node
        
        #Just add the node with root and parent so we can use the set_parent code to update to the correct parent.
        new_node.parent = target_world.scene.rootnode.id

        logger.info("Creating Entity Node <%s : %s>"%(str(new_node),str(new_node.id)))
        target_world.scene.nodes.append(new_node)
        
        if parent != "root":
            set_parent(world, new_node.id, parent)
        
def remove_node(world, node):
    
    with underworlds.Context("edit-tool") as ctx:
        
        target_world = ctx.worlds[world]
        
        try:
            rem_node = target_world.scene.nodes[node]
        except KeyError as e:
            logger.error(str(e))
            sys.exit(1)
        
        logger.info("Removing <%s : %s> NODE" % (str(rem_node),str(rem_node.id)))
        target_world.scene.nodes.remove(rem_node)

def create_box_mesh(world, scaleX=1, scaleY=1, scaleZ=1, diffuse=(1,1,1,1)):
    
    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
    
        logger.info("Creating a box mesh of x=%s y=%s z=%s m" % (str(scaleX), str(scaleY), str(scaleZ)))
        box = Box.create(scaleX,scaleY,scaleZ, diffuse)
        ctx.push_mesh(box)
        
        mesh_ids = [box.id]
        
        return mesh_ids
        
def add_mesh_to_node(world, node, mesh_ids):

    logger.info("Starting add_mesh_to_node")
    with underworlds.Context("edit-tool") as ctx:
        
        target_world = ctx.worlds[world]
        
        try:
            mesh_node = target_world.scene.nodes[node]
        except KeyError as e:
            logger.error(str(e))
            sys.exit(1)
        
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
    raise NotImplementedError # issue 9
    
def load_mesh(world, model):

     with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]

        mesh_ids = []

        meshes = ModelLoader().load_meshes(model, ctx=ctx)
        for m in meshes.values():
            mesh_ids = mesh_ids + m
            
        logger.info("Loaded mesh %s with ids: %s" % (str(model), str(mesh_ids)))
        
        return mesh_ids
    
def remove_mesh(world, node, mesh_id):
    
    with underworlds.Context("edit-tool") as ctx:
        
        target_world = ctx.worlds[world]
        
        try:
            rem_mesh_node = target_world.scene.nodes[node]
        except KeyError as e:
            logger.error(str(e))
            sys.exit(1)
            
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
    
def set_parent(world, node, parent):
    
    with underworlds.Context("edit-tool") as ctx:
        
        target_world = ctx.worlds[world]
        
        try:
            updt_node = target_world.scene.nodes[node]
        except KeyError as e:
            logger.error(str(e))
            sys.exit(1)

        if parent != "root":
            try:
                parent_node = target_world.scene.nodes[parent]
            except KeyError as e:
                logger.error(str(e))
                sys.exit(1)

            updt_node.parent = parent_node.id
            parent_node.children.append(updt_node.id) #The requirement of this line might be a bug. Root node gets its children updated automatically, and the children is cleared automatically.
            
            logger.info("Setting parent of node %s to %s" % (str(updt_node.id),str(pare_node.id)))

        else:
            updt_node.parent = target_world.scene.rootnode.id
            logger.info("Setting parent of node %s to %s (root)" % (str(updt_node.id),str(target_world.scene.rootnode.id)))

        target_world.scene.nodes.update(updt_node)
        if parent != "root":
            target_world.scene.nodes.update(parent_node)
        
        
def get_mesh(id):
    with underworlds.Context("edit-tool") as ctx:
        
        return ctx.mesh(id)

if __name__ == "__main__":

    print("Use uwds-edit to directly use these tools.")
