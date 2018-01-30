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

    def test_default_parent(self):
        """ Checks that new node are parented to root node by default.
        """

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes

        node = Node()
        self.assertIsNone(node.parent)

        nodes.append(node)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(nodes[node.id].parent, world.scene.rootnode.id)

    def test_base_parent(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes

        parent = Node()
        child = Node()

        child.parent = parent.id

        nodes.append([parent, child])

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 3) # root node + our 2 nodes

        updated_child = nodes[child.id]
        updated_parent = nodes[parent.id]

        self.assertEqual(child.parent, updated_child.parent)
        self.assertEqual(parent.id, updated_parent.id)
        self.assertEqual(updated_child.parent, updated_parent.id)

        self.assertEqual(updated_parent.parent, world.scene.rootnode.id)

    def test_multiple_children(self):

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes

        parent = Node()
        child1 = Node()
        child2 = Node()
        child3 = Node()

        child1.parent = parent.id
        child2.parent = parent.id
        child3.parent = parent.id

        nodes.append([parent, child1, child2, child3])

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 5) # root node + our nodes

        self.assertEqual(nodes[child1.id].parent, parent.id)
        self.assertEqual(nodes[child2.id].parent, parent.id)
        self.assertEqual(nodes[child3.id].parent, parent.id)

        nodes.remove(child1)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 4) # root node + our nodes

        self.assertEqual(nodes[child2.id].parent, parent.id)
        self.assertEqual(nodes[child3.id].parent, parent.id)


    def test_delete_parent(self):
        """ When a parent is deleted, the orphan children should be re-parented to
        the root node.
        """

        world = self.ctx.worlds["base"]
        nodes = world.scene.nodes

        parent = Node()
        child1 = Node()
        child2 = Node()
        childchild1 = Node()

        child1.parent = parent.id
        child2.parent = parent.id
        childchild1.parent = child1.id

        nodes.append([parent, child1, child2, childchild1])

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 5) # root node + our 2 nodes

        self.assertEqual(nodes[child1.id].parent, parent.id)
        self.assertEqual(nodes[child2.id].parent, parent.id)
        self.assertEqual(nodes[childchild1.id].parent, child1.id)

        nodes.remove(parent)

        time.sleep(PROPAGATION_TIME) # wait for propagation
        self.assertEqual(len(nodes), 4) # root node + child 

        self.assertEqual(nodes[child1.id].parent, world.scene.rootnode.id)
        self.assertEqual(nodes[child2.id].parent, world.scene.rootnode.id)
        self.assertEqual(nodes[childchild1.id].parent, child1.id)




    def tearDown(self):
        self.ctx.close()
        self.server.stop(0).wait()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestParenting)
     return suite


if __name__ == '__main__':
    unittest.main()
