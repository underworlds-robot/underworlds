import unittest

import underworlds.worlds
import underworlds.services

class TestCollada(unittest.TestCase):

    def setUp(self):
        self.bw = underworlds.worlds.get_world("base")

        self.bw.load("res/base.dae")

        self.objects = ["Cube", "Camera", "Lamp"]

        self.bs = self.bw.get_state()

    def test_frames(self):

        self.assertItemsEqual(self.objects, self.bs.list_objects())
        self.assertItemsEqual(self.objects, self.bs.list_frames())

if __name__ == '__main__':
    unittest.main()
