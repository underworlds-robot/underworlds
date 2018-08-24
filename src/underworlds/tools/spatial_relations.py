#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import underworlds
import underworlds.server
from underworlds.helpers.geometry import get_bounding_box_for_node
from underworlds.helpers.geometry import compute_transformed_bounding_box
from underworlds.helpers.geometry import get_world_transform
from underworlds.helpers.transformations import compose_matrix
from underworlds.helpers.transformations import decompose_matrix
from underworlds.helpers.transformations import quaternion_from_matrix
from underworlds.types import MESH

import math
import numpy
from numpy import linalg

import logging; logger = logging.getLogger("underworlds.spatial_reasoning")

EPSILON = 0.005 # 5mm
ROTATION_180_X = numpy.array([[1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,1]], dtype=numpy.float32)

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
    
def istoback(ctx, scene, node1, node2, view_matrix):
    """ Returns True if node1 is to the back of node2 based on a view matrix
    
    For node1 to be to the back of node2:
        - the view transformed bounding box of node 1 is to north of the
          the view transformed bounding box of node 2. 
    """
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb1 = compute_transformed_bounding_box(ctx, scene, node1, view_matrix, bb_min, bb_max)
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb2 = compute_transformed_bounding_box(ctx, scene, node2, view_matrix, bb_min, bb_max)
    
    return istonorth(trans_bb1, trans_bb2)
    
def isfacing(ctx, scene, node1, node2):
    """ Returns True if node2 is facing node1 based on a view matrix
        calculated from the 'face' of node 2.
    
    For node2 to be facing node1:
        - node2 to must be considered to have a front face.
        - the view transformed bounding box of node 1 is to north of the
          the view transformed bounding box of node 2. 
    """
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    if "facing" not in node2.properties:
        return False
        
    n2_pos = get_world_transform(scene, node2)
    face_pos = numpy.dot(node2.properties["facing"], n2_pos)
    
    view_matrix = get_spatial_view_matrix(face_pos, False)
    
    trans_bb2 = compute_transformed_bounding_box(ctx, scene, node2, view_matrix, bb_min, bb_max)
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb1 = compute_transformed_bounding_box(ctx, scene, node1, view_matrix, bb_min, bb_max)
    
    return istonorth(trans_bb1, trans_bb2)

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
    
def istoright(ctx, scene, node1, node2, view_matrix):
    """ Returns True if node1 is to the right of node2 based on a view matrix
    
    For node1 to be to the right of node2:
        - the view transformed bounding box of node 1 is to east of the
          the view transformed bounding box of node 2. 
    """
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb1 = compute_transformed_bounding_box(ctx, scene, node1, view_matrix, bb_min, bb_max)
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb2 = compute_transformed_bounding_box(ctx, scene, node2, view_matrix, bb_min, bb_max)
    
    return istoeast(trans_bb1, trans_bb2)
    
def isstarboard(ctx, scene, node1, node2):
    """ Returns True if node1 is on the right of node2 based on a view matrix
        calculated from the 'face' of node 2.
    
    For node1 to be on the right of node2:
        - node2 to must be considered to have a front face.
        - the view transformed bounding box of node 1 is to east of the
          the view transformed bounding box of node 2. 
    """
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    if "facing" not in node2.properties:
        return False
        
    n2_pos = get_world_transform(scene, node2)
    face_pos = numpy.dot(node2.properties["facing"], n2_pos)
    
    view_matrix = get_spatial_view_matrix(face_pos, False)
    
    trans_bb2 = compute_transformed_bounding_box(ctx, scene, node2, view_matrix, bb_min, bb_max)
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb1 = compute_transformed_bounding_box(ctx, scene, node1, view_matrix, bb_min, bb_max)
    
    return istoeast(trans_bb1, trans_bb2)
    

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

