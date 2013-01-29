import time
import unittest

import logging; logger = logging.getLogger("underworlds.testing." + __name__)
logging.basicConfig(level=logging.DEBUG)

import underworlds
from underworlds.errors import *
from underworlds.server import Server
from underworlds.tools.loader import ModelLoader
from underworlds.types import Event


PROPAGATION_TIME=0.001 # time to wait for node update notification propagation (in sec)

class TestTimeline(unittest.TestCase):

    def setUp(self):
        self.server = Server()
        self.server.start()
        time.sleep(0.1) # leave some time to the server to start

        self.ctx = underworlds.Context("unittest - " + __name__)

        self.world = self.ctx.worlds["test"]
        self.timeline = self.world.timeline

    def test_base(self):

        self.assertIsNotNone(self.timeline)

        event = Event(Event.GENERIC)

        ok = False
        def onevt(self, evt):
            ok = True

        self.timeline.on(event).call(onevt)

        self.timeline.event(event)
        time.sleep(PROPAGATION_TIME)
        self.assertTrue(ok)

    def test_events_start_stop(self):
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

    def test_modelloading(self):

        event = Event(Event.MODELLOAD)

        with self.assertRaises(TimeoutError)
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
        self.server.stop()
        self.server.join()

def test_suite():
     suite = unittest.TestLoader().loadTestsFromTestCase(TestTimeline)
     return suite


if __name__ == '__main__':
    unittest.main()
