import numpy
from numpy import linalg

import logging; logger = logging.getLogger("underworlds.helpers.geometry")

from ..types import MESH
from functools import reduce

def transform(vector3, matrix4x4):
    """ Apply a transformation matrix on a 3D vector.

    :param vector3: a numpy array with 3 elements
    :param matrix4x4: a numpy 4x4 matrix
    """
    return numpy.dot(matrix4x4, numpy.append(vector3, 1.))

def get_scene_bounding_box(scene):
    """
    Returns the axis-aligned bounding box (AABB) of a whole scene,
    or None if the scene is empty.
    """
    bb_min = [1e10, 1e10, 1e10] # x,y,z
    bb_max = [-1e10, -1e10, -1e10] # x,y,z

    if not scene.rootnode.children:
        logger.warning("rootnode has no children! The scene is probably empty.")
        return None, None

    return get_bounding_box_for_node(scene.nodes, scene.rootnode, bb_min, bb_max, linalg.inv(scene.rootnode.transformation))

def get_bounding_box_for_node(nodes, node, bb_min, bb_max, transformation):
    
    transformation = numpy.dot(transformation, node.transformation)
    if node.type == MESH:
        for v in node.aabb:
            v = transform(v, transformation)
            bb_min[0] = min(bb_min[0], v[0])
            bb_min[1] = min(bb_min[1], v[1])
            bb_min[2] = min(bb_min[2], v[2])
            bb_max[0] = max(bb_max[0], v[0])
            bb_max[1] = max(bb_max[1], v[1])
            bb_max[2] = max(bb_max[2], v[2])

    for child in node.children:
        bb_min, bb_max = get_bounding_box_for_node(nodes, nodes[child], bb_min, bb_max, transformation)

    return bb_min, bb_max

def _get_parent_chain(scene, node, parents):
    parents.append(node.parent)

    if node.parent == scene.rootnode:
        return parents

    return _get_parent_chain(scene, node.parent, parents)

def transformed_aabb(scene, node):
    """ TODO: this computation is incorrect! To compute a transformed AABB, we need to
    re-compute the AABB from the transformed *vertices* (or maybe from the transformed bounding box?)
    """
    parents = reversed(_get_parent_chain(scene, node, []))

    global_transformation = reduce(numpy.dot, [p.transformation for p in parents])
    
    return transform(node.aabb[0], global_transformation), \
           transform(node.aabb[1], global_transformation)
