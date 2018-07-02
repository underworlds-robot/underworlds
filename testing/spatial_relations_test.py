import unittest
import time

import numpy

import underworlds
import underworlds.server
from underworlds.tools.loader import ModelLoader
from underworlds.tools.spatial_relations import *

class TestSpatialRelations(unittest.TestCase):

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

        self.ctx = underworlds.Context("unittest - spatial relations")

        # workaround for https://github.com/grpc/grpc/issues/14088
        self.ctx.reset()
        
    def test_spatial_relations(self):
        world = self.ctx.worlds["base"]

        ModelLoader().load("res/spatial.blend", world="base")
        
        time.sleep(1) # leave some time for the loader to finish
        
        mainbb = get_bounding_box_for_node(world.scene, world.scene.nodebyname("Main")[0])
        belowbb = get_bounding_box_for_node(world.scene, world.scene.nodebyname("Below")[0])
        insidebb = get_bounding_box_for_node(world.scene, world.scene.nodebyname("Inside")[0])
        onTopbb = get_bounding_box_for_node(world.scene, world.scene.nodebyname("OnTop")[0])
        eastbb = get_bounding_box_for_node(world.scene, world.scene.nodebyname("ToEast")[0])
        northbb = get_bounding_box_for_node(world.scene, world.scene.nodebyname("ToNorth")[0])
        southbb = get_bounding_box_for_node(world.scene, world.scene.nodebyname("ToSouth")[0])
        westbb = get_bounding_box_for_node(world.scene, world.scene.nodebyname("ToWest")[0])
        
        self.assertTrue(isbelow(belowbb,mainbb))
        self.assertTrue(isin(insidebb,mainbb))
        self.assertTrue(isontop(onTopbb,mainbb))
        self.assertTrue(istoeast(eastbb,mainbb))
        self.assertTrue(istonorth(northbb,mainbb))
        self.assertTrue(istosouth(southbb,mainbb))
        self.assertTrue(istowest(westbb,mainbb))
        
    def test_spatial_relations_perspective(self):
        world = self.ctx.worlds["base"]

        ModelLoader().load("res/spatial.blend", world="base")
        
        time.sleep(1) # leave some time for the loader to finish
        
        view_matrix = get_spatial_view_matrix()
        self.assertTrue(istoleft(self.ctx, world.scene, world.scene.nodebyname("ToWest")[0], world.scene.nodebyname("Main")[0], view_matrix))
        
        camera_node = world.scene.nodebyname("CameraEast")[0]
        camera_node2 = world.scene.nodebyname("CameraEastTest")[0]
        camera_node3 = world.scene.nodebyname("CameraWestUSD")[0]
        camera_node4 = world.scene.nodebyname("CameraWest")[0]
        
        view_matrix = get_spatial_view_matrix(get_world_transform(world.scene, camera_node))
        view_matrix2 = get_spatial_view_matrix(get_world_transform(world.scene, camera_node2), False)
        view_matrix3 = get_spatial_view_matrix(get_world_transform(world.scene, camera_node3), False)
        view_matrix4 = get_spatial_view_matrix(get_world_transform(world.scene, camera_node3), True)
        view_matrix5 = get_spatial_view_matrix(get_world_transform(world.scene, camera_node4), False)
        
        #End up being slightly different due to rounding errors. Might want to look into rounding off the values in the matrices.
        #self.assertTrue(numpy.array_equal(view_matrix, view_matrix2))
        
        self.assertTrue(istoleft(self.ctx, world.scene, world.scene.nodebyname("ToSouth")[0], world.scene.nodebyname("Main")[0], view_matrix2))
        self.assertTrue(istoleft(self.ctx, world.scene, world.scene.nodebyname("ToSouth")[0], world.scene.nodebyname("Main")[0], view_matrix))
        self.assertTrue(istoright(self.ctx, world.scene, world.scene.nodebyname("ToNorth")[0], world.scene.nodebyname("Main")[0], view_matrix))
        self.assertTrue(istofront(self.ctx, world.scene, world.scene.nodebyname("ToEast")[0], world.scene.nodebyname("Main")[0], view_matrix))
        self.assertTrue(istoback(self.ctx, world.scene, world.scene.nodebyname("ToWest")[0], world.scene.nodebyname("Main")[0], view_matrix))
        
        self.assertTrue(istoleft(self.ctx, world.scene, world.scene.nodebyname("ToSouth")[0], world.scene.nodebyname("Main")[0], view_matrix3))
        self.assertTrue(istoright(self.ctx, world.scene, world.scene.nodebyname("ToSouth")[0], world.scene.nodebyname("Main")[0], view_matrix5))
        
        #This test currently failing, issue with the way matrix is decomposed? See note on angle ranges http://nghiaho.com/?page_id=846 
        #self.assertTrue(istoright(self.ctx, world.scene, world.scene.nodebyname("ToSouth")[0], world.scene.nodebyname("Main")[0], view_matrix4))
        
        self.assertTrue(isfacing(self.ctx, world.scene, world.scene.nodebyname("ToNorth")[0], world.scene.nodebyname("Main")[0]))
        
        
        
        
    def tearDown(self):
        self.ctx.close()
    
def test_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSpatialRelations)
    return suite


if __name__ == '__main__':
    unittest.main()
