import unittest
import time

import logging; logger = logging.getLogger("underworlds")
logging.basicConfig(level=logging.INFO)

import underworlds
import underworlds.server
from underworlds.types import Node, MESH
from underworlds.tools.loader import ModelLoader

PROPAGATION_TIME=0.02 # time to wait for node update notification propagation (in sec)

class TestMeshes(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()
        self.ctx = underworlds.Context("unittest - meshes")

    def test_frames(self):

        world = self.ctx.worlds["base"]
        ModelLoader(world.name).load("testing/res/monkey_mat.dae")

        time.sleep(PROPAGATION_TIME) # wait for propagation

        objects = ['Scene', 'Camera', 'Lamp', 'Monkey_002', 'Monkey_001', 'Monkey']

        self.assertItemsEqual(objects, [n.name for n in world.scene.nodes])

    def test_serialization(self):

        world = self.ctx.worlds["base"]
        ModelLoader(world.name).load("testing/res/base_visibility.dae")

        time.sleep(PROPAGATION_TIME) # wait for propagation

        for n in world.scene.nodes:
            if n.type == MESH:
                mesh = self.ctx.mesh(n.cad[0])
                # all the meshes in this scene are cubes, ie, 6 faces, ie 12 triangles
                self.assertEqual(len(mesh.faces), 12)

    def tearDown(self):
        self.ctx.close()
        self.server.stop(0).wait()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestMeshes)
     return suite


if __name__ == '__main__':
    unittest.main()
