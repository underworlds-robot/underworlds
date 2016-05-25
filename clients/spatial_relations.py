#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import underworlds
from underworlds.helpers.geometry import get_bounding_box_for_node
from underworlds.types import MESH

import logging; logger = logging.getLogger("underworlds.spatial_reasoning")

EPSILON = 0.005 # 5mm

def bb_center(bb):

    x1,y1,z1 = bb[0]
    x2,y2,z2 = bb[1]

    return x1+x2/2, y1+y2/2, z1+z2/2

def bb_footprint(bb):

    x1,y1,z1 = bb[0]
    x2,y2,z2 = bb[1]

    return (x1,y1), (x2,y2)

def overlap(rect1, rect2):
    '''Overlapping rectangles overlap both horizontally & vertically
    '''
    (l1,b1), (r1,t1) = rect1
    (l2,b2), (r2,t2) = rect2
    return range_overlap(l1, r1, l2, r2) and \
           range_overlap(b1, t1, b2, t2)

def range_overlap(a_min, a_max, b_min, b_max):
    '''Neither range is completely greater than the other

    http://codereview.stackexchange.com/questions/31352/overlapping-rectangles
    '''
    return (a_min <= b_max) and (b_min <= a_max)

def isabove(bb1, bb2):
    """ For obj 1 to be above obj 2:
         - the bottom of its bounding box must be higher that
           the top of obj 2's bounding box
         - the bounding box footprint of both objects must overlap
    """

    bb1_min, _ = bb1
    _, bb2_max = bb2

    x1,y1,z1 = bb1_min
    x2,y2,z2 = bb2_max

    if z1 < z2 - EPSILON:
        return False

    return overlap(bb_footprint(bb1),
                   bb_footprint(bb2))

def isontop(bb1, bb2):
    """ For obj 1 to be on top of obj 2:
         - obj1 must be above obj 2
         - the bottom of obj 1 must be close to the top of obj 2
    """


    bb1_min, _ = bb1
    _, bb2_max = bb2

    x1,y1,z1 = bb1_min
    x2,y2,z2 = bb2_max

    return z1 < z2 + EPSILON and isabove(bb1, bb2)

def compute_relations(scene):

    boundingboxes = {n: get_bounding_box_for_node(scene, n) for n in scene.nodes if n.type == MESH}
    allocentric_relations(boundingboxes)

def allocentric_relations(nodes):

    for n,bb in nodes.items():
        for n2,bb2 in nodes.items():
            if n == n2:
                continue

            if isabove(bb, bb2):
                logger.info("%s is above %s" % (n, n2))
                if isontop(bb, bb2):
                    logger.info("%s is on top of %s" % (n, n2))


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("world", help="Underworlds world to monitor")
    #parser.add_argument("-d", "--debug", help="run in interactive, debug mode", action="store_true")
    args = parser.parse_args()

    with underworlds.Context("Geometry Reasonning") as ctx:

        world = ctx.worlds[args.world]

        compute_relations(world.scene)

        try:
            while True:
                world.scene.waitforchanges()
                logger.info("Updating relations...")
                compute_relations(world.scene)

        except KeyboardInterrupt:
            print("Bye bye")


