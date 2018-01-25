#! /usr/bin/env python

import time
import unittest

from concurrent.futures import ThreadPoolExecutor

import logging; logger = logging.getLogger("underworlds.testing.waitforchanges")
logging.basicConfig(level=logging.DEBUG)

import underworlds
import underworlds.server
from underworlds.types import Node
import underworlds.underworlds_pb2 as gRPC

PROPAGATION_TIME=0.05 # time to wait for node update notification propagation (in sec)

def wait_for_changes(world):

    change = world.scene.waitforchanges(0.5)
    return change


class TestWaitforchanges(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()

        self.ctx1 = underworlds.Context("unittest - waitforchanges - user1")
        self.ctx2 = underworlds.Context("unittest - waitforchanges - user2")

        self.executor = ThreadPoolExecutor(max_workers=1)


    def test_adding_nodes(self):

        world1 = self.ctx1.worlds["base"]
        world2 = self.ctx2.worlds["base"]

        # start to wait for changes.
        # First, we do not perform any change -> should timeout
        future = self.executor.submit(wait_for_changes, world2)
        self.assertIsNone(future.result())

        # Second, we make a change -> creation of a new node
        future = self.executor.submit(wait_for_changes, world2)

        n = Node()
        n.name = "test"
        world1.scene.append_and_propagate(n)

        change = future.result()
        self.assertIsNotNone(change)
        self.assertEquals(change[0], n.id)
        self.assertEquals(change[1], gRPC.Invalidation.NEW)

        # Now, we move the node
        future = self.executor.submit(wait_for_changes, world2)
        n.translate([0,1,0])
        world1.scene.update_and_propagate(n)

        change = future.result()
        self.assertIsNotNone(change)
        self.assertEquals(change[0], n.id)
        self.assertEquals(change[1], gRPC.Invalidation.UPDATE)

        # Finally, we remove the node
        future = self.executor.submit(wait_for_changes, world2)
        world1.scene.remove_and_propagate(n)

        change = future.result()
        self.assertIsNotNone(change)
        self.assertEquals(change[0], n.id)
        self.assertEquals(change[1], gRPC.Invalidation.DELETE)

        # Lastly, we do nothing again -> should timeout
        future = self.executor.submit(wait_for_changes, world2)
        self.assertIsNone(future.result())



    def tearDown(self):
        self.ctx1.close()
        self.ctx2.close()
        self.server.stop(0).wait()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestWaitforchanges)
     return suite


if __name__ == '__main__':
    unittest.main(verbosity=2,failfast=False)

