#! /usr/bin/env python

import time
import unittest

import logging; logger = logging.getLogger("underworlds.testing.topology")
logging.basicConfig(level=logging.DEBUG)

import underworlds
import underworlds.server
from underworlds.types import Node, PROVIDER, READER

PROPAGATION_TIME=0.02 # time to wait for node update notification propagation (in sec)

class TestTopology(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()
        time.sleep(0.1) # leave some time to the server to start
        self.observer_ctx = underworlds.Context("unittest - observer")

    def test_topology(self):

        topo = self.observer_ctx.topology()
        self.assertEquals(len(topo.clients), 1)
        self.assertIn(self.observer_ctx.id, [c.id for c in topo.clients])
        self.assertEquals(len(topo.worlds), 0)

        self.observer_ctx.worlds["base"]

        topo = self.observer_ctx.topology()
        self.assertEquals(len(topo.worlds), 1)
        self.assertIn("base", topo.worlds)

        # Add a PROVIDER client
        provider_id = None

        provider_ctx = underworlds.Context("provider")
        world = provider_ctx.worlds["base"]
        world.scene.nodes.append(Node()) # create and add a random node
        provider_id = provider_ctx.id

        topo = self.observer_ctx.topology()

        self.assertEquals(len(topo.clients), 2)
        self.assertIn(provider_id, [c.id for c in topo.clients])
        provider = {c.id:c for c in topo.clients}[provider_id]
        self.assertIn("base", [l.world for l in provider.links])
        link = {l.world:l for l in provider.links}["base"]
        self.assertEquals(PROVIDER, link.type)
        last_provider_activity = link.last_activity.time

        # Add a READER client
        reader_id = None
        with underworlds.Context("reader") as reader_ctx:
            world2 = reader_ctx.worlds["base"]
            for n in world2.scene.nodes:
                print(n)
            reader_id = reader_ctx.id

        topo = self.observer_ctx.topology()

        self.assertEquals(len(topo.clients), 3)
        self.assertIn(reader_id, [c.id for c in topo.clients])
        reader = {c.id:c for c in topo.clients}[reader_id]
        self.assertIn("base", [l.world for l in reader.links])
        link2 = {l.world:l for l in reader.links}["base"]
        self.assertEquals(READER, link2.type)

        # Check the provider is still here
        provider = {c.id:c for c in topo.clients}[provider_id]
        self.assertIn("base", [l.world for l in provider.links])
        link = {l.world:l for l in provider.links}["base"]
        self.assertEquals(PROVIDER, link.type)
        # The provider has not been used: the last activity timestamp should be the same
        self.assertEquals(last_provider_activity, link.last_activity.time)

        # Modify the world from the PROVIDER context
        time.sleep(0.2)
        world.scene.nodes.append(Node()) # create and add a random node

        topo = self.observer_ctx.topology()

        # Check the provider is still here
        provider = {c.id:c for c in topo.clients}[provider_id]
        self.assertIn("base", [l.world for l in provider.links])
        link = {l.world:l for l in provider.links}["base"]
        self.assertEquals(PROVIDER, link.type)
        # The provider *has been used*: the last activity timestamp should be higher
        self.assertLess(last_provider_activity, link.last_activity.time)

        provider_ctx.close()



    def tearDown(self):
        self.observer_ctx.close()
        self.server.stop(0)

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestTopology)
     return suite


if __name__ == '__main__':
    unittest.main()
