#! /usr/bin/env python

import time

import logging; logger = logging.getLogger("underworlds.testing")
logging.basicConfig(level=logging.DEBUG)

import underworlds
from underworlds.types import Node

PROPAGATION_TIME=0.001 # time to wait for node update notification propagation (in sec)


# Add a PROVIDER client
with underworlds.Context("provider") as provider_ctx:
    world = provider_ctx.worlds["base"]
    world.scene.nodes.update(Node()) # create and add a random node

# Add a READER client
with underworlds.Context("reader") as reader_ctx:
    world = reader_ctx.worlds["base"]
    world2 = reader_ctx.worlds["brave new world"]
    for n in world.scene.nodes:
        world2.scene.nodes.update(n)

