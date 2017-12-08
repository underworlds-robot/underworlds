import unittest
import time

import underworlds
import underworlds.server
from underworlds.tools.loader import ModelLoader
from underworlds.tools.spatial_relations import *

class TestSpatialRelations(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()
        time.sleep(0.1) # leave some time to the server to start

        self.ctx = underworlds.Context("unittest - spatial relations")
        
    def test_spatial_relations(self):
        world = self.ctx.worlds["base"]

        ModelLoader().load("res/spatial.blend", world="base")
        
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
    
def test_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSpatialRelations)
    return suite


if __name__ == '__main__':
    unittest.main()