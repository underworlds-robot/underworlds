#! /usr/bin/env python

import argparse
import time

import yappi

import threading
from concurrent.futures import ThreadPoolExecutor

import logging; logger = logging.getLogger("underworlds.testing.performances")

import underworlds
import underworlds.server
from underworlds.types import Node
import underworlds.underworlds_pb2 as gRPC

OUT_FILE = '/tmp/underworlds.profile'

running = True
starttime = None

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
            print("+%.1f -- Propagating from %s to %s" % ((time.time() - starttime)*1000, world1, world2))
            world2.scene.update_and_propagate(world1.scene.nodes[id])
        print("Stopping passthrough")


def wait_for_changes(world):

    print("Waiting for changes in world %s" % world)

    starttime = time.time()

    change = world.scene.waitforchanges(5)
    return change, time.time()-starttime



    
def test_propagation_time(nb_worlds):
    global starttime

    executor = ThreadPoolExecutor(max_workers=nb_worlds)

    for i in range(nb_worlds-1):
        print("Setting up passthrough between world %d and world %d" % (i, i+1))
        f = executor.submit(passthrough, "world%d" % i, "world%d" % (i+1))

    ctx = underworlds.Context("test_client")
    entry_world = ctx.worlds["world0"]
    exit_world = ctx.worlds["world%d" % (nb_worlds-1)]


    #yappi.start()
    future = executor.submit(wait_for_changes, exit_world)

    n = Node()
    n.name = "test"

    print("Propagating a change from world %s..." % entry_world)

    starttime=time.time()

    entry_world.scene.append_and_propagate(n)

    change, duration = future.result()
    #yappi.stop()
    #finish_yappi()

    print("It took %s to be notified of the change in world %s" % (ms(duration), exit_world))

    if change is None:
        raise RuntimeError("The change has not been seen!")


    running = False
    executor.shutdown(wait=True)
    ctx.close()

    return duration

def finish_yappi():
    print('[YAPPI STOP]')

    print('[YAPPI WRITE]')

    stats = yappi.get_func_stats()

    for stat_type in ['pstat', 'callgrind', 'ystat']:
      print('writing {}.{}'.format(OUT_FILE, stat_type))
      stats.save('{}.{}'.format(OUT_FILE, stat_type), type=stat_type)

    print('\n[YAPPI FUNC_STATS]')

    print('writing {}.func_stats'.format(OUT_FILE))
    with open('{}.func_stats'.format(OUT_FILE), 'wb') as fh:
      stats.print_all(out=fh)

    print('\n[YAPPI THREAD_STATS]')

    print('writing {}.thread_stats'.format(OUT_FILE))
    tstats = yappi.get_thread_stats()
    with open('{}.thread_stats'.format(OUT_FILE), 'wb') as fh:
      tstats.print_all(out=fh)

    print('[YAPPI OUT]')

if __name__ == '__main__':
    durations = []

    parser = argparse.ArgumentParser()
    parser.add_argument("maxworlds", default=5, type=int, nargs="?", help="Maximum number of Underworlds worlds to spawn")
    parser.add_argument("-d", "--debug", help="debug mode", action="store_true")
    parser.add_argument("-dd", "--fulldebug", help="debug mode (verbose)", action="store_true")
    parser.add_argument("-i", "--incremental", action="store_true", help="test for every nb of worlds, from 2 to maxworlds")
    args = parser.parse_args()

    if args.debug or args.fulldebug:
        if args.fulldebug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
    else:
        logger.setLevel(logging.WARN)

    minworlds = 2 if args.incremental else args.maxworlds

    for nb in range(minworlds, args.maxworlds+1):
        print("\n\n\n-- %d worlds --\n" % nb)

        server = underworlds.server.start()
        time.sleep(0.2) # leave some time to the server to start

        durations.append(test_propagation_time(nb))
        server.stop(0)

        for d in durations:
            print("%.1f" % (d * 1000))


