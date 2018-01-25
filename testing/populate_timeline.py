#! /usr/bin/env python

import sys
import time

import underworlds
from underworlds.types import Situation

if len(sys.argv) != 2:
    print("Usage: %s <world>" % __file__)
    sys.exit(1)

with underworlds.Context("provider") as ctx:
    world = ctx.worlds[sys.argv[1]]

    timeline = world.timeline

    s1 = timeline.start()
    time.sleep(0.2)
    s2 = timeline.start()
    s3 = timeline.event()
    time.sleep(0.2)
    timeline.end(s2)
    time.sleep(0.5)
    timeline.end(s1)