def istofront(ctx, scene, node1, node2, view_matrix):
    """ Returns True if node 1 is to the front of node 2 based on a view matrix
    
    For node1 to be to the front of node2:
        - the view transformed bounding box of node 1 is to south of the
          the view transformed bounding box of node 2. 
    """
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb1 = compute_transformed_bounding_box(ctx, scene, node1, view_matrix, bb_min, bb_max)
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb2 = compute_transformed_bounding_box(ctx, scene, node2, view_matrix, bb_min, bb_max)
    
    return istosouth(trans_bb1, trans_bb2)
    
def isbehind(ctx, scene, node1, node2):
    """ Returns True if node 1 is behind node 2 based on a view matrix
        calculated from the 'face' of node 2.
    
    For node1 to be behind node2:
        - node2 to must be considered to have a front face.
        - the view transformed bounding box of node 1 is to north of the
          the view transformed bounding box of node 2. 
    """
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    if "facing" not in node2.properties:
        return False
        
    n2_pos = get_world_transform(scene, node2)
    face_pos = numpy.dot(node2.properties["facing"], n2_pos)
    
    view_matrix = get_spatial_view_matrix(face_pos, False)
    
    trans_bb2 = compute_transformed_bounding_box(ctx, scene, node2, view_matrix, bb_min, bb_max)
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb1 = compute_transformed_bounding_box(ctx, scene, node1, view_matrix, bb_min, bb_max)
    
    return istosouth(trans_bb1, trans_bb2)

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
    
def istoleft(ctx, scene, node1, node2, view_matrix):
    """ Returns True if node 1 is to the left of node 2 based on a view matrix
    
    For node1 to be to the left of node2:
        - the view transformed bounding box of node 1 is to west of the
          the view transformed bounding box of node 2. 
    """
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb1 = compute_transformed_bounding_box(ctx, scene, node1, view_matrix, bb_min, bb_max)
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb2 = compute_transformed_bounding_box(ctx, scene, node2, view_matrix, bb_min, bb_max)
    
    return istowest(trans_bb1, trans_bb2)
    
def isport(ctx, scene, node1, node2):
    """ Returns True if node1 is on the left of node2 based on a view matrix
        calculated from the 'face' of node 2.
    
    For node1 to be on the left of node2:
        - node2 to must be considered to have a front face.
        - the view transformed bounding box of node 1 is to west of the
          the view transformed bounding box of node 2. 
    """
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    if "facing" not in node2.properties:
        return False
        
    n2_pos = get_world_transform(scene, node2)
    face_pos = numpy.dot(node2.properties["facing"], n2_pos)
    
    view_matrix = get_spatial_view_matrix(face_pos, False)
    
    trans_bb2 = compute_transformed_bounding_box(ctx, scene, node2, view_matrix, bb_min, bb_max)
    
    bb_min=[1e10, 1e10, 1e10] 
    bb_max=[-1e10, -1e10, -1e10]
    
    trans_bb1 = compute_transformed_bounding_box(ctx, scene, node1, view_matrix, bb_min, bb_max)
    
    return istowest(trans_bb1, trans_bb2)

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
    
    if z1 >= z2:
        return False

    if z1 < z3 - EPSILON:
        return False

    return weakly_cont(bb_footprint(bb1),
                   bb_footprint(bb2))
                   
def get_spatial_view_matrix(trans_matrix=numpy.identity(4, dtype = numpy.float32), gravity_bias=True):
    
    if gravity_bias == True:
        #Remove pitch,roll and z translation. (This assumes that gravity is in the negative z direction)
        #WARNING - Currently using euler angles which causes issues if the rotation angles go out of bounds. See note on angle ranges http://nghiaho.com/?page_id=846
        scale, shear, angles, translate, perspective = decompose_matrix(trans_matrix)
        trans_matrix = compose_matrix(scale, shear, (0,0,angles[2]), (translate[0],translate[1],0), perspective)
        #trans_matrix = compose_matrix((1,1,1), (0,0,0), (0,0,angles[2]), (translate[0],translate[1],0), perspective)
        
    view_matrix = linalg.inv(trans_matrix)
    
    return view_matrix

