#! /usr/bin/env python

import time
import unittest

import threading
from concurrent.futures import ThreadPoolExecutor

import logging; logger = logging.getLogger("underworlds.testing.performances")
logging.basicConfig(level=logging.WARN)

import underworlds
import underworlds.server
from underworlds.types import Node
import underworlds.underworlds_pb2 as gRPC

running = True

def ms(duration):
    return "%.1fms" % (duration * 1000)

def passthrough(world1, world2):
    """ Simple passthrough filter: wait for changes on a world world1 and
    propagate these changes to world world2.
    """

    with underworlds.Context("user%d" % threading.current_thread().ident) as ctx:

        world1 = ctx.worlds[world1]
        world2 = ctx.worlds[world2]

        while running:
            id, op = world1.scene.waitforchanges(0.5)
            world2.scene.update_and_propagate(world1.scene.nodes[id])
        print("Stopping passthrough")


def wait_for_changes(world):

    print("Waiting for changes in world %s" % world)

    starttime = time.time()

    change = world.scene.waitforchanges(5)
    return change, time.time()-starttime



    
def test_propagation_time(nb_worlds):

    executor = ThreadPoolExecutor(max_workers=nb_worlds)

    for i in range(nb_worlds-1):
        print("Setting up passthrough between world %d and world %d" % (i, i+1))
        f = executor.submit(passthrough, "world%d" % i, "world%d" % (i+1))

    ctx = underworlds.Context("test_client")
    entry_world = ctx.worlds["world0"]
    exit_world = ctx.worlds["world%d" % (nb_worlds-1)]


    future = executor.submit(wait_for_changes, exit_world)
    time.sleep(0.1)

    n = Node()
    n.name = "test"

    print("Propagating a change from world %s..." % entry_world)
    entry_world.scene.append_and_propagate(n)

    change, duration = future.result()
    duration -= 0.1
    print("It took %s to be notified of the change in world %s" % (ms(duration), exit_world))

    if change is None:
        raise RuntimeError("The change has not been seen!")


    running = False
    executor.shutdown(wait=True)
    ctx.close()

    return duration

if __name__ == '__main__':
    durations = []

    for nb in range(2,12):
        print("\n\n\n-- %d worlds --\n" % nb)

        server = underworlds.server.start()
        time.sleep(0.2) # leave some time to the server to start

        durations.append(test_propagation_time(nb))
        server.stop(0)

        for d in durations:
            print("%.1f" % (d * 1000))


