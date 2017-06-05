#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import underworlds
from underworlds.helpers.geometry import get_bounding_box_for_node, calc_trans_matrix
from underworlds.types import MESH
from underworlds.tools.loader import ModelLoader
import logging; loadLogger = logging.getLogger("underworlds.model_loader")
import os.path as path
import sys
import underworlds.server
from math import *
import numpy as np
import json

def load(objName):
    #Get Underworlds path and put together path for blender file.
    #Using simplified models to speed up loading for Underworlds and increase stability
    if objName == "giraffe":
        objName = "giraffe2"
    if objName == "Monkey":
        objName = "Monkey2"
    filename = "res\%s.blend" %  (objName)

    loadLogger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    #Load model
    nodes = ModelLoader().load(filename, world="test")
    ids = [node.id for node in nodes if node.name == objName]
    if ids:
        myID = ids[0]
        msg = "test_move load: ID = %s" % (myID)
        logging.info(msg)
        return myID
    logging.info("test_move load: Could not get ID")
    
if __name__ == "__main__":
    with open("res\load.json") as f:
    
        pparams = json.dumps(json.load(f))
        objsToLoad = pparams["loadable_objects"]
        
        for item in objsToLoad:
            objName = item["filename"]
            uwID = load(objName)
            
            posX = item["position"]["x"]
            posZ = item["position"]["y"]
            posY = item["position"]["z"]
            rotX = item["rotation"]["x"]
            rotZ = item["rotation"]["y"]
            rotY = item["rotation"]["z"]
            scaleX = item["scaling"]["x"]
            scaleZ = item["scaling"]["y"]
            scaleY = item["scaling"]["z"]
            
            #Convert from degrees to radians
            xrot = xrot * 0.01745329252
            yrot = yrot * 0.01745329252
            zrot = zrot * 0.01745329252
        
            node.transformation = calc_trans_matrix(x, y, z, xrot, yrot, zrot, xScale, yScale, zScale, "xConv")
        
            scene.nodes.update(node)
        
        print "Done"