def get_node_sr(worldName, nodeID, camera=None, gravity_bias=True, exclNodeID=None):

    rel_list = []
    
    with underworlds.Context("spatial_relations") as ctx:
        
        world = ctx.worlds[worldName]
        
        vm = None
        
        if camera is not None:
            if camera == "default":
                vm = get_spatial_view_matrix()
            else:
                vm = get_spatial_view_matrix(get_world_transform(scene, camera), gravity_bias)
            
            #vm = get_spatial_view_matrix(worldName, camera)

        node = world.scene.nodes[nodeID]

        bb1 = get_bounding_box_for_node(world.scene, world.scene.nodes[nodeID])
        
        if vm is not None:
            bb_min=[1e10, 1e10, 1e10] 
            bb_max=[-1e10, -1e10, -1e10]
            bb1_trans = compute_transformed_bounding_box(ctx, world.scene, node, vm, bb_min, bb_max)
        
        for node2 in world.scene.nodes:
            if node2.id == node.id or node2.id == exclNodeID or node2.id == world.scene.rootnode.id or node2.name[0] == "_":
                continue
                
            bb2 = get_bounding_box_for_node(world.scene, node2)
            
            if isin(bb1, bb2):
                logger.info("%s in %s" % (node.name, node2.name))
                rel_list.append([1, node.id, node2.id, "in"])
                continue
                   
            elif isontop(bb1, bb2):
                logger.info("%s onTop %s" % (node.name, node2.name))
                rel_list.append([2, node.id, node2.id, "onTop"])
                continue
                   
            elif isabove(bb1, bb2):
                logger.info("%s above %s" % (node.name, node2.name))
                rel_list.append([3, node.id, node2.id, "above"])
                continue
             
            elif isbelow(bb1, bb2):
                logger.info("%s below %s" % (node.name, node2.name))
                rel_list.append([4, node.id, node2.id, "below"])
                continue
                
            elif isclose(bb1, bb2):
                if vm is None:
                    if istonorth(bb1, bb2):
                        logger.info("%s to north %s" % (node.name, node2.name))
                        rel_list.append([5, node.id, node2.id, "toNorth"])
                    elif istoeast(bb1, bb2):
                        logger.info("%s to east %s" % (node.name, node2.name))
                        rel_list.append([6, node.id, node2.id, "toEast"])
                    elif istosouth(bb1, bb2):
                        logger.info("%s to south %s" % (node.name, node2.name))
                        rel_list.append([7, node.id, node2.id, "toSouth"])
                    elif istowest(bb1, bb2):
                        logger.info("%s to west %s" % (node.name, node2.name))
                        rel_list.append([8, node.id, node2.id, "toWest"])
                    else:
                        logger.info("%s close %s" % (node.name, node2.name))
                        rel_list.append([9, node.id, node2.id, "close"])
                else:
                    bb_min=[1e10, 1e10, 1e10] 
                    bb_max=[-1e10, -1e10, -1e10]
                    bb2_trans = compute_transformed_bounding_box(ctx, world.scene, node2, vm, bb_min, bb_max)
                    #Do these calculations only once for efficiency, and use the same logic to then calculate from the view matrix
                    
                    if istonorth(bb1_trans, bb2_trans):
                        logger.info("%s to back %s" % (node.name, node2.name))
                        rel_list.append([5, node.id, node2.id, "toBack"])
                    elif istoeast(bb1_trans, bb2_trans):
                        logger.info("%s to right %s" % (node.name, node2.name))
                        rel_list.append([6, node.id, node2.id, "toRight"])
                    elif istosouth(bb1_trans, bb2_trans):
                        logger.info("%s to front %s" % (node.name, node2.name))
                        rel_list.append([7, node.id, node2.id, "toFront"])
                    elif istowest(bb1_trans, bb2_trans):
                        logger.info("%s to left %s" % (node.name, node2.name))
                        rel_list.append([8, node.id, node2.id, "toLeft"])
                    else:
                        logger.info("%s close %s" % (node.name, node2.name))
                        rel_list.append([9, node.id, node2.id, "close"])
    
                continue
                       
        return rel_list
        
