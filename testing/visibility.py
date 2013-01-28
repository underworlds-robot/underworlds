import unittest
import time

import underworlds
from underworlds.server import Server

class TestVisibility(unittest.TestCase):

    def setUp(self):
        self.server = Server()
        self.server.start()
        time.sleep(0.1) # leave some time to the server to start

        self.ctx = underworlds.Context("unittest - visibility")

    def test_visibility(self):
        world = self.ctx.worlds["base"]
        world.load("res/base_visibility.dae")
        self.bs = world.get_state()


        self.assertTrue(False, "This test is not expected to run... 'visibility_monitor' should first be turned into some sort of library.")

        self.assertTrue(underworlds.services.visibility(self.bs, "Cube1", "Camera1"))
        self.assertFalse(underworlds.services.visibility(self.bs, "Cube2", "Camera1"))

        self.assertTrue(underworlds.services.visibility(self.bs, "Cube1", "Camera2"))
        self.assertTrue(underworlds.services.visibility(self.bs, "Cube2", "Camera2"))

        self.assertTrue(underworlds.services.visibility(self.bs, "Cube2", "Camera3"))

        self.assertFalse(underworlds.services.visibility(self.bs, "Cube2", "Camera4"))

        self.assertFalse(underworlds.services.visibility(self.bs, "Cube1", "Camera5"))
        self.assertFalse(underworlds.services.visibility(self.bs, "Cube2", "Camera5"))

        self.assertFalse(underworlds.services.visibility(self.bs, "Cube1", "Camera6"))
        self.assertTrue(underworlds.services.visibility(self.bs, "Cube2", "Camera6"))

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestVisibility)
     return suite


if __name__ == '__main__':
    unittest.main()
