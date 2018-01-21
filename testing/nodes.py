import time
import unittest

import logging; logger = logging.getLogger("underworlds")
logging.basicConfig(level=logging.DEBUG)

import underworlds
import underworlds.server
from underworlds.types import Node

PROPAGATION_TIME=0.02 # time to wait for node update notification propagation (in sec)

class TestNodes(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()

        self.ctx = underworlds.Context("unittest - nodes")
        self.ctx2 = underworlds.Context("unittest - nodes 2")


    def test_rootnode(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes
        root = world.scene.rootnode
        self.assertIsNotNone(root)

        root2 = None
        for n in nodes:
            if n.name == "root":
                root2 = n

        self.assertIsNotNone(root2)
        self.assertEquals(root2, root)

        root2.name = "toto"
        nodes.update(root2)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEquals(root, world.scene.rootnode) # the equality test is based on the ID, and the ID did not change
        self.assertEquals(world.scene.rootnode.name, "toto")

        world2 = self.ctx2.worlds["base"]
        self.assertEquals(world2.scene.rootnode, world.scene.rootnode)

    def tearDown(self):
        self.ctx.close()
        self.ctx2.close()
        self.server.stop(0).wait()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestNodes)
     return suite


if __name__ == '__main__':
    unittest.main()
