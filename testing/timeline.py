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
        time.sleep(0.1) # leave some time to the server to start

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

        self.assertEquals(t1, t2)
        self.assertTrue(self.t0 < t1 < self.t3)

    def test_events_base(self):

        s = Situation()

        self.timeline.start(s)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertIn(s, self.timeline.situations)
        self.assertIn(s, self.timeline.activesituations)

        self.timeline.end(s)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertIn(s, self.timeline.situations)
        self.assertNotIn(s, self.timeline.activesituations)

        s = createevent()

        self.timeline.start(s)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertIn(s, self.timeline.situations)
        self.assertNotIn(s, self.timeline.activesituations)

        self.timeline.end(s)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertIn(s, self.timeline.situations)
        self.assertNotIn(s, self.timeline.activesituations)


    def _test_events_callback(self):
        event = Event()

        ok = False
        def onevt(self, evt):
            ok = True

        self.timeline.on(event).call(onevt)

        self.timeline.event(event)
        time.sleep(PROPAGATION_TIME)
        self.assertTrue(ok)

    def _test_events_start_stop(self):
        t = self.timeline

        s = Situation()
        t.start(s)

        self.assertEquals(len(t.activesituations), 1)
        self.assertIn(s, t.activesituations)

        t.end(s)

        self.assertEquals(len(t.activesituations), 0)

        # can not call .event() with a situation
        with self.assertRaises(TypeError):
            t.event(s)

        e = Event()

        t.end(e) # should do nothing at all

        t.start(e) # events end immediately
       
        self.assertEquals(len(t.activesituations), 0)

        t.event(e) # for events, should be synonym with 't.start'
       
        self.assertEquals(len(t.activesituations), 0)

    def _test_modelloading(self):

        event = Event(Event.MODELLOAD)

        with self.assertRaises(TimeoutError):
            self.timeline.on(event).wait(timeout = 0.1)

        ModelLoader(self.world).load("res/base.dae")

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
        self.server.stop(0)

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestTimeline)
     return suite


if __name__ == '__main__':
    unittest.main()
