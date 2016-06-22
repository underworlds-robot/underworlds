import time
import unittest

import logging; logger = logging.getLogger("underworlds")
logging.basicConfig(level=logging.DEBUG)

import underworlds
import underworlds.server
from underworlds.types import Node

PROPAGATION_TIME=0.02 # time to wait for node update notification propagation (in sec)

class TestSingleUser(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()
        time.sleep(0.1) # leave some time to the server to start

        self.ctx = underworlds.Context("unittest - single user")
        self.ctx2 = underworlds.Context("unittest - single user 2")


    def test_initial_access(self):

        world = self.ctx.worlds["base"]
        self.assertIsNotNone(world)

        self.assertIsNotNone(world.scene)
        self.assertIsNotNone(world.timeline)

        nodes = world.scene.nodes
        self.assertEquals(len(nodes), 1) # the root node is always present

    def test_adding_nodes(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes
        
        self.assertEquals(len(nodes), 1)
        self.assertEquals(nodes[0].name, "root")

        n = Node()
        n.name = "test"
        nodes.append(n)

        self.assertEquals(len(nodes), 1) # the effective length of nodes takes a few ms to be updated
        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEquals(len(nodes), 2)

        # Get another reference to the 'base' world, and check
        # our node is still here.
        world1bis = self.ctx.worlds["base"]
        nodes1bis = world1bis.scene.nodes

        self.assertTrue(world is world1bis)
        self.assertTrue(nodes is nodes1bis)


        # Get another reference to the 'base' world, via another context.
        # The 2 worlds are not the same python object anymore but
        # should remain consistent
        world2 = self.ctx2.worlds["base"]
        nodes2 = world2.scene.nodes

        self.assertFalse(world is world2)
        self.assertFalse(nodes is nodes2)

        self.assertEquals(len(nodes2), 2)
        self.assertEquals(len(nodes2), 2)

        names = [n.name for n in nodes2]
        self.assertSetEqual(set(names), {"root", "test"})

        # Add a second node and check it is available to all references
        n2 = Node()
        n2.name = "test2"
        nodes.update(n2) # 'update' and 'append' are actually aliases

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEquals(len(nodes), 3)
        self.assertEquals(len(nodes2), 3)

        names2 = [n.name for n in nodes2]
        self.assertSetEqual(set(names2), {"root", "test", "test2"})
        # ensure the ordering is maintained
        self.assertListEqual(names, names2[:2])

        # Now alter 'world2' and make sure 'world' is updated accordingly
        n3 = Node()
        n3.name = "test3"
        nodes2.update(n3)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEquals(len(nodes), 4)
        names3 = [n.name for n in nodes]
        self.assertSetEqual(set(names3), {"root", "test", "test2", "test3"})

    def test_removing_nodes(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes
        
        n1 = Node()
        n1.name = "test"
        nodes.update(n1)
        n2 = Node()
        n2.name = "test2"
        nodes.update(n2)
        n3 = Node()
        n3.name = "test3"
        nodes.update(n3)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEquals(len(nodes), 4)

        # Get another reference to the 'base' world, and check
        # our nodes are here.
        world2 = self.ctx2.worlds["base"]
        nodes2 = world2.scene.nodes
        self.assertEquals(len(nodes2), 4)

        names = [n.name for n in nodes2] # store the order.

        # Now, remove a node at the end
        nodes.remove(n3)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEquals(len(nodes2), 3)
        names2 = [n.name for n in nodes2]
        names.remove(n3.name)
        self.assertListEqual(names, names2)

        # Now, remove a node in the middle
        nodes.remove(n1)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEquals(len(nodes2), 2)
        names2 = [n.name for n in nodes2]
        names.remove(n1.name)
        print("After two removals: %s" % names2)
        self.assertListEqual(names, names2)


        # Check the order is still ok if I append a node again
        nodes.update(n1)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEquals(len(nodes2), 3)
        names2 = [n.name for n in nodes2]
        self.assertListEqual(names, names2[:2])

    def tearDown(self):
        self.ctx.close()
        self.ctx2.close()
        self.server.stop(0)

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestSingleUser)
     return suite


if __name__ == '__main__':
    unittest.main(verbosity=2,failfast=False)

