import time
import unittest

import logging; logger = logging.getLogger("underworlds.testing.topology")
logging.basicConfig(level=logging.DEBUG)

import underworlds
from underworlds.server import Server
from underworlds.types import Node, PROVIDER, READER

PROPAGATION_TIME=0.001 # time to wait for node update notification propagation (in sec)

class TestTopology(unittest.TestCase):

    def setUp(self):
        self.server = Server()
        self.server.start()
        time.sleep(0.1) # leave some time to the server to start
        self.observer_ctx = underworlds.Context("unittest - observer")

    def test_topology(self):

        topo = self.observer_ctx.topology()
        self.assertEquals(len(topo['clients']), 1)
        self.assertIn(self.observer_ctx.id, topo['clients'])
        self.assertEquals(len(topo['worlds']), 0)

        self.observer_ctx.worlds["base"]

        topo = self.observer_ctx.topology()
        self.assertEquals(len(topo['worlds']), 1)
        self.assertIn("base", topo['worlds'])

        # Add a PROVIDER client
        provider_id = None
        with underworlds.Context("provider") as provider_ctx:
            world = provider_ctx.worlds["base"]
            world.scene.nodes.update(Node()) # create and add a random node
            provider_id = provider_ctx.id

        topo = self.observer_ctx.topology()

        self.assertEquals(len(topo['clients']), 2)
        self.assertIn(provider_id, topo['clients'])
        self.assertIn("base", topo['clients'][provider_id])
        self.assertEquals(PROVIDER, topo['clients'][provider_id]['base'][0])

        # Add a READER client
        reader_id = None
        with underworlds.Context("reader") as reader_ctx:
            world = reader_ctx.worlds["base"]
            for n in world.scene.nodes:
                print(n)
            reader_id = reader_ctx.id

        topo = self.observer_ctx.topology()
        self.assertEquals(len(topo['clients']), 3)
        self.assertIn(reader_id, topo['clients'])
        self.assertIn("base", topo['clients'][reader_id])
        self.assertEquals(READER, topo['clients'][reader_id]['base'][0])

    def tearDown(self):
        self.observer_ctx.close()
        self.server.stop()
        self.server.join()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestTopology)
     return suite


if __name__ == '__main__':
    unittest.main()
