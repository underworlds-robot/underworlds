import unittest

import underworlds.worlds
import underworlds.services

class TestVisibility(unittest.TestCase):

    def setUp(self):
        self.bw = underworlds.worlds.get_world("base")

        self.bw.load("res/base_visibility.dae")
        self.bs = self.bw.get_state()

    def test_visibility(self):

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


if __name__ == '__main__':
    unittest.main()
