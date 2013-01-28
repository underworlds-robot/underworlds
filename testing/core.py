import unittest

from underworlds.types import Node, MESH

class TestCore(unittest.TestCase):

    def test_nodes(self):

        n = Node()

        self.assertIsNotNone(n.id)

        n.name = "test"
        n.type = MESH

        serialized = n.serialize()

        n2 = Node.deserialize(serialized)

        self.assertEquals(n, n2)


def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestCore)
     #suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDiscriminateCompleteDialog))
     return suite

if __name__ == '__main__':
    unittest.main()
