import time
import unittest

import logging; logger = logging.getLogger("underworlds")
logging.basicConfig(level=logging.DEBUG)

import underworlds
import underworlds.server
from underworlds.types import Node
from underworlds.helpers.geometry import get_world_transform

PROPAGATION_TIME=0.05 # time to wait for node update notification propagation (in sec)

class TestParenting(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()

        self.ctx = underworlds.Context("unittest - parenting")

    def test_base_parent(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes

        parent = Node()
        child = Node()

        child.parent = parent.id
        child.translate([1,1,1])

        nodes.append([parent, child])

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 3) # root node + our 2 nodes

        self.assertEqual(nodes[child.id].transform[3,0], 1)
        world_pose = get_world_transform(world.scene, child)
        self.assertEqual(world_pose[3,0], 1)


        parent.translate([1,1,1])
        nodes.update(parent)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(nodes[child.id].transform[3,0], 1)
        world_pose = get_world_transform(world.scene, child)
        self.assertEqual(world_pose[3,0], 2)


    def test_delete_parent(self):
        pass

    def tearDown(self):
        self.ctx.close()
        self.ctx2.close()
        self.server.stop(0).wait()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestParenting)
     return suite


if __name__ == '__main__':
    unittest.main()
