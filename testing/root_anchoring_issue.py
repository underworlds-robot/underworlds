#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import unittest

import underworlds
import underworlds.server

import logging; logger = logging.getLogger("underworlds.testing")
logging.basicConfig(level=logging.DEBUG)

import time
from underworlds.tools.loader import ModelLoader
import os.path as path

from underworlds.helpers.transformations import compose_matrix

PROPAGATION_TIME=0.001 # time to wait for node update notification propagation (in sec)

class TestRootAnchoring(unittest.TestCase):
    """Test for a bug where loading a second model reset the transformation of the first model
    """

    def setUp(self):
        self.server = underworlds.server.start()
        time.sleep(0.1) # leave some time to the server to start

        self.ctx = underworlds.Context("unittest - root anchoring transformation issue")


    def test_anchoring(self):

        world = self.ctx.worlds["test"]
        nodes = ModelLoader().load(path.join("res","tree.blend"), world="test")
        tree = world.scene.nodebyname("tree")[0]
        
        self.assertEqual(tree.transformation[0,3], 0)
                
        tree.transformation = compose_matrix(None, None, None, [2, 0, 0], None)
        world.scene.nodes.update(tree)
        
        time.sleep(PROPAGATION_TIME)
        self.assertEqual(world.scene.nodes[tree.id].transformation[0,3], 2)

        # ...loading another model reset the transformation of our original
        # model
        nodes = ModelLoader().load(path.join("res","monkey_mat.blend"), world="test")
        
        time.sleep(PROPAGATION_TIME)
        self.assertEqual(world.scene.nodes[tree.id].transformation[0,3], 2)
        

    def tearDown(self):
        self.ctx.close()
        self.server.stop(0)
        
    
if __name__ == '__main__':
    unittest.main()
