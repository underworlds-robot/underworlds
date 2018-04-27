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

def create_node(world, node, parent="root"):
    
    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        new_node = Node()
        new_node.name = node
        new_node.type = ENTITY
        
        if parent != "root":
            try:
                parent = target_world.scene.nodes[parent]
            except KeyError as e:
                logger.error(str(e))
                sys.exit(1)

            new_node.parent = parent.id

        else:
            new_node.parent = target_world.scene.rootnode.id

        logger.info("Creating NODE <%s : %s>"%(str(new_node),str(new_node.id)))
        target_world.scene.nodes.append(new_node)
    
def remove_node(world, node):
    
    with underworlds.Context("edit-tool") as ctx:
        
        target_world = ctx.worlds[world]
        
        try:
            node = target_world.scene.nodes[node]
        except KeyError as e:
            logger.error(str(e))
            sys.exit(1)
        
        new_node = node
        logger.info("Removing <%s : %s> NODE" % (str(new_node),str(new_node.id)))
        target_world.scene.nodes.remove(new_node)

def add_box_mesh(world, node, scaleX=1, scaleY=1, scaleZ=1, diffuse=(1,1,1,1), crtNode=False, parent="root"):
    
    with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        
        try:
            node = target_world.scene.nodes[node]
        except KeyError as e:
            if crtNode == False:
                logger.error(str(e))
                sys.exit(1)
            else:
                create_node(world, node, parent)
                try:
                    node = target_world.scene.nodes[node]
                except KeyError as e:
                    logger.info("Unable to find or create node %s" % node)
                    logger.error(str(e))
                    sys.exit(1)
        
        new_node = node
        
        mesh_ids = []
    
        logger.info("Creating a box mesh of "+ str(sizes)+ " m")
        box = Box.create(sizeX,sizeY,sizeZ, diffuse)
        ctx.push_mesh(box)
        mesh_ids = [box.id]
        
        new_node.type = MESH
        new_node.hires += mesh_ids
        new_node.cad += mesh_ids
        
        logger.info("Adding MESH for <%s : %s> with meshes %s" % (str(new_node),str(new_node.id), str(mesh_ids)))
        
        target_world.scene.nodes.update(new_node)
    
def add_sphere_mesh(world, node, radius=1, diffuse=(1,1,1,1), crtNode=False, parent="root"):
    raise NotImplementedError # issue 9
    
def add_load_mesh(world, node, model, crtNode=False, parent="root"):

     with underworlds.Context("edit-tool") as ctx:

        target_world = ctx.worlds[world]
        
        try:
            node = target_world.scene.nodes[node]
        except KeyError as e:
            if crtNode == False:
                logger.error(str(e))
                sys.exit(1)
            else:
                create_node(world, node, parent)
                try:
                    node = target_world.scene.nodes[node]
                except KeyError as e:
                    logger.info("Unable to find or create node %s" % node)
                    logger.error(str(e))
                    sys.exit(1)
                    
        new_node = node

        mesh_ids = []

        meshes = ModelLoader().load_meshes(model, ctx=ctx)
        for m in meshes.values():
            mesh_ids = mesh_ids + m
        new_node.type = MESH
        new_node.hires += mesh_ids
        new_node.cad += mesh_ids
        logger.info("Adding MESH for <%s : %s> with meshes %s" % (str(new_node),str(new_node.id), str(mesh_ids)))
        
        target_world.scene.nodes.update(new_node)
    
def remove_meshes(world, node):
    
    with underworlds.Context("edit-tool") as ctx:
        
        try:
            node = target_world.scene.nodes[node]
        except KeyError as e:
            logger.error(str(e))
            sys.exit(1)
        
        new_node = node
        logger.info("Removing MESH %s for <%s : %s >" % (str(new_node.cad),str(new_node),str(new_node.id)))
        new_node.cad = []
        new_node.type = ENTITY
        
        target_world.scene.nodes.update(new_node)
    
def set_parent(world, node, parent):
    
    with underworlds.Context("edit-tool") as ctx:
        
        try:
            node = target_world.scene.nodes[node]
        except KeyError as e:
            logger.error(str(e))
            sys.exit(1)

        new_node = node

        if args.parent != "root":
            try:
                parent = target_world.scene.nodes[parent]
            except KeyError as e:
                logger.error(str(e))
                sys.exit(1)

            new_node.parent = parent.id

        else:
            new_node.parent = target_world.scene.rootnode.id

        target_world.scene.nodes.update(new_node)

if __name__ == "__main__":

    print("Use uwds-edit to directly use these tools.")
