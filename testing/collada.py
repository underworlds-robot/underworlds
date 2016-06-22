import unittest
import time

import logging; logger = logging.getLogger("underworlds")
logging.basicConfig(level=logging.INFO)

import underworlds
import underworlds.server
from underworlds.types import Node
from underworlds.tools.loader import ModelLoader

PROPAGATION_TIME=0.02 # time to wait for node update notification propagation (in sec)

class TestCollada(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()
        time.sleep(0.1) # leave some time to the server to start
        self.ctx = underworlds.Context("unittest - collada")

    def test_frames(self):

        world = self.ctx.worlds["base"]
        ModelLoader(world.name).load("testing/res/monkey_mat.dae")

        time.sleep(PROPAGATION_TIME) # wait for propagation

        objects = ['Scene', 'Camera', 'Lamp', 'Monkey_002', 'Monkey_001', 'Monkey']

        self.assertItemsEqual(objects, [n.name for n in world.scene.nodes])

    def tearDown(self):
        self.ctx.close()
        self.server.stop(0)

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestCollada)
     return suite


if __name__ == '__main__':
    unittest.main()
