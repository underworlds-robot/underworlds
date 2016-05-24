import unittest
import time

import underworlds
from underworlds.server import Server
from underworlds.types import Node
from underworlds.tools.loader import ModelLoader


class TestCollada(unittest.TestCase):

    def setUp(self):
        self.server = Server()
        self.server.start()
        time.sleep(0.1) # leave some time to the server to start
        self.ctx = underworlds.Context("unittest - collada")

    def test_frames(self):

        world = self.ctx.worlds["base"]
        ModelLoader(world.name).load("res/monkey_mat.dae")

        objects = ['Scene', 'Camera', 'Lamp', 'Monkey_002', 'Monkey_001', 'Monkey']

        self.assertItemsEqual(objects, [n.name for n in world.scene.nodes])

    def tearDown(self):
        self.ctx.close()
        self.server.stop()
        self.server.join()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestCollada)
     return suite


if __name__ == '__main__':
    unittest.main()
