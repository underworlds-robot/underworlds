#!/usr/bin/env python
#-*- coding: UTF-8 -*-


import logging; logger = logging.getLogger("underworlds.testing")
logging.basicConfig(level=logging.DEBUG)

import unittest
import time

import underworlds
import underworlds.server

from underworlds.tools.loader import ModelLoader
from underworlds.types import MESH, CAMERA
import os.path as path

from underworlds.helpers.transformations import compose_matrix

PROPAGATION_TIME=0.05 # time to wait for node update notification propagation (in sec)

class TestModelLoading(unittest.TestCase):
    """Test for a bug where loading a second model reset the transformation of the first model
    """

    # workaround for https://github.com/grpc/grpc/issues/14088
    @classmethod
    def setUpClass(cls):
        cls.server = underworlds.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop(1).wait()


    def setUp(self):

        # workaround for https://github.com/grpc/grpc/issues/14088
        #self.server = underworlds.server.start()

        self.ctx = underworlds.Context("unittest - root anchoring transformation issue")

        # workaround for https://github.com/grpc/grpc/issues/14088
        self.ctx.reset()

    def test_basic_loading(self):

        world = self.ctx.worlds["test"]
        nodes = ModelLoader().load(path.join("res","tree.blend"), world="test")

        time.sleep(PROPAGATION_TIME)

        self.assertEqual(len(nodes), 2) # <BlenderRoot> and <tree>
        self.assertEqual(len(world.scene.nodes), 2)

        trees = world.scene.nodebyname("tree")
        self.assertEqual(len(trees), 1) # only one tree
        self.assertEqual(trees[0].type, MESH)

    def test_complex_loading(self):

        world = self.ctx.worlds["test"]
        nodes = ModelLoader().load(path.join("res","visibility.blend"), world="test")

        time.sleep(PROPAGATION_TIME)

        self.assertEqual(len(nodes), 8)
        self.assertEqual(len(world.scene.nodes), 8)

        self.assertEqual(len(world.scene.nodebyname("Camera1")), 1)
        cam1 = world.scene.nodebyname("Camera1")[0]
        self.assertEqual(cam1.type, CAMERA)
        self.assertFalse("mesh_ids" in cam1.properties)

        self.assertEqual(len(world.scene.nodebyname("Cube1")), 1)
        cube1 = world.scene.nodebyname("Cube1")[0]
        self.assertEqual(cube1.type, MESH)
        self.assertTrue("mesh_ids" in cube1.properties)


    def test_double_loading(self):

        world = self.ctx.worlds["test"]
        ModelLoader().load(path.join("res","tree.blend"), world="test")
        ModelLoader().load(path.join("res","tree.blend"), world="test")

        time.sleep(PROPAGATION_TIME)

        self.assertEqual(len(world.scene.nodes), 3) # one root and 2 trees

        trees = world.scene.nodebyname("tree")
        self.assertEqual(len(trees), 2) # should have 2 trees

        self.assertEqual(trees[0].properties["mesh_ids"], trees[1].properties["mesh_ids"])
        self.assertNotEqual(trees[0].id, trees[1].id)

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
        nodes = ModelLoader().load(path.join("res","cow.blend"), world="test")
        
        time.sleep(PROPAGATION_TIME)
        self.assertEqual(world.scene.nodes[tree.id].transformation[0,3], 2)
        
    def test_facing_property(self):
        
        world = self.ctx.worlds["test"]
        
        ModelLoader().load(path.join("res","facing.blend"), world="test")
        node = world.scene.nodebyname("ToNorth")[0]
        
        self.assertTrue("facing" in node.properties)
        
        world = self.ctx.worlds["test2"]

        ModelLoader().load(path.join("res","spatial.blend"), world="test2")
        
        node1 = world.scene.nodebyname("ToWest")[0]
        node2 = world.scene.nodebyname("Main")[0]
        node3 = world.scene.nodebyname("ToNorth")[0]
        
        self.assertTrue("facing" in node1.properties)
        self.assertTrue("facing" in node2.properties)
        self.assertTrue("facing" in node3.properties)

    def tearDown(self):
        self.ctx.close()

        # workaround for https://github.com/grpc/grpc/issues/14088
        #self.server.stop(1).wait()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestModelLoading)
     return suite

if __name__ == '__main__':
    unittest.main()
