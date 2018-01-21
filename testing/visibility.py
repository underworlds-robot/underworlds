#! /usr/bin/env python

import unittest
import time

import underworlds
import underworlds.server
from underworlds.tools.loader import ModelLoader
from underworlds.tools.visibility import VisibilityMonitor

class TestVisibility(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()

        self.ctx = underworlds.Context("unittest - visibility")

    def test_visibility(self):
        world = self.ctx.worlds["base"]

        ModelLoader().load("res/visibility.blend", world="base")

        cube1 = world.scene.nodebyname("Cube1")[0]
        cube2 = world.scene.nodebyname("Cube2")[0]
        #visibility = VisibilityMonitor(self.ctx, world, debug=True)
        visibility = VisibilityMonitor(self.ctx, world)

        results = visibility.compute_all()

        self.assertItemsEqual(["Camera1", "Camera2", "Camera3", "Camera4", "Camera5"], \
                              results.keys())

        self.assertItemsEqual([cube1, cube2], results["Camera1"])
        self.assertItemsEqual([cube1, cube2], results["Camera2"])
        self.assertItemsEqual([cube2], results["Camera3"])
        self.assertItemsEqual([cube1], results["Camera4"])
        self.assertListEqual([], results["Camera5"])

    def tearDown(self):
        self.ctx.close()
        self.server.stop(0).wait()


def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestVisibility)
     return suite


if __name__ == '__main__':
    unittest.main()
