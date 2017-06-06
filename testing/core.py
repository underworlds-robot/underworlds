import unittest
import json

from underworlds.types import Node, MESH

import underworlds.underworlds_pb2

class TestCore(unittest.TestCase):

    def test_nodes(self):

        n = Node()

        self.assertIsNotNone(n.id)

        n.name = "test"
        n.type = MESH

        serialized = n.serialize(underworlds.underworlds_pb2.Node)

        n2 = Node.deserialize(serialized)

        self.assertEqual(n, n2)


def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestCore)
     #suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDiscriminateCompleteDialog))
     return suite

if __name__ == '__main__':
    unittest.main()
