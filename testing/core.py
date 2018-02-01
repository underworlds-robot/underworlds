import unittest
import json

from underworlds.types import *
from underworlds.tools.primitives_3d import Box

import underworlds.underworlds_pb2

class TestCore(unittest.TestCase):

    def test_nodes(self):

        n = Node()

        self.assertIsNotNone(n.id)

        n.name = "test"
        self.assertEqual(n.type, UNDEFINED)

        serialized = n.serialize(underworlds.underworlds_pb2.Node)

        n2 = Node.deserialize(serialized)

        self.assertEqual(n, n2)


    def test_nodes_type(self):

        n = Mesh()
        self.assertEqual(n.type, MESH)
        self.assertTrue("mesh_ids" in n.properties)
        self.assertFalse("aspect" in n.properties)

        # no mesh data set, which violates the specification that the 'mesh_ids'
        # property is required.
        # This is checked when serializing the node, and should throw
        with self.assertRaises(UnderworldsError) as e:
            serialized = n.serialize(underworlds.underworlds_pb2.Node)

        cube = Box.create(10,10,10)
        # we do not need to push the mesh to the server for this test
        n.properties["mesh_ids"] = [cube.id]
        serialized = n.serialize(underworlds.underworlds_pb2.Node)

        n2 = Node.deserialize(serialized)

        self.assertEqual(n, n2)
        self.assertEqual(n.type, n2.type)
        self.assertEqual(n.name, n2.name)
        self.assertEqual(n.properties, n2.properties)


        n = Camera()
        self.assertEqual(n.type, CAMERA)
        self.assertTrue("aspect" in n.properties)
        self.assertTrue("horizontalfov" in n.properties)
        self.assertFalse("mesh_ids" in n.properties)

        n.properties["aspect"] = 0
        n.properties["horizontalfov"] = 0

        serialized = n.serialize(underworlds.underworlds_pb2.Node)

        n2 = Node.deserialize(serialized)

        self.assertEqual(n, n2)
        self.assertEqual(n.type, n2.type)
        self.assertEqual(n.name, n2.name)
        self.assertEqual(n.properties, n2.properties)




        n = Entity()
        self.assertEqual(n.type, ENTITY)
        self.assertFalse("aspect" in n.properties)
        self.assertFalse("horizontalfov" in n.properties)
        self.assertFalse("mesh_ids" in n.properties)

        serialized = n.serialize(underworlds.underworlds_pb2.Node)

        n2 = Node.deserialize(serialized)

        self.assertEqual(n, n2)
        self.assertEqual(n.type, n2.type)
        self.assertEqual(n.name, n2.name)
        self.assertEqual(n.properties, n2.properties)



def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestCore)
     #suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDiscriminateCompleteDialog))
     return suite

if __name__ == '__main__':
    unittest.main()
