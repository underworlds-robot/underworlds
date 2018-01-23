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

    def test_siutation_manipulations(self):

        s1 = Situation()
        s2 = Situation()

        self.assertEqual(len(self.timeline),0)

        self.timeline.append(s1)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(self.timeline),1)
        self.assertIn(s1, self.timeline)
        self.assertEqual(self.timeline[0].endtime, 0)
 
        s1.endtime = 1
        self.timeline.update(s1)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(self.timeline),1)
        self.assertEqual(self.timeline[0].endtime, 1)

        self.timeline.update(s2) # alias for append
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(self.timeline),2)
        self.assertIn(s2, self.timeline)
 
        self.timeline.update(s2) # shouldn't do anything, as s2 is already present
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(self.timeline),2)
 
        s1.endtime = 2
        s2.endtime = 3
        self.timeline.update(s1)
        self.timeline.update(s2)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(self.timeline),2)
        self.assertEqual(self.timeline[s1.id].endtime, 2)
        self.assertEqual(self.timeline[s2.id].endtime, 3)

 
        self.timeline.remove(s1)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(self.timeline),1)
        self.assertEqual(self.timeline[0].id, s2.id)
 
        self.timeline.remove(s2)
        time.sleep(PROPAGATION_TIME) # wait for propagation

        self.assertEqual(len(self.timeline),0)

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
