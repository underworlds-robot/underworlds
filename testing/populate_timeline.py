#! /usr/bin/env python

import time

import underworlds
from underworlds.types import Situation, createevent

with underworlds.Context("provider") as ctx:
    world = ctx.worlds["base"]

    timeline = world.timeline

    s1 = Situation()
    s2 = Situation()

    timeline.start(s1)
    time.sleep(0.2)
    timeline.start(s2)
    timeline.start(createevent())
    time.sleep(0.2)
    timeline.end(s2)
    time.sleep(0.5)
    timeline.end(s1)
