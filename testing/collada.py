import unittest

import underworlds
from underworlds.server import Server
from underworlds.types import Node


class TestCollada(unittest.TestCase):

    def setUp(self):
        self.server = Server()
        self.server.start()
        time.sleep(0.1) # leave some time to the server to start
        self.ctx = underworlds.Context("unittest - collada")

    def test_frames(self):

        world = self.ctx.worlds["base"]
        world.load("res/base.dae")

        objects = ["Cube", "Camera", "Lamp"]

        bs = world.get_state()

        self.assertItemsEqual(objects, bs.list_objects())
        self.assertItemsEqual(objects, bs.list_frames())

    def tearDown(self):
        self.ctx.close()
        self.server.stop()
        self.server.join()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestCollada)
     return suite


if __name__ == '__main__':
    unittest.main()
