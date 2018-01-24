#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
import uuid

from multiprocessing import Pipe, Pool
import threading
from concurrent.futures import ThreadPoolExecutor

import logging; logger = logging.getLogger("underworlds.testing.performances")

import underworlds
import underworlds.server
from underworlds.types import Node
from underworlds.helpers.profile import profileonce
import underworlds.underworlds_pb2 as gRPC

def ms(duration):
    return "%.1fms" % (duration * 1000)


def passthrough(world1, world2, signaling_pipe):
    """ Simple passthrough filter: wait for changes on a world world1 and
    propagate these changes to world world2.
    """

    name = "passthrough_filter_%s_to_%s" % (world1, world2)
    with underworlds.Context(name) as ctx:

        world1 = ctx.worlds[world1]
        world2 = ctx.worlds[world2]

        try:
            print("Waiting for changes...")
            while not signaling_pipe.poll():
                #print("%f -- %s waiting" % (time.time(), name))
                change = world1.scene.waitforchanges(0.5)
                #print("%f -- %s Done waiting (last change: %s)" % (time.time(), name, str(change)))
                if change is not None:
                    id, op = change
                    #print("%f -- propagating from %s to %s" % (time.time(), name, world1, world2))
                    world2.scene.update_and_propagate(world1.scene.nodes[id])
                    change = None
        except Exception as e:
            import traceback
            traceback.print_exc()
        print("Stopping passthrough")
    print("Passthrough stopped")


def wait_for_changes(world, nb_changes):

    print("Waiting for changes in world %s" % world)

    starttime = time.time()

    change = None

    for i in range(nb_changes):
        change = world.scene.waitforchanges(3)

    profileonce("waitforchanges triggered")

    return change, time.time()-starttime



    
def test_propagation_time(nb_worlds, nb_changes):

    executor = ThreadPoolExecutor(max_workers=nb_worlds)
    pool = Pool(nb_worlds)

    pipes = []
    res = []
    for i in range(nb_worlds-1):
        print("Setting up passthrough between world %d and world %d" % (i, i+1))
        #f = executor.submit(passthrough, "world%d" % i, "world%d" % (i+1))
        conn1, conn2 = Pipe()
        pipes.append(conn1)
        res.append(pool.apply_async(passthrough, ["world%d" % i, "world%d" % (i+1), conn2]))

    time.sleep(0.5)

    ctx = underworlds.Context("test_client")
    entry_world = ctx.worlds["world0"]
    exit_world = ctx.worlds["world%d" % (nb_worlds-1)]

    future = executor.submit(wait_for_changes, exit_world, nb_changes)

    print("\n\n\nPropagating %d change(s) from world %s..." % (nb_changes, entry_world))
    profileonce("start test with %d worlds" % nb_worlds)


    for i in range(nb_changes):
        n = Node()
        n.name = "node_%d" % i
        entry_world.scene.append_and_propagate(n)
        time.sleep(0.01)

    seen, duration = future.result()

    profileonce("end test")


    if seen is None:
        logger.error("The changes have not been seen!")
        duration = 0
    else:
        print("It took %s to be notified of the %d change(s) in world %s" % (ms(duration), nb_changes, exit_world))

    executor.shutdown(wait=True)

    for p in pipes:
        p.send(True)
    pool.close()
    pool.join()
    ctx.close()

    return duration

if __name__ == '__main__':
    durations = {}

    parser = argparse.ArgumentParser()
    parser.add_argument("maxworlds", default=5, type=int, nargs="?", help="Maximum number of Underworlds worlds to spawn")
    parser.add_argument("-d", "--debug", help="debug mode", action="store_true")
    parser.add_argument("-dd", "--fulldebug", help="debug mode (verbose)", action="store_true")
    parser.add_argument("-i", "--incremental", action="store_true", help="test for every nb of worlds, from 2 to maxworlds")
    parser.add_argument("-r", "--repeat", default=1, type=int, nargs="?", help="how many times the test should be repeated (default: no repeat)")
    parser.add_argument("-c", "--changes", default=1, type=int, nargs="?", help="how many changes should be propagated (default: one)")
    args = parser.parse_args()

    if args.debug or args.fulldebug:
        if args.fulldebug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
    else:
        logger.setLevel(logging.WARN)

    minworlds = 2 if args.incremental else args.maxworlds

    for idx in range(0, args.repeat):
        print("\n\n\n-- Iteration #%d --\n" % idx)

        for nb in range(minworlds, args.maxworlds+1):
            print("\n\n\n-- %d worlds --\n" % nb)

            server = underworlds.server.start()
            durations.setdefault(nb,[]).append(test_propagation_time(nb, args.changes))
            server.stop(0).wait()


        time.sleep(0.5)

        for nb,times in durations.items():
            print("%d;%s" % (nb, ";".join([str("%.1f" % (d * 1000)) for d in times])))


