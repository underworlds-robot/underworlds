#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import underworlds
from underworlds.helpers.geometry import get_bounding_box_for_node
from underworlds.types import MESH

import math

import logging; logger = logging.getLogger("underworlds.spatial_reasoning")

EPSILON = 0.005 # 5mm

def bb_center(bb):

    x1,y1,z1 = bb[0]
    x2,y2,z2 = bb[1]

    return x1+x2/2, y1+y2/2, z1+z2/2

def bb_footprint(bb):
    """ Returns a rectangle that defines the bottom face of a bounding box
    """
    x1,y1,z1 = bb[0]
    x2,y2,z2 = bb[1]

    return (x1,y1), (x2,y2)

def bb_frontprint(bb):
    """ Returns a rectangle that defines the front face of a bounding box.
    """

    x1,y1,z1 = bb[0]
    x2,y2,z2 = bb[1]

    return (x1,z1), (x2,z2)

def bb_sideprint(bb):
    """ Returns a rectangle that defines the side face of a bounding box
    """
    x1,y1,z1 = bb[0]
    x2,y2,z2 = bb[1]

    return (y1,z1), (y2,z2)


def characteristic_dimension(bb):
    """ Returns the length of the bounding box diagonal
    """

    x1,y1,z1 = bb[0]
    x2,y2,z2 = bb[1]

    return math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))

def distance(bb1, bb2):
    """ Returns the distance between the bounding boxes centers.
    """
    x1,y1,z1 = bb_center(bb1)
    x2,y2,z2 = bb_center(bb2)

    return math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2)+(z1-z2)*(z1-z2))




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

def weakly_cont(rect1, rect2):
    '''Obj1 is weakly contained if the base of the object is surrounded
    by Obj2
    '''
    (l1,b1), (r1,t1) = rect1
    (l2,b2), (r2,t2) = rect2

    return (l1 >= l2) and (b1 >= b2) and (r1 <= r2) and (t1 <= t2)

def iswklycont(bb1, bb2):
    '''Takes two bounding boxes and then return the value of weakly_cont
    '''
    return weakly_cont(bb_footprint(bb1), bb_footprint(bb2))

def islower(bb1, bb2):
    """ Returns true if obj 1 is lower than obj2.

        For obj 1 to be lower than obj 2:
         - The the top of its bounding box must be lower than the bottom 
           of obj 2's bounding box
    """

    _, bb1_max = bb1
    bb2_min, _ = bb2

    x1,y1,z1 = bb1_max
    x2,y2,z2 = bb2_min

    return z1 < z2

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

    def isbelow(bb1, bb2):
        """ Returns true if ob1 is below obj 2.

        For obj 1 to be below obj 2:
         - obj 1 is lower than obj 2
         - the bounding box footbrint of both objects must overlap
    """

    if islower(bb1, bb2):
        return overlap(bb_footprint(bb1), bb_footprint(bb2))

    return False

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

def isclose(bb1, bb2):
    """ Returns True if the first object is close to the second.

    More precisely, returns True if the first bounding box is within a radius R
    (R = 2 X second bounding box dimension) of the second bounding box.

    Note that in general, isclose(bb1, bb2) != isclose(bb2, bb1)
    """


    dist = distance(bb1,bb2)
    dim2 = characteristic_dimension(bb2)

    return dist < 2 * dim2

def isnorth(bb1, bb2, north_vector=[0,1,0]):
    """ Returns True if bb1 is north of bb2

        For obj1 to be north of obj2 if we assume a north_vector of [0,1,0]
            - The min Y of bb1 is greater than the max Y of bb2
    """

    #Currently a North Vector of 0,1,0 (North is in the positive Y direction)
    #is assumed. At some point this should be updated to allow for non-traditional
    #North to be taken and to allow for directions based on perspective.
    if north_vector != [0,1,0]:
        raise NotImplementedError

    bb1_min, _ = bb1
    _, bb2_max = bb2

    x1,y1,z1 = bb1_min
    x2,y2,z2 = bb2_max

    return y1 > y2


def iseast(bb1, bb2, north_vector=[0,1,0]):
    """ Returns True if bb1 is east of bb2

        For obj1 to be east of obj2 if we assume a north_vector of [0,1,0]
            - The min X of bb1 is greater than the max X of bb2
    """

    #Currently a North Vector of 0,1,0 (North is in the positive Y direction)
    #is assumed. At some point this should be updated to allow for non-traditional
    #North to be taken and to allow for directions based on perspective.
    if north_vector != [0,1,0]:
        raise NotImplementedError

    bb1_min, _ = bb1
    _, bb2_max = bb2

    x1,y1,z1 = bb1_min
    x2,y2,z2 = bb2_max

    return x1 > x2

