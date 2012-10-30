import unittest

from underworlds import node

class TestCore(unittest.TestCase):

    def test_nodes(self):

        n = node.Node()

        self.assertIsNotNone(n.id)

        n.name = "test"
        n.type = node.MESH

        serialized = n.serialize()

        n2 = node.Node.deserialize(serialized)

        self.assertEquals(n, n2)


if __name__ == '__main__':
    unittest.main()
