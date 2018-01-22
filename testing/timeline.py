import time
import unittest

import logging; logger = logging.getLogger("underworlds.testing." + __name__)
logging.basicConfig(level=logging.DEBUG)

import underworlds
from underworlds.errors import *
import underworlds.server
from underworlds.tools.loader import ModelLoader

from underworlds.types import Situation, createevent


PROPAGATION_TIME=0.001 # time to wait for node update notification propagation (in sec)

class TestTimeline(unittest.TestCase):

    def setUp(self):
        self.server = underworlds.server.start()

        self.t0 = time.time()
        self.ctx = underworlds.Context("unittest - timeline")
        self.ctx2 = underworlds.Context("unittest - timeline2")

        self.world = self.ctx.worlds["base"]
        self.timeline = self.world.timeline

    def test_base(self):

        self.t3 = time.time()

        self.assertIsNotNone(self.timeline)
        t1 = self.timeline.origin
        t2 = self.timeline.origin

        self.assertEqual(t1, t2)
        self.assertTrue(self.t0 < t1 < self.t3)

    def test_events_base(self):

        s = Situation()

        self.timeline.start(s)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(self.timeline), 1)

        self.assertIn(s, self.timeline)


        self.timeline.end(s)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertIn(s, self.timeline)
        self.assertEqual(len(self.timeline), 1)

        s = createevent()

        self.timeline.start(s)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertIn(s, self.timeline)
        self.assertEqual(len(self.timeline), 2)

        self.timeline.end(s) # this is a no-op for events
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertIn(s, self.timeline)
        self.assertEqual(len(self.timeline), 2)


    def _test_events_callback(self):
        event = Event()

        ok = False
        def onevt(self, evt):
            ok = True

        self.timeline.on(event).call(onevt)

        self.timeline.event(event)
        time.sleep(PROPAGATION_TIME)
        self.assertTrue(ok)

    def _test_modelloading(self):

        event = Event(Event.MODELLOAD)

        with self.assertRaises(TimeoutError):
            self.timeline.on(event).wait(timeout = 0.1)

        ModelLoader().load("res/base.dae", world=self.world)

        self.timeline.on(event).wait(timeout = 0.1) # should not throw a timeouterror

        ok = False
        def onload(self, evt):
            ok = True

        self.timeline.on(event).call(onload)
        ModelLoader(self.world).load("res/base.dae")
        time.sleep(PROPAGATION_TIME)
        self.assertTrue(ok)

    def tearDown(self):
        self.ctx.close()
        self.ctx2.close()
        self.server.stop(0).wait()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestTimeline)
     return suite


if __name__ == '__main__':
    unittest.main()