def issouth(bb1, bb2, north_vector=[0,1,0]):
    """ Returns True if bb1 is south of bb2

        For obj1 to be south of obj2 if we assume a north_vector of [0,1,0]
            - The max Y of bb1 is less than the min Y of bb2
    """

    #Currently a North Vector of 0,1,0 (North is in the positive Y direction)
    #is assumed. At some point this should be updated to allow for non-traditional
    #North to be taken and to allow for directions based on perspective.
    if north_vector != [0,1,0]:
        raise NotImplementedError

    _,bb1_max = bb1
    bb2_min,_ = bb2

    x1,y1,z1 = bb1_max
    x2,y2,z2 = bb2_min

    return y1 < y2

def iswest(bb1, bb2, north_vector=[0,1,0]):
    """ Returns True if bb1 is west of bb2

        For obj1 to be west of obj2 if we assume a north_vector of [0,1,0]
            - The max X of bb1 is less than the min X of bb2
    """

    #Currently a North Vector of 0,1,0 (North is in the positive Y direction)
    #is assumed. At some point this should be updated to allow for non-traditional
    #North to be taken and to allow for directions based on perspective.
    if north_vector != [0,1,0]:
        raise NotImplementedError

    _,bb1_max = bb1
    bb2_min,_ = bb2

    x1,y1,z1 = bb1_max
    x2,y2,z2 = bb2_min

    return x1 < x2

def istonorth(bb1, bb2, north_vector=[0,1,0]):
    """ Returns True if bb1 is to the north of bb2.

    For obj1 to be to north of obj2:
        - obj1 is close to obj2
        - The side faces for obj1 and obj2 overlap
        - obj1 is north obj2
    """

    #Currently a North Vector of 0,1,0 (North is in the positive Y direction)
    #is assumed. At some point this should be updated to allow for non-traditional
    #North to be taken and to allow for directions based on perspective.
    if north_vector != [0,1,0]:
        raise NotImplementedError

    if isclose(bb1, bb2):
        if overlap(bb_frontprint(bb1), bb_frontprint(bb2)):
            return isnorth(bb1, bb2, north_vector)
    return False

def istoeast(bb1, bb2, north_vector=[0,1,0]):
    """ Returns True if bb1 is to the east of bb2.

    For obj1 to be to east of obj2:
        - obj1 is close to obj2
        - The side faces for obj1 and obj2 overlap
        - obj1 is east obj2
    """

    #Currently a North Vector of 0,1,0 (North is in the positive Y direction)
    #is assumed. At some point this should be updated to allow for non-traditional
    #North to be taken and to allow for directions based on perspective.
    if north_vector != [0,1,0]:
        raise NotImplementedError

    if isclose(bb1, bb2):
        if overlap(bb_sideprint(bb1), bb_sideprint(bb2)):
            return iseast(bb1, bb2, north_vector)
    return False

def istosouth(bb1, bb2, north_vector=[0,1,0]):
    """ Returns True if bb1 is to the south of bb2.

    For obj1 to be to south of obj2:
        - obj1 is close to obj2
        - The side faces for obj1 and obj2 overlap
        - obj1 is south obj2
    """

    #Currently a North Vector of 0,1,0 (North is in the positive Y direction)
    #is assumed. At some point this should be updated to allow for non-traditional
    #North to be taken and to allow for directions based on perspective.
    if north_vector != [0,1,0]:
        raise NotImplementedError

    if isclose(bb1, bb2):
        if overlap(bb_frontprint(bb1), bb_frontprint(bb2)):
            return issouth(bb1, bb2, north_vector)
    return False

def istowest(bb1, bb2, north_vector=[0,1,0]):
    """ Returns True if bb1 is to the west of bb2.

    For obj1 to be to west of obj2:
        - obj1 is close to obj2
        - The side faces for obj1 and obj2 overlap
        - obj1 is west obj2
    """

    #Currently a North Vector of 0,1,0 (North is in the positive Y direction)
    #is assumed. At some point this should be updated to allow for non-traditional
    #North to be taken and to allow for directions based on perspective.
    if north_vector != [0,1,0]:
        raise NotImplementedError

    if isclose(bb1, bb2):
        if overlap(bb_sideprint(bb1), bb_sideprint(bb2)):
            return iswest(bb1, bb2, north_vector)
    return False

def isin(bb1, bb2):
    """ Returns True if bb1 is in bb2. 

    To be 'in' bb1 is weakly contained by bb2 and the bottom of bb1 is lower 
    than the top of bb2 and higher than the bottom of bb2.
    """
    bb1_min, _ = bb1
    bb2_min, bb2_max = bb2

    x1,y1,z1 = bb1_min
    x2,y2,z2 = bb2_max
    x3,y3,z3 = bb2_min

    if z1 > z2 + EPSILON:
        return False

    if z1 < z3 - EPSILON:
        return False

    return weakly_cont(bb_footprint(bb1),
            bb_footprint(bb2))

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

            if isclose(bb, bb2):
                logger.info("%s is close of %s" % (n, n2))

            if isin(bb, bb2):
                logger.info("%s is in %s" % (n, n2))

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


