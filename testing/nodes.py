import time
import unittest

import logging; logger = logging.getLogger("underworlds")
logging.basicConfig(level=logging.DEBUG)

import underworlds
import underworlds.server
from underworlds.types import Node

PROPAGATION_TIME=0.05 # time to wait for node update notification propagation (in sec)

class TestNodes(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()

        self.ctx = underworlds.Context("unittest - nodes")
        self.ctx2 = underworlds.Context("unittest - nodes 2")

    def test_initial_access(self):

        world = self.ctx.worlds["base"]
        self.assertIsNotNone(world)

        self.assertIsNotNone(world.scene)
        self.assertIsNotNone(world.timeline)

        nodes = world.scene.nodes
        self.assertEqual(len(nodes), 1) # the root node is always present

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
        self.assertEqual(root2, root)

        root2.name = "toto"
        nodes.update(root2)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(root, world.scene.rootnode) # the equality test is based on the ID, and the ID did not change
        self.assertEqual(world.scene.rootnode.name, "toto")

        world2 = self.ctx2.worlds["base"]
        self.assertEqual(world2.scene.rootnode, world.scene.rootnode)


    def test_adding_nodes(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes
        
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].name, "root")

        n = Node()
        n.name = "test"
        nodes.append(n)

        self.assertEqual(len(nodes), 1) # the effective length of nodes takes a few ms to be updated
        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 2)

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

        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes2), 2)

        names = [n.name for n in nodes2]
        self.assertSetEqual(set(names), {"root", "test"})

        # Add a second node and check it is available to all references
        n2 = Node()
        n2.name = "test2"
        nodes.update(n2) # 'update' and 'append' are actually aliases

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 3)
        self.assertEqual(len(nodes2), 3)

        names2 = [n.name for n in nodes2]
        self.assertSetEqual(set(names2), {"root", "test", "test2"})
        # ensure the ordering is maintained
        self.assertListEqual(names, names2[:2])

        # Now alter 'world2' and make sure 'world' is updated accordingly
        n3 = Node()
        n3.name = "test3"
        nodes2.update(n3)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 4)
        names3 = [n.name for n in nodes]
        self.assertSetEqual(set(names3), {"root", "test", "test2", "test3"})

    def test_accessing_nodes(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes
        
        n1 = Node()
        n2 = Node()
        nodes.append(n1)
        nodes.append(n2)

        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(n1, nodes[n1.id])
        self.assertEqual(n2, nodes[n2.id])

        with self.assertRaises(IndexError) as context:
            nodes["non-existing-id"]

        with self.assertRaises(IndexError) as context:
            nodes[len(nodes)]


    def test_removing_nodes(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes
        
        n1 = Node()
        n1.name = "test1"
        nodes.update(n1)
        n2 = Node()
        n2.name = "test2"
        nodes.update(n2)
        n3 = Node()
        n3.name = "test3"
        nodes.update(n3)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 4) # the 3 added nodes + root node

        # Get another reference to the 'base' world, and check
        # our nodes are here.
        world2 = self.ctx2.worlds["base"]
        nodes2 = world2.scene.nodes
        self.assertEqual(len(nodes2), 4) # the 3 added nodes + root node

        names = [n.name for n in nodes2] # store the order.

        # Now, remove a node at the end
        nodes.remove(n3)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(nodes2), 3)
        names2 = [n.name for n in nodes2]
        names.remove(n3.name)
        self.assertListEqual(names, names2)

        # Now, remove a node in the middle
        nodes.remove(n1)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(nodes2), 2)
        names2 = [n.name for n in nodes2]
        names.remove(n1.name)
        print("After two removals: %s" % names2)
        self.assertListEqual(names, names2)


        # Check the order is still ok if I append a node again
        nodes.update(n1)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(nodes2), 3)
        names2 = [n.name for n in nodes2]
        self.assertListEqual(names, names2[:2])


    def test_multiple_nodes(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes
        
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].name, "root")

        new_nodes = [Node() for i in range(10)]

        nodes.append(new_nodes)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 11)

        nodes.remove(new_nodes)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 1)

    def tearDown(self):
        self.ctx.close()
        self.ctx2.close()
        self.server.stop(0).wait()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestNodes)
     return suite


if __name__ == '__main__':
    unittest.main()