def check_for_exclusions(worldname, rel_list, iteration, view_matrix=numpy.identity(4, dtype = numpy.float32)):

    i = 0
    relation = rel_list[iteration][3]
    
    if iteration > 0:
        if relation == rel_list[iteration - 1][3]:
            #These relations should have already been checked in a previous iteration.
            return rel_list
    
    rel_poss_excl = []
    
    #Get a list of all the nodes that have the same relation to our current node
    while  (iteration + i) < len(rel_list) and rel_list[iteration + i][3] == relation:
        rel_poss_excl.append([rel_list[iteration + i][2], i])
        i += 1
    
    length = len(rel_poss_excl)
        
    if length > 1:
        i = 0
        rel_excl = []
        with underworlds.Context("spatial_description") as ctx:
            
            world = ctx.worlds[worldname]
            
            while(i < length):
            
                j = 0
                
                node1 = world.scene.nodes[rel_poss_excl[i][0]]
                bb1 = get_bounding_box_for_node(world.scene, node1)
                
                while (j < length):
                    
                    if i == j or j in rel_excl:
                        j += 1
                        continue
                        
                    node2 = world.scene.nodes[rel_poss_excl[j][0]]
                    bb2 = get_bounding_box_for_node(world.scene, node2)
                    
                    if relation == "in":
                        if isin(bb1, bb2):
                            rel_excl.append(j) #Append to list to be deleted afterward
                            
                    elif relation == "onTop":
                        pass
                        
                    elif relation == "above":
                        if isin(bb2, bb1) or isabove(bb2, bb1):
                            rel_excl.append(j)
                        
                    elif relation == "below":
                        if isin(bb2, bb1) or isbelow(bb2, bb1) or isontop(bb2, bb1):
                            rel_excl.append(j)
                        
                    elif relation == "close":
                        pass
                        
                    elif relation == "toBack":
                        if isin(bb2, bb1) or istoback(ctx, world.scene, node2, node1, view_matrix):
                            rel_excl.append(j)
                    
                    elif relation == "toRight":
                        if isin(bb2, bb1) or istoright(ctx, world.scene, node2, node1, view_matrix):
                            rel_excl.append(j)
                            
                    elif relation == "toFront":
                        if isin(bb2, bb1) or istofront(ctx, world.scene, node2, node1, view_matrix):
                            rel_excl.append(j)
                            
                    elif relation == "toLeft":
                        if isin(bb2, bb1) or istoleft(ctx, world.scene, node2, node1, view_matrix):
                            rel_excl.append(j)
                        
                    elif relation == "toNorth":
                        if isin(bb2, bb1) or istonorth(bb2, bb1):
                            rel_excl.append(j)
                        
                    elif relation == "toEast":
                        if isin(bb2, bb1) or istoeast(bb2, bb1):
                            rel_excl.append(j)
                        
                    elif relation == "toSouth":
                        if isin(bb2, bb1) or istoeast(bb2, bb1):
                            rel_excl.append(j)
                        
                    elif relation == "toWest":
                        if isin(bb2, bb1) or istowest(bb2, bb1):
                            rel_excl.append(j)
                            
                    else:
                        raise NotImplementedError
                        
                    j += 1
                i += 1
            
        for j in reversed(sorted(rel_excl)):
            del rel_list[iteration + j]
            
    return rel_list

def compute_all_relations(worldName, perspective=[0,1,0]):
    
    all_rel_list = []
    
    with underworlds.Context("spatial_relations") as ctx:
        world = ctx.worlds[worldName]
    
        for node in world.scene.nodes:
            cur_rel_list = get_node_sr(worldName, node.id)
            all_rel_list.append({node.id, cur_rel_list})
            
        return all_rel_list

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("world", help="Underworlds world to monitor")
    #parser.add_argument("-d", "--debug", help="run in interactive, debug mode", action="store_true")
    args = parser.parse_args()

    with underworlds.Context("Spatial Reasonning") as ctx:

        world = ctx.worlds[args.world]

        compute_all_relations(args.world)

        try:
            while True:
                world.scene.waitforchanges()
                logger.info("Updating relations...")
                compute_all_relations(args.world)

        except KeyboardInterrupt:
            print("Bye bye")


